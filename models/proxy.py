import socket
import ssl
import os
import sys
import itertools
import threading

from util import parser, certs
from util.logging_conf import logger
from controllers import queue_manager
from threading import Thread


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

        self.certs_path = self.join_with_script_dir("certs/")
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
        #  print(f"{self.proxy_socket}")
        except KeyboardInterrupt:
            self.stop()
            sys.exit(1)
        except socket.error as e:
            print(e)
            self.stop()
        self.handle_client()

    def handle_client(self):

        while self.running:
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
                parsed_data = parser.parse_data(self.client_data)

                if parsed_data:
                    if self.intercepting:
                        self.intercept(hostname=parsed_data["host"],
                                       port=parsed_data["port"],
                                       method=parsed_data["method"])
                    else:
                        self.send_data(parsed_data["host"], parsed_data["data"], parsed_data["method"],
                                       parsed_data["port"])

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

    def relay_data(self, remote_socket, client_socket, client_data, port):
        # TODO: port only for debug rn, delete later

        _data = ''
        _chunk = ''
        while True:
            try:
                _data = _data + client_data.decode('utf-8', errors='ignore')

                # print(f"Client:\n{'=' * 200}\n{_data}\n{'=' * 200}")

                remote_socket.sendall(client_data)

                chunk = remote_socket.recv(self.buffer_size)
                if not chunk:
                    break

                # For debug
                # TODO: calc buff len at beginning of handshake
                _chunk = _chunk + chunk.decode('utf-8', errors='ignore')

                # print(f"Remote:\n{'=' * 200}\n{_chunk}\n{'=' * 200}")

                client_socket.send(chunk)  # send back to browser
            except socket.error as error:
                logger.error(f"ERROR: Unable to relay data {error}")

    def intercept(self, method, hostname, port):
        logger.debug("Intercepting")

        if port == 80 and method != "CONNECT":
            logger.debug("sending to queue")
            queue_manager.client_request_queue.put(self.client_data)
            return
        if port == 443:
            # DO NOT DELETE, MUST ESTABLISH/CONFIRM CONN W PROXY
            self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            logger.debug("genning cert")

            cert_path, key_path = certs.generate_certificate(self.certs_path,
                                                             hostname,
                                                             self.cacert,
                                                             self.cakey)
            logger.debug(f"GOT certs: {cert_path, key_path}")
            client_ssl_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)
            logger.debug(f"GOT socket ssl client: {client_ssl_socket}")
            ssl_client_data = client_ssl_socket.recv(4096)
            logger.debug(f"GOT: {ssl_client_data}")

            queue_manager.client_request_queue.put(ssl_client_data)

            remote_socket = socket.create_connection((hostname, port))
            remote_ssl_socket = self.wrap_remote_socket(remote_socket, hostname)
            # hacky way of holding the conn so browser doesnt gives us errors
            remote_ssl_socket.recv(self.buffer_size)
            return
        else:
            pass

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

    def probe_tls_support(self, hostname, port=443):
        """

        :param hostname: Remote target hostname
        :param port: Remote target port, default is 443
        :return: 1 If HTTPS is supported, 0 if it isn't
        """

        remote_socket = socket.create_connection((hostname, port))
        try:
            remote_ssl_socket = self.wrap_remote_socket(remote_socket, hostname)
            print(f"Version {remote_ssl_socket.version()}")
            return 1
        except socket.error:
            return 0

    def send_data(self, hostname: str, data: bytes, method: str = None, port: int = 80):
        if not self.running:
            return

        try:

            if self.probe_tls_support(hostname):
                port = 443
            else:
                port = 80

            remote_socket = socket.create_connection((hostname, port))

            if port == 80:

                threading.Thread(target=self.relay_data, args=(remote_socket,
                                                               self.client_socket,
                                                               data,
                                                               port)).start()
            else:

                cert_path, key_path = certs.generate_certificate(self.certs_path,
                                                                 hostname,
                                                                 self.cacert,
                                                                 self.cakey)

                #  print(f"cert:{cert_path}\nkey{key_path}")

                # DO NOT DELETE, MUST ESTABLISH/CONFIRM CONN W PROXY
                self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

                client_ssl_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)
                remote_ssl_socket = self.wrap_remote_socket(remote_socket, hostname)

                ssl_client_data = client_ssl_socket.recv(4096)

                threading.Thread(target=self.relay_data, args=(remote_ssl_socket,
                                                               client_ssl_socket,
                                                               ssl_client_data,
                                                               port)).start()

                # remote_socket.close()
        except socket.error as err:
            logger.debug(f"{err} | Server ID: {self.id} |\n>Server Thread {self} |\n>Data: {data}")

        finally:
            pass
