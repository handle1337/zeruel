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

            try:
                self.client_data = self.client_socket.recv(self.buffer_size)
                parsed_data = self.parse_data(self.client_data)

                if parsed_data:
                    # send_data_thread = Thread(target=self.send_data, args=(parsed_data["host"],
                    #                                                        parsed_data["port"],
                    #                                                        parsed_data["data"],
                    #                                                        parsed_data["method"]))
                    #
                    # send_data_thread.start()  # send connection request

                    if self.intercepting:
                        self.intercept(hostname=parsed_data["host"],
                                       port=parsed_data["port"],
                                       method=parsed_data["method"])
                    else:
                        self.send_data(parsed_data["host"],
                                       parsed_data["port"],
                                       parsed_data["data"],
                                       parsed_data["method"])

            except socket.error as e:
                logger.exception(f"Exception {e} | Server ID: {self.id} |\nData: {self.client_data}")

        self.stop()

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

        # TODO: parse origin/host as well
        # host : where the req is going
        # origin : where req is from

        print(f"Parsing: {data}")

        data_lines = data.decode('utf-8', errors='ignore').split('\n')

        print(f"Data lines: {data_lines}")

        method = data_lines[0].split(' ')[0]
        url = data_lines[0].split(' ')[1]
        port = 80

        print(url)

        host = ''

        if '://' in url:
            parsed_url = urlparse(url)
            host = parsed_url.netloc

            # TODO: There's some edge cases here we're not accounting for

            if ':' in host:
                split_host = host.split(':')
                host = split_host[0]
                port = int(split_host[1])

            if parsed_url.scheme == "http":
                port = 80
            elif parsed_url.scheme == "https":
                port = 443

        elif ':' in url:
            split_host = url.split(':')
            host = split_host[0]
            port = int(split_host[1])

        result = {"method": method, "host": host, "port": port, "data": data}

        print(f"{result}")

        return result

    # TODO: what do we do with this?
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

    @staticmethod
    def generate_csr(hostname, key, path=None):
        """
        :param hostname: Subject root hostname to use when adding SANs
        :param key: Subject's private key
        :param path: Optional path for csr request output
        :return:
        """

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

        # Generate cert

        cert = crypto.X509()
        cert.get_subject().CN = hostname
        cert.set_serial_number(int.from_bytes(os.urandom(16), "big") >> 1)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(31536000)  # 1 year

        # Yes we must add the SANs to the cert as well
        san_list = [f"DNS.1:*.{hostname}",
                    f"DNS.2:{hostname}"]

        cert.add_extensions([
            crypto.X509Extension(b"subjectAltName", False, ', '.join(san_list).encode())
        ])

        # Sign it
        cert.set_issuer(root_ca_cert.get_subject())
        cert.set_pubkey(csr.get_pubkey())

        cert.sign(root_ca_key, 'sha256')

        with open(cert_file_path, 'w+') as cert_file:
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

        return cert_file_path, key_file_path

    def relay_data(self, remote_socket, client_socket, client_data, chunk, port):
        # TODO: port only for debug rn, delete later

        _data = ''
        _chunk = ''
        while True:
            _data = _data + client_data.decode('utf-8', errors='ignore')

            print(f"Client:\n{'=' * 200}\n{_data}\n{'=' * 200}")

            remote_socket.sendall(client_data)

            chunk = remote_socket.recv(self.buffer_size)
            if not chunk:
                if port == 80:
                    break
                else:
                    pass  # TODO: should be break but we need to handle CORS parsing first

            # For debug
            # TODO: calc buff len at beginning of handshake
            _chunk = _chunk + chunk.decode('utf-8', errors='ignore')

            print(f"Remote:\n{'=' * 200}\n{_chunk}\n{'=' * 200}")

            client_socket.send(chunk)  # send back to browser

    def intercept(self, method, hostname, port):
        if self.intercepting:
            # No need to capture CONNECT reqs
            if method != "CONNECT":
                if port == 80:
                    print("\nsending to queue\n")
                    queue_manager.client_request_queue.put(self.client_data)
                else:
                    cert_path, key_path = self.generate_certificate(hostname)
                    client_ssl_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)
                    ssl_client_data = client_ssl_socket.recv(4096)
                    queue_manager.client_request_queue.put(ssl_client_data)

    @staticmethod
    def wrap_client_socket(client_socket, cert_path, key_path):
        client_ssl_socket = ssl.wrap_socket(sock=client_socket,
                                            certfile=cert_path,
                                            keyfile=key_path,
                                            server_side=True)
        return client_ssl_socket

    @staticmethod
    def wrap_remote_socket(remote_socket, hostname):
        remote_ctx = ssl.create_default_context()
        remote_ssl_socket = remote_ctx.wrap_socket(remote_socket, server_hostname=hostname)
        return remote_ssl_socket

    def send_data(self, hostname: str, port: int, data: bytes, method: str = None):
        if not self.running:
            return

        try:

            remote_socket = socket.create_connection((hostname, port))

            if port == 80:
                chunk = None
                remote_socket = socket.create_connection((hostname, port))

                relay_data_thread = Thread()
                self.relay_data(remote_socket, self.client_socket, data, chunk, port)
            else:

                cert_path, key_path = self.generate_certificate(hostname)

                print(f"cert:{cert_path}\nkey{key_path}")

                self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")  # Necessary DO NOT DELETE

                client_ssl_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)
                remote_ssl_socket = self.wrap_remote_socket(remote_socket, hostname)

                chunk = None

                ssl_client_data = client_ssl_socket.recv(4096)

                self.relay_data(remote_ssl_socket, client_ssl_socket, ssl_client_data, chunk, port)

                # remote_socket.close()
        except socket.error as err:
            logger.debug(f"{err} | Server ID: {self.id} |\n>Server Thread {self} |\n>Data: {data}")

        finally:
            pass
