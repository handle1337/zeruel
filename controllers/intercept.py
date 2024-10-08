from controllers import queue_manager
from views.intercept_view import InterceptTab
from models.intercept import InterceptModel


class InterceptController:
    def __init__(self, root, server):
        self.server = server
        self.client_request_queue = queue_manager.client_request_queue
        self.info_queue = queue_manager.info_queue
        self.intercept_tab = InterceptTab(root, controller=self)
        self.intercept_model = InterceptModel(controller=self)

        self.intercepting = self.intercept_model.intercepting
        self.intercepted_request = None

    def forward_request(self, request: str):
        request = request.encode()  # to bytes
        self.intercept_model.forward_request(request)

    def toggle_intercept(self, state: bool):
        self.intercept_model.intercepting = state
        self.intercepting = state

    def update(self):
        if self.intercepted_request:
            self.intercept_tab.clear()
            self.intercept_tab.update_intercepted_request_widget(self.intercepted_request)
            self.intercepted_request = None
        else:
            self.intercepted_request = self.intercept_model.get_client_request_from_queue()
            self.intercept_tab.update_intercepted_request_widget(self.intercepted_request)
            self.intercept_tab.root.after(100, self.update)

    def start_intercepting(self):
        self.intercept_model.start_intercepting()

    def stop_intercepting(self):
        self.intercept_model.stop_intercepting()
