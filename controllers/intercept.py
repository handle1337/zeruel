import tkinter
import threading
from controllers.gui_bootstrap import RootWindow
import tkinter as tk
from models.intercept import InterceptModel
from models.proxy import Server


class InterceptController:
    def __init__(self, intercept_tab, intercept_model):
        self.intercept_tab = intercept_tab
        self.intercept_model = intercept_model

        self.intercepting = self.intercept_model.intercepting

    def forward_request(self):
        request = self.intercept_tab.get_intercepted_request().encode()
        self.intercept_model.forward_request(request)

    def toggle_intercept(self, state: bool):
        self.intercept_model.intercepting = state

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
        pass

    def stop_intercepting(self):
        pass