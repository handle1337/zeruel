import threading
from controllers import server_manager


class InterceptModel:
    def __init__(self):
        self.server_thread = server_manager.server_threads[0]
        self.client_request_queue = self.server_thread.client_request_queue

        self.intercepting = False

    def forward_request(self, request):
        if self.server_thread and self.server_thread.running:
            if request:
                outgoing_request = self.server_thread.parse_data(request)

                print(request)
                print(outgoing_request)

                webserver = outgoing_request["server"]
                port = outgoing_request["port"]
                data = outgoing_request["data"]
                threading.Thread(target=self.server_thread.send_data, args=(webserver, port, data)).start()
            else:
                print("no request intercepted")

    def start_intercepting(self):
        server_manager.stop(self.server_thread)
        self.server_thread = server_manager.new_server()
        server_manager.start(self.server_thread, intercept=True)

    def stop_intercepting(self):
        server_manager.stop(self.server_thread)
        self.server_thread = server_manager.new_server()
        server_manager.start(self.server_thread, intercept=False)

    def get_client_request_from_queue(self):
        if not self.client_request_queue.empty():
            return self.client_request_queue.get_nowait().decode("utf-8")
