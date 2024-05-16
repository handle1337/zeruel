import tkinter as tk
from tkinter import ttk


class RootWindow:
    def __init__(self, root):
        self.root = root

        self.root.title("Zeruel Proxy")
        window_width, window_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+0+0" % (window_width, window_height))
        self.tab_control = ttk.Notebook(self.root)

        self.setup_tabs()
        self.setup_tab_control()

        self.tab_control.pack(expand=True, fill="both")

    def setup_tabs(self):
        self.intercept_tab = tk.Frame(self.tab_control, bg="#8c8787")
        self.repeater_tab = tk.Frame(self.tab_control, bg="#8c8787")
        self.scanner_tab = tk.Frame(self.tab_control, bg="#8c8787")

    def setup_tab_control(self):
        self.tab_control.add(self.intercept_tab, text="Intercept")
        self.tab_control.add(self.repeater_tab, text="Repeater")
        self.tab_control.add(self.scanner_tab, text="Scanner")


    def __del__(self):
        print("RootWindow Destroyed")