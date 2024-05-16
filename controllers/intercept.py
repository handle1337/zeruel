import tkinter as tk
from views.intercept_view import InterceptTab
from models.intercept import InterceptModel


class InterceptController:
    def __init__(self, root):
        self.intercept_tab = InterceptTab(root, self)
        self.intercept_model = InterceptModel()

        self.intercepting = self.intercept_model.intercepting

    def forward_request(self, request: str):
        request = request.encode()
        self.intercept_model.forward_request(request)

    def toggle_intercept(self, state: bool):
        self.intercept_model.intercepting = state
        self.intercepting = state

    def update_step(self):
        request = self.intercept_model.get_client_request_from_queue()
        if request:
            self.intercept_tab.clear()
            self.intercept_tab.update_intercepted_request_widget(request)

    def update_loop(self):
        if self.intercepting:
            self.update_step()
            self.intercept_tab.root.after(100, self.update_loop)

    def start_intercepting(self):
        self.intercept_model.start_intercepting()

    def stop_intercepting(self):
        self.intercept_model.stop_intercepting()
