from tkinter import ttk


class RootWindow:
    def __init__(self, root):
        self.root = root

        self.root.title("Zeruel Proxy")
        window_width, window_height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+0+0" % (window_width, window_height))
        self.tab_control = ttk.Notebook(self.root)

        self.intercept_tab_frame = ttk.Frame(self.tab_control)
        self.repeater_tab_frame = ttk.Frame(self.tab_control)
        self.scanner_tab_frame = ttk.Frame(self.tab_control)

        self.setup_tab_control()

        self.tab_control.pack(expand=True, fill="both")

    def setup_tabs(self):
        pass

    def setup_tab_control(self):
        self.tab_control.add(self.intercept_tab_frame, text="Intercept")
        self.tab_control.add(self.repeater_tab_frame, text="Repeater")
        self.tab_control.add(self.scanner_tab_frame, text="Scanner")


    def __del__(self):
        print("RootWindow Destroyed")