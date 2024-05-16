import queue
import socket
import ssl
import sys
from threading import Thread


class Server(Thread):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host, port):
        Thread.__init__(self)
        self.running = False
        self.server_socket = None
        self.host = host
        self.port = port
        self.buffer_size = 8192
        self.intercepting = False

        self.client_request_queue = queue.Queue()
        self.client_server_queue = queue.Queue()

        self.client_data = None

    @staticmethod
    def get_instance():
        return Server._instance

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                                          1)  # This is a necessary step since we need to reuse the port immediately
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            print(f"{self.server_socket}")
        except KeyboardInterrupt:
            self.stop()
            sys.exit(1)
        except socket.error as e:
            print(e)
        self.handle_client()

    def handle_client(self):
        while self.running:

            # accept incoming connections from client/browser
            try:
                self.client_socket, client_address = self.server_socket.accept()
                print(f"{self.client_socket} {client_address[0]} {client_address[1]}")
            except Exception as e:
                print(e)
                return

            # get request from client/browser
            self.client_data = self.client_socket.recv(self.buffer_size)
            request = self.parse_data(self.client_data)

            if request:
                send_data_thread = Thread(target=self.send_data, args=(request["server"],
                                                                       request["port"],
                                                                       request["data"]))
                # We don't need to intercept requests with CONNECT method
                # (TODO: should instead parse the req for methods instead of checking if string is in request)
                if self.intercepting:
                    if not ("CONNECT" in str(self.client_data)):
                        print("\nsending to queue\n")
                        self.client_request_queue.put(self.client_data)  # we display this in the GUI
                else:
                    send_data_thread.start()  # send connection request

                    # self.server_request_queue.put(
                    #     self.parse_data(self.client_data))  # we queue parsed data to be used when forwarding request

        if not send_data_thread.is_alive():
            pass
            # send_data_thread.join()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            print("killed proxy")
            print(f"client {self.client_socket}")

    @staticmethod
    def parse_data(data):
        if not data:
            return
        print(data)
        first_line = data.split(b'\n')[0]

        url = first_line.split()[1]

        http_pos = url.find(b'://')  # Finding the position of ://
        if http_pos == -1:
            temp = url
        else:

            temp = url[(http_pos + 3):]

        port_pos = temp.find(b':')

        webserver_pos = temp.find(b'/')
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]
        print(data)
        return {"server": webserver, "port": port, "data": data}

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

    def send_data(self, hostname: str, port: int, data: bytes | bytearray):
        hostname = hostname.decode('utf-8')
        print("\nsend data\n")
        remote_socket = None
        try:

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((hostname, port))
            # print("\ndata " + data.decode('utf-8'))
            print("\nwebserver " + hostname)
            print("\nport " + str(port))

            context = ssl.create_default_context()
            if port == 80:
                remote_socket.sendall(data)
                while True:
                    chunk = remote_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    # print("reply " + chunk.decode('utf-8'))
                    self.client_socket.sendall(chunk)  # send back to browser

            # with context.wrap_socket(remote_socket, server_hostname=hostname) as wrapped_socket:
            #     wrapped_socket.sendall(data)
            #     while True:
            #         chunk = wrapped_socket.recv(self.buffer_size)
            #         if not chunk:
            #             break
            #         #print("reply " + chunk.decode('utf-8'))
            #         self.client_socket.sendall(chunk) # send back to browser

        except Exception as e:
            remote_socket.close()
            print(f"err: {e}")
        remote_socket.close()
