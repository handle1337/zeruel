import tkinter as tk

from controllers.gui_bootstrap import RootWindowController
from models.proxy import Server

HOST = ""
PORT = 7121


# TODO: when intercept is turned off, we must forward requests immediately
# TODO: must also implement ssl.... somehow
# TODO: instead of turning the proxy on and off we should just change how we handle reqs


class Scanner:
    def __init__(self, master):
        self.master = master



def app_loop(root, app):
    while True:
        root.update_idletasks()
        root.update()


def main():
    print("[[Zeruel Proxy]]")
    proxy_server_thread = Server(HOST, PORT)
    proxy_server_thread.start()
    root = tk.Tk()
    root.wm_state('zoomed')
    app = RootWindowController(root)
    app_loop(root, app)


if __name__ == "__main__":
    main()
