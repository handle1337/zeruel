import queue
import re
import socket
import ssl
import os
import sys
import itertools
from util.logging_conf import logger
from urllib.parse import urlparse
from controllers import queue_manager
from threading import Thread
from OpenSSL import crypto


class Server(Thread):
    new_id = itertools.count()

    def __init__(self, host, port):
        super().__init__()
        self.id = next(Server.new_id)
        print(self.id)
        self.running = False
        self.proxy_socket = None
        self.host = host
        self.port = port

        # TODO: we need a way to handle buffers better
        self.buffer_size = 8192
        self.intercepting = False

        self.client_socket = None
        self.client_data = None

        # TODO: add support for linux
        self.certs_path = self.join_with_script_dir("certs\\")
        self.cakey = self.certs_path + "zeruelCA.key"
        self.cacert = self.certs_path + "zeruelCA.crt"
        # self.certkey = self.certs_path + "generated\\github.com\\github.com.key"

    def run(self):
        self.running = True
        try:

            logger.info(f"Started server thread: {self} with intercept: {self.intercepting} | Server ID: {self.id}")

            self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                                         1)  # This is a necessary step since we need to reuse the port immediately
            self.proxy_socket.bind((self.host, self.port))
            self.proxy_socket.listen(10)
            print(f"{self.proxy_socket}")
        except KeyboardInterrupt:
            self.stop()
            sys.exit(1)
        except socket.error as e:
            print(e)
            self.stop()
        self.handle_client()

    def handle_client(self):

        while self.running:
            print(f"Intercepting: {self.intercepting}")
            print("Awaiting connection from client")
            # accept incoming connections from client/browser
            try:
                self.client_socket, client_address = self.proxy_socket.accept()
                print(f"{self.client_socket} {client_address[0]} {client_address[1]}")
            except socket.timeout:
                print("Connection timeout, retrying...")
                continue
            except Exception as e:
                print(e)
                self.stop()
                return
            # get request from browser
            # TODO while loop here to only recv buffer matching data len
            self.client_data = self.client_socket.recv(self.buffer_size)
            request = self.parse_data(self.client_data)

            if request:
                send_data_thread = Thread(target=self.send_data, args=(request["host"],
                                                                       request["port"],
                                                                       request["data"],
                                                                       request["method"]))

                print(request)

                if self.intercepting:
                    # No need to capture CONNECT reqs
                    if request["method"] != "CONNECT":
                        print("\nsending to queue\n")
                        queue_manager.client_request_queue.put(self.client_data)  # we display this in the GUI
                        # queue_manager.server_request_queue.put(self.parse_data(self.client_data))
                    else:
                        send_data_thread.start()
                else:
                    # TODO if https load cert chain for proxy
                    send_data_thread.start()  # send connection request

                    # self.server_request_queue.put(
                    #     self.parse_data(self.client_data))  # we queue parsed data to be used when forwarding request
        # if not send_data_thread.is_alive():
        #     #send_data_thread.join()

    def stop(self):
        self.running = False
        if self.proxy_socket:
            self.proxy_socket.close()
            print("killed server socket")
        if self.client_socket:
            self.client_socket.close()
            print("killed client socket")

    @staticmethod
    def parse_data(data):
        if not data:
            return

        print(data)

        data_lines = data.decode('utf-8', errors='ignore').split('\n')
        method = data_lines[0].split(' ')[0]
        url = data_lines[0].split(' ')[1]

        if "http" in url:
            port = 80
            if "https" in url:
                port = 443
            parsed_url = urlparse(url)
            host = parsed_url.netloc
        else:
            host, port = data_lines[0].split(' ')[1].split(':')

        host = re.sub(r'https?://', '', host).replace('/', '')

        # user_agent = data_lines[1].split(': ')[1]
        port = int(port)
        result = {"method": method, "host": host, "port": port, "data": data}
        # print(result)
        return result

    def forward_data(self):
        if not self.client_data:
            print("no data")
            return
        request = self.parse_data(self.client_data)
        send_data_thread = Thread(target=self.send_data, args=(request["server"],
                                                               request["port"],
                                                               request["data"]))
        self.client_data = None
        send_data_thread.start()

    def connect(self):
        pass

    # TODO: move this to future file manager module
    @staticmethod
    def join_with_script_dir(path):
        return os.path.join(os.path.dirname(os.path.abspath(__name__)), path)

    @staticmethod
    def generate_keypair(path=None):
        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)
        if path:
            with open(path, 'w+') as key_file:
                key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))
        return key

    def generate_csr(self, hostname, key, path=None):
        """
        :param hostname: Subject root hostname to use when adding SANs
        :param key: Subject's private key
        :param path: Optional path for csr request output
        :return:
        """

        # gen privkey file for hostname csr
        san_list = [f"DNS.1:*.{hostname}",
                    f"DNS.2:{hostname}"]

        csr = crypto.X509Req()
        csr.get_subject().CN = hostname
        # SANs are required by modern browsers, so we add them
        csr.add_extensions([
            crypto.X509Extension(b"subjectAltName", False, ', '.join(san_list).encode())
        ])
        csr.set_pubkey(key)
        csr.sign(key, "sha256")

        if path:
            with open(path, 'w+') as csr_file:
                csr_file.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, csr).decode("utf-8"))
        return csr

    def generate_certificate(self, hostname: str):
        # ref https://gist.github.com/soarez/9688998
        # ref: https://stackoverflow.com/questions/10175812/how-to-generate-a-self-signed-ssl-certificate-using-openssl

        host_cert_path = f"{self.certs_path}generated\\{hostname}"
        key_file_path = f"{host_cert_path}\\{hostname}.key"
        csr_file_path = f"{host_cert_path}\\{hostname}.csr"
        cert_file_path = f"{host_cert_path}\\{hostname}.pem"

        if not os.path.isdir(host_cert_path):
            os.mkdir(host_cert_path)

        root_ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(self.cacert, 'rb').read())
        root_ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(self.cakey, 'rb').read())

        print(f"{root_ca_cert} {root_ca_key}")

        key = self.generate_keypair(key_file_path)
        csr = self.generate_csr(hostname, key, csr_file_path)

        san_list = [f"DNS.1:*.{hostname}",
                    f"DNS.2:{hostname}"]

        cert = crypto.X509()
        cert.get_subject().CN = hostname
        cert.set_serial_number(int.from_bytes(os.urandom(16), "big") >> 1)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(31536000)  # 1 year

        cert.add_extensions([
            crypto.X509Extension(b"subjectAltName", False, ', '.join(san_list).encode())
        ])

        cert.set_issuer(root_ca_cert.get_subject())
        cert.set_pubkey(csr.get_pubkey())

        cert.sign(root_ca_key, 'sha256')

        with open(cert_file_path, 'w+') as cert_file:
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

        return cert_file_path, key_file_path

    def send_data(self, hostname: str, port: int, data: bytes, method: str = None):
        if not self.running:
            return

        try:

            remote_socket = socket.create_connection((hostname, port))

            if port == 80:

                print("\nwebserver " + str(hostname))
                print("\nport " + str(port))
                print("\nremote " + str(remote_socket))
                print("\nclient " + str(self.client_socket))

                remote_socket.sendall(data)
                while True:
                    # TODO: https://stackoverflow.com/a/1716173
                    chunk = remote_socket.recv(self.buffer_size)
                    if not chunk:
                        break

                    print(f"to browser {chunk}")
                    self.client_socket.send(chunk)  # send back to browser
            else:

                cert_path, key_path = self.generate_certificate(hostname)

                # TODO https: // gist.github.com / oborichkin / d8d0c7823fd6db3abeb25f69352a5299

                print(f"cert:{cert_path}\nkey{key_path}")

                remote_ctx = ssl.create_default_context()

                client_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)
                client_ctx.minimum_version = ssl.TLSVersion.TLSv1_3

                self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")  # Necessary DO NOT DELETE

                client_ssl_socket = ssl.wrap_socket(sock=self.client_socket,
                                                    certfile=cert_path,
                                                    keyfile=key_path,
                                                    server_side=True)

                print(f"ssl client socket {client_ssl_socket}")

                remote_ssl_socket = remote_ctx.wrap_socket(remote_socket, server_hostname=hostname)

                if method == "CONNECT":
                    pass
                # remote_ssl_socket.sendall(data)
                chunk = None
                # Relay data
                # TODO: clean this up

                _chunk = ''
                _data = ""

               # print(f"dat\n{data}\n")
                client_data = client_ssl_socket.recv(4096)

                while True:
                    _data = _data + client_data.decode('utf-8', errors='ignore')

                    print(f"Client:\n{'=' * 200}\n{_data}\n{'=' * 200}")

                    remote_ssl_socket.send(client_data)

                    chunk = remote_ssl_socket.recv(self.buffer_size)
                    if not chunk:
                        pass

                    # For debug
                    # TODO: calc buff len at beginning of handshake

                    _chunk = _chunk + chunk.decode('utf-8', errors='ignore')

                    print(f"Remote:\n{'=' * 200}\n{_chunk}\n{'=' * 200}")

                    client_ssl_socket.send(chunk)  # send back to browser

                # remote_socket.close()
        except socket.error as err:
            logger.debug(f"{err} | Server ID: {self.id} |\n>Server Thread {self} |\n>Data: {data}")

        finally:
            pass
