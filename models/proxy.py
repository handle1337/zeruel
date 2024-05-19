import queue
import re
import socket
import ssl
import sys
import itertools
from urllib.parse import urlparse
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
        self.buffer_size = 8192
        self.intercepting = False

        self.client_socket = None
        self.client_data = None

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
                # We don't need to intercept requests with CONNECT method
                # (TODO: should instead parse the req for methods instead of checking if string is in request)
                if self.intercepting:
                    # No need to capture CONNECT reqs
                    if request["method"] != "CONNECT":
                        print("\nsending to queue\n")
                        queue_manager.client_request_queue.put(self.client_data)  # we display this in the GUI
                        queue_manager.server_request_queue.put(self.parse_data(self.client_data))
                    else:
                        send_data_thread.start()
                else:
                    # send_data_thread.start()  # send connection request
                    pass

                    # self.server_request_queue.put(
                    #     self.parse_data(self.client_data))  # we queue parsed data to be used when forwarding request

        if not send_data_thread.is_alive():
            pass
            # send_data_thread.join()

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
        data_lines = data.decode('utf-8').split('\n')
        method = data_lines[0].split(' ')[0]

        host = None
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
        print(result)
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

    def send_data(self, hostname: str, port: int, data: bytes, method: str = None):
        if not self.running:
            return
        print("\nsend data\n")
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
                remote_context = ssl.create_default_context()
                # client_context = ssl.create_default_context()
                remote_socket = remote_context.wrap_socket(remote_socket, server_hostname=hostname)
                # wrapped_client_socket = client_context.wrap_socket(self.server_socket, server_hostname=hostname)
                # wrapped_remote_socket.sendall(data)
                print(f"wrapped {remote_socket}")
                if method == "CONNECT":
                    self.client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                remote_socket.sendall(data)
                # wrapped_remote_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                while True:
                    print("sending data")
                    chunk = remote_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    self.client_socket.sendall(chunk)  # send back to browser

        # except socket.error as e:
        #     remote_socket.close()
        #     print(f"err: {e}")
        # remote_socket.close()
        finally:
            pass
