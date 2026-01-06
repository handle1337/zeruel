import sys
import tkinter as tk
import logging

from controllers.gui_bootstrap import RootWindowController
from controllers import server_manager


logger = logging.getLogger(__name__)



HOST = ""
PORT = 7121



class Scanner:
    def __init__(self, master):
        self.master = master


def main():
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', filename='zeruel.log', filemode='w', level=logging.DEBUG)
    logger.info('Started Zeruel Proxy')
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
    if sys.platform.startswith("win"):
        root.state("zoomed")
    else:
        root.attributes("-zoomed", True)

    RootWindowController(root, server)
    root.mainloop()
    logger.info('Finished')


if __name__ == "__main__":
    main()
