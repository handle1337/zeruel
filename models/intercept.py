import threading
import queue
from util import parser
from controllers import server_manager


class InterceptModel:
    def __init__(self, controller):
        self.server_thread = controller.server
        self.protocols = controller.server.protocols
        self.client_request_queue = controller.client_request_queue
        self.info_queue = controller.info_queue

        self.intercepting = False  # TODO: take this as an arg

    def forward_request(self, request: bytes):
        if self.server_thread and self.server_thread.running:
            if request:

                try:

                    remote_socket = self.get_remote_socket_from_queue()
                    parsed_request = parser.parse_data(request)

                    print(f"Request: {request}")
                    print(f"Parsed Request: {parsed_request}")

                    webserver = parsed_request["host"]
                    port = parsed_request["port"]
                    protocol = parsed_request["protocol"]
                    data = parsed_request["data"]
                    method = parsed_request["method"]

                    if port:
                        threading.Thread(target=self.server_thread.send_data,
                                         args=(webserver, remote_socket, data, method, port)).start()
                    elif protocol == self.protocols.HTTP:
                        threading.Thread(target=self.server_thread.send_data,
                                         args=(webserver, remote_socket, data, method, 80)).start()
                    elif protocol == self.protocols.HTTPS or protocol is None:
                        threading.Thread(target=self.server_thread.send_data,
                                         args=(webserver, remote_socket, data, method, port)).start()

                except queue.Empty:
                    print("No remote socket")
            else:
                print("no request intercepted")

    def start_intercepting(self):
        server_manager.stop_all()
        self.server_thread = server_manager.new_server()
        server_manager.start(self.server_thread, intercept=True)

    def stop_intercepting(self):
        server_manager.stop(self.server_thread)
        self.server_thread = server_manager.new_server()
        server_manager.start(self.server_thread, intercept=False)

    def get_client_request_from_queue(self):
        try:
            request = self.client_request_queue.get_nowait().decode('utf-8', errors='ignore')
            return request
        except queue.Empty:
            return None

    def get_remote_socket_from_queue(self):
        try:
            remote_socket = self.info_queue.get_nowait()
            print(f"data in info queue {remote_socket}")
            return remote_socket
        except queue.Empty:
            return None
