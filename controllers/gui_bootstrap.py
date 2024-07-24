from views.repeater_view import RepeaterTab
from views.rootwindow_view import RootWindow

from models.intercept import InterceptModel

from controllers.intercept import InterceptController
from views.intercept_view import InterceptTab

from tkinter import ttk
import tkinter as tk


class RootWindowController:
    def __init__(self, root, server):
        self.root_window = RootWindow(root)

        intercept_tab = self.root_window.intercept_tab

        self.intercept_controller = InterceptController(root=intercept_tab, server=server)

        #self.intercept_tab = InterceptTab(self.RootWindow.repeater_tab, None)

    def __del__(self):
        print("RootWindow Destroyed")
