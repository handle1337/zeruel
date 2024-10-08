import sys
import tkinter as tk
from tkinter import ttk

from controllers.gui_bootstrap import RootWindowController
from controllers import server_manager

HOST = ""
PORT = 7121



class Scanner:
    def __init__(self, master):
        self.master = master


def main():
    print("[[Zeruel Proxy]]")

    server = server_manager.new_server()
    server.start()
    print(server_manager.server_threads)
    root = tk.Tk()

    def kill():
        server_manager.stop_all()
        root.quit()
        root.destroy()
        sys.exit()

    root.protocol('WM_DELETE_WINDOW', kill)
    root.wm_state('zoomed')
    RootWindowController(root, server)
    root.mainloop()


if __name__ == "__main__":
    main()
