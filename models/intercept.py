import threading
from models.proxy import Server


def is_queue_empty(queue):
    if not queue.empty():
        return True
    return False


class InterceptModel:
    def __init__(self):
        self.server_thread = Server.get_instance()
        self.client_request_queue = self.server_thread.client_request_queue

        self.intercepting = False

        self.request_sent = False

    def forward_request(self, request):
        if self.server_thread and self.server_thread.running:
            # if not self.server_queue.empty():
            #     request = self.server_queue.get()
            #     print(f"From Server queue: {request}")

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
        self.server_thread.intercepting = True

    def stop_intercepting(self):
        self.server_thread.intercepting = False

    def get_client_request_from_queue(self):
        if not self.client_request_queue.empty():
            return self.client_request_queue.get_nowait().decode("utf-8")