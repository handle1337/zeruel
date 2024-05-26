import queue
import re
import socket
import ssl
import os
import sys
import itertools
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
        self.buffer_size = 8192
        self.intercepting = False

        self.client_socket = None
        self.client_data = None

        # TODO: add support for linux
        self.certs_path = self.join_with_script_dir("certs\\")
        self.cakey = self.certs_path + "zeruelCA.key"
        self.cacert = self.certs_path + "zeruelCA.crt"
        self.certkey = self.certs_path + "cert.key"

    def run(self):
        self.running = True
        try:
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
            # get request from client/browser
            self.client_data = self.client_socket.recv(self.buffer_size)
            request = self.parse_data(self.client_data)

            if request:
                send_data_thread = Thread(target=self.send_data, args=(request["host"],
                                                                       request["port"],
                                                                       request["data"],
                                                                       request["method"]))
                if self.intercepting:
                    # No need to capture CONNECT reqs
                    if request["method"] != "CONNECT":
                        print("\nsending to queue\n")
                        queue_manager.client_request_queue.put(self.client_data)  # we display this in the GUI
                        queue_manager.server_request_queue.put(self.parse_data(self.client_data))
                    else:
                        send_data_thread.start()
                else:
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
        data_lines = data.decode('utf-8').split('\n')
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

    # TODO: move this to future file manager
    @staticmethod
    def join_with_script_dir(path):
        return os.path.join(os.path.dirname(os.path.abspath(__name__)), path)

    def generate_certificate(self, hostname: str):
        host_cert_path = f"{self.certs_path}{hostname}"
        key_file_path = f"{host_cert_path}\\{hostname}.key"
        cert_file_path = f"{host_cert_path}\\{hostname}.pem"

        if not os.path.isdir(host_cert_path):
            os.mkdir(host_cert_path)

        root_ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM, open(self.cacert, 'rb').read())
        root_ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM, open(self.cakey, 'rb').read())

        key = crypto.PKey()
        key.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().CN = hostname
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(31536000)
        cert.set_issuer(root_ca_cert.get_subject())
        cert.set_subject(cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(root_ca_key, 'sha256')

        # key_dump = crypto.dump_privatekey(crypto.FILETYPE_PEM, key),
        # cert_dump = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)

        with open(cert_file_path, 'w+') as cert_file:
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))

        with open(key_file_path, 'w+') as key_file:
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key).decode("utf-8"))

        return cert_file_path, key_file_path

    # return key if needed to decrypt

    def send_data(self, hostname: str, port: int, data: bytes, method: str = None):
        if not self.running:
            return

        try:

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((hostname, port))

            if port == 80:

                # print("\ndata " + data.decode('utf-8'))
                print("\nwebserver " + str(hostname))
                print("\nport " + str(port))
                print("\nremote " + str(remote_socket))
                print("\nclient " + str(self.client_socket))

                remote_socket.sendall(data)
                while True:
                    chunk = remote_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    # print("reply " + chunk.decode('utf-8'))
                    self.client_socket.sendall(chunk)  # send back to browser
            else:

                cert_path, key_path = self.generate_certificate(hostname)
                print(cert_path)

                remote_context = ssl.create_default_context()

                client_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                client_context.load_cert_chain(keyfile=key_path, certfile=cert_path)

                self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

                client_ssl_socket = client_context.wrap_socket(self.client_socket, server_side=True)

                remote_ssl_socket = remote_context.wrap_socket(remote_socket, server_hostname=hostname)

                if method == "CONNECT":
                    pass
                # remote_ssl_socket.sendall(data)
                while True:
                    data = client_ssl_socket.recv(4096)
                    if len(data) == 0:
                        break
                    remote_ssl_socket.sendall(data)

                    #

                    chunk = remote_ssl_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    client_ssl_socket.sendall(chunk)  # send back to browser

        # except socket.error as e:
        #     print("Error\n\n\n")
        #     remote_socket.close()
        #     print(f"err: {e}")
        # remote_socket.close()
        finally:
            pass
