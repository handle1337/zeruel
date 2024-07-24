import queue
import socket
import ssl
import os
import sys
import itertools
import threading
import enum

from util import parser, certs
from util.logging_conf import logger
from controllers import queue_manager
from threading import Thread


class Protocols(enum.Enum):
    HTTP = enum.auto()
    HTTPS = enum.auto()


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

        self.protocols = Protocols

        # TODO: we need a way to handle buffers better
        self.buffer_size = 8192
        self.intercepting = False

        self.client_socket = None
        self.client_data = None

        self.certs_path = self.join_with_script_dir("certs/")
        self.cakey = self.certs_path + "/zeruelCA.key"
        self.cacert = self.certs_path + "/zeruelCA.crt"

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

            try:
                self.client_data = self.client_socket.recv(self.buffer_size)
                parsed_data = parser.parse_data(self.client_data)

                if parsed_data:
                    host = parsed_data["host"]
                    port = 80
                    data = parsed_data["data"]
                    parsed_protocol = parsed_data["protocol"]

                    if parsed_data["port"] and parsed_data["port"] != 80:
                        port = parsed_data["port"]
                        remote_socket = socket.create_connection((host, port))
                    elif parsed_protocol:
                        remote_socket = socket.create_connection((host, port))
                    else:
                        # check if port 443 is https, upgrade if so
                        protocol = self.probe_tls_support(parsed_data["host"], port=443)
                        if protocol == self.protocols.HTTPS:
                            port = 443
                        remote_socket = socket.create_connection((host, port))

                    if self.intercepting:
                        self.intercept(hostname=host,
                                       remote_socket=remote_socket,
                                       method=parsed_data["method"],
                                       port=port,
                                       data=data)
                    else:
                        self.send_data(hostname=host,
                                       data=parsed_data["data"],
                                       remote_socket=remote_socket,
                                       port=port)

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

    def connect(self):
        pass

    # TODO: move this to future file manager module
    @staticmethod
    def join_with_script_dir(path):
        return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__name__)), path))

    def relay_data(self, remote_socket, client_socket, client_data):
        # _data = ''
        # _chunk = ''
        while True:
            try:
                # _data = _data + client_data.decode('utf-8', errors='ignore')
                # print(f"Client:\n{'=' * 200}\n{_data}\n{'=' * 200}")

                remote_socket.sendall(client_data)

                chunk = remote_socket.recv(self.buffer_size)
                if not chunk:
                    break

                # TODO: calc buff len at beginning of handshake
                # _chunk = _chunk + chunk.decode('utf-8', errors='ignore')

                # print(f"Remote:\n{'=' * 200}\n{_chunk}\n{'=' * 200}")

                # If intercepting we force browser to wait
                if self.intercepting:
                    client_socket.send(chunk)

                    # client_socket.send(b"HTTP/1.1 100 Continue\r\n\r\n")
                else:
                    client_socket.send(chunk)  # send back to browser
            except socket.error as error:
                logger.error(f"ERROR: Unable to relay data {error}")

    def intercept(self, method, hostname, remote_socket, port, data):

        protocol = self.probe_tls_support(hostname, port)

        if protocol == self.protocols.HTTP and method != "CONNECT":
            logger.debug("sending to queue")
            queue_manager.client_request_queue.put(self.client_data)
            queue_manager.info_queue.put(remote_socket)
            return

        if protocol == self.protocols.HTTPS:

            # DO NOT DELETE, MUST ESTABLISH/CONFIRM CONN W PROXY
            self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

            ssl_remote_socket = self.wrap_remote_socket(remote_socket, hostname)
            #if method != "CONNECT":
            logger.debug("genning cert")
            cert_path, key_path = certs.generate_certificate(self.certs_path,
                                                             hostname,
                                                             self.cacert,
                                                             self.cakey)

            logger.debug(f"GOT certs: {cert_path, key_path}")
            ssl_client_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)

            logger.debug(f"GOT socket ssl client: {ssl_client_socket}")
            ssl_client_data = ssl_client_socket.recv(4096)

            #logger.debug(f"GOT: {ssl_client_data}")
            print(f"GOT: {ssl_client_data}")
            queue_manager.client_request_queue.put(ssl_client_data)

            queue_manager.info_queue.put(ssl_remote_socket)
            queue_manager.client_socket_queue.put(ssl_client_socket)

            #hold conn
            #ssl_remote_socket.recv(4096)

                    # else:
                    #     threading.Thread(target=self.send_data,
                    #                      args=(hostname, ssl_remote_socket, data, port)).start()

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

    def probe_tls_support(self, hostname, port=443) -> enum.Enum:
        """

        :param hostname: Remote target hostname
        :param port: Remote target port, default is 443
        :return: Protocol enum
        """

        remote_socket = socket.create_connection((hostname, port))
        try:
            remote_ssl_socket = self.wrap_remote_socket(remote_socket, hostname)
            print(f"Version {remote_ssl_socket.version()} host: {hostname}")
            return self.protocols.HTTPS
        except socket.error:
            return self.protocols.HTTP

    def send_data(self, hostname: str, remote_socket, data: bytes, method=None, port: int = None):
        if not self.running:
            return

        try:

            protocol = self.protocols.HTTP

            if port != 80:
                protocol = self.probe_tls_support(hostname)

            # print(f"Sending to {hostname}:{port}")
            # print(f"Data {data}")
            # print(f"Protocol {protocol}")
            # print(f"r_sock {remote_socket}")
            # print(f"c_sock {self.client_socket}")

            if protocol == self.protocols.HTTP:

                threading.Thread(target=self.relay_data, args=(remote_socket,
                                                               self.client_socket,
                                                               data)).start()
            elif protocol == self.protocols.HTTPS:

                # When intercepting the remote socket gets wrapped, we don't need to wrap it again
                if not self.intercepting:
                    # DO NOT DELETE, MUST ESTABLISH/CONFIRM CONN W PROXY
                    self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    cert_path, key_path = certs.generate_certificate(self.certs_path,
                                                                     hostname,
                                                                     self.cacert,
                                                                     self.cakey)
                    print(f"certs {cert_path} {key_path}")
                    client_ssl_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)
                    remote_ssl_socket = self.wrap_remote_socket(remote_socket, hostname)
                    threading.Thread(target=self.relay_data, args=(remote_ssl_socket,
                                                                   client_ssl_socket,
                                                                   client_ssl_socket)).start()
                else:
                    """ 
                    when intercepting a check is made in Server.intercept() indicating whether or not
                    the request is using the CONNECT method, if it isn't an ssl wrapped client socket is passed
                    to the queue. if nothing is passed we must wrap the client socket here
                    """
                    try:
                        # method != connect
                        client_ssl_socket = queue_manager.client_socket_queue.get_nowait()
                    except queue.Empty as e:

                        cert_path, key_path = certs.generate_certificate(self.certs_path,
                                                                         hostname,
                                                                         self.cacert,
                                                                         self.cakey)
                        client_ssl_socket = self.wrap_client_socket(self.client_socket, cert_path, key_path)

                        print(f"{e}: wrapping socket {client_ssl_socket} with {cert_path} {key_path}")

                    remote_ssl_socket = remote_socket # we infer that remote socket is wrapped in Server.intercept()

                #ssl_client_data = client_ssl_socket.recv(4096)

                threading.Thread(target=self.relay_data, args=(remote_ssl_socket,
                                                               client_ssl_socket,
                                                               data)).start()


        except socket.error as err:
            logger.debug(f"{err} | Server ID: {self.id} |\n>Server Thread {self} |\n>Data: {data}")

        finally:
            pass
