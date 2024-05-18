import sys
import tkinter as tk

from controllers.gui_bootstrap import RootWindowController
from controllers import server_manager

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
    app = RootWindowController(root, server)
    app_loop(root, app)


if __name__ == "__main__":
    main()
