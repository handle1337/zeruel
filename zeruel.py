import queue
import socket
import ssl
from threading import Thread, Lock
import tkinter as tk
from tkinter import ttk

HOST = ""
PORT = 7121

# TODO: when intercept is turned off, we must forward requests immediately
# TODO: must also implement ssl.... somehow
class Server(Thread):
    def __init__(self, host, port, _queue, lock):
        super().__init__()
        self.running = False
        self.server_socket = None
        self.host = host
        self.port = port
        self.buffer_size = 8192
        self.queue = _queue
        self.lock = lock

        self._data = None

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.running = True
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                                          1)  # This is a necessary step since we need to reuse the port immediately
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            print(f"{self.server_socket}")
        except Exception as e:
            print(e)

        while self.running:
            self.client_socket, client_address = self.server_socket.accept()
            print(f"{self.client_socket}")

            # We stop taking in new data while we deal with the current req
            with self.lock:
                self._data = self.client_socket.recv(self.buffer_size)

                self.queue.put(self._data)  # we put it in the queue to receive it later when dealing with GUI

                #break  # make this only the case when intercepting
                # self.forward_data(client_socket, data, client_address)

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    @staticmethod
    def parse_data(data):
        print(data)
        first_line = data.split(b'\n')[0]

        url = first_line.split()[1]

        http_pos = url.find(b'://')  # Finding the position of ://
        if http_pos == -1:
            temp = url
        else:

            temp = url[(http_pos + 3):]

        port_pos = temp.find(b':')

        webserver_pos = temp.find(b'/')
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if port_pos == -1 or webserver_pos < port_pos:
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos + 1):])[:webserver_pos - port_pos - 1])
            webserver = temp[:port_pos]
        print(data)
        return {"server": webserver, "port": port, "data": data}

    def forward_data(self):
        if not self._data:
            print("no data")
            return
        request = self.parse_data(self._data)
        self.send_data(webserver=request["server"],
                       port=80,
                       data=request["data"])

    def send_data(self, webserver, port, data):
        forward_socket = None
        try:
            print("data " + data.decode('utf-8'))
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            #context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

            #wrapped_socket = context.wrap_socket(forward_socket)

            forward_socket.connect((webserver, port))
            forward_socket.send(data)
            while True:
                reply = forward_socket.recv(self.buffer_size)
                if len(reply) > 0:
                    print("reply " + reply.decode('utf-8'))
                    self.client_socket.send(reply)

        except Exception as e:
            forward_socket.close()
            print(f"err: {e}")
        forward_socket.close()


class Repeater:
    def __init__(self, master):
        print("Initialized Repeater")
        self.master = master

        lf_control_repeater = tk.LabelFrame(self.master, text="Repeater", bg="#a8a8a8", foreground='black')
        lf_control_repeater.pack(fill=tk.BOTH, expand=True)

        intercept_button = tk.Button(lf_control_repeater, text="Send", bg="#ededed", foreground='black', width=20)
        intercept_button.pack(side=tk.TOP, anchor=tk.NW)

        lf_control_request = tk.LabelFrame(lf_control_repeater, text="Request", bg="#a8a8a8", foreground='black')
        lf_control_response = tk.LabelFrame(lf_control_repeater, text="Response", bg="#a8a8a8", foreground='black')

        lf_control_request.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lf_control_response.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Here we set width and height to 1 so we can let the geometry manager expand the widget to fill extra space
        self.request_text = tk.Text(lf_control_request,
                                    borderwidth=3,
                                    relief=tk.GROOVE,
                                    bg="black",
                                    foreground='#00ff22',
                                    font=("Roboto", 14),
                                    insertbackground="#00ff22",
                                    width=1,
                                    height=1,
                                    )

        self.response_text = tk.Text(lf_control_response,
                                     borderwidth=3,
                                     relief=tk.GROOVE,
                                     bg="black",
                                     foreground='#00ff22',
                                     font=("Roboto", 14),
                                     insertbackground="#00ff22",
                                     width=1,
                                     height=1
                                     )

        self.request_text.pack(fill=tk.BOTH, expand=True)
        self.response_text.pack(fill=tk.BOTH, expand=True)


class Scanner:
    def __init__(self, master):
        self.master = master


class Intercept:
    def __init__(self, master):
        print("Initialized Intercept")
        self.master = master

        self.queue = queue.Queue()
        self.lock = Lock()

        labelframe_control = tk.LabelFrame(self.master, text="Intercepted Request", bg="#a8a8a8", foreground='black')
        labelframe_control.pack(side=tk.LEFT)

        self.intercept_button = tk.Button(labelframe_control, text="Intercept: off", bg="#ededed", foreground='black',
                                          width=20, command=self.intercept_toggle)
        self.forward_button = tk.Button(labelframe_control, text="Forward Request", bg="#ededed", foreground='black',
                                        width=20, command=self.forward_request)
        self.intercept_button.pack(side=tk.TOP, anchor=tk.NW)
        self.forward_button.pack(side=tk.TOP, anchor=tk.NW)

        self.intercepted_request = tk.Text(labelframe_control,
                                           borderwidth=3,
                                           relief=tk.GROOVE,
                                           bg="black",
                                           foreground='#00ff22',
                                           width=200,
                                           height=80,
                                           font=("Roboto", 14),
                                           insertbackground="#00ff22"
                                           )

        self.intercepted_request.pack()


    def forward_request(self):
        if not self.server_thread.running:
            pass
        else:
            forward_thread = Thread(target=self.server_thread.forward_data)
            forward_thread.start()
            self.start_proxy()
        self.intercepted_request.delete('1.0', tk.END)
        self.update()

    def start_proxy(self):
        self.server_thread = Server(HOST, PORT, self.queue, self.lock)
        self.server_thread.start()

    def stop_proxy(self):
        if hasattr(self, 'networking_thread') and self.networking_thread:
            self.server_thread.stop()
            self.server_thread.join()

    def update(self):
        try:
            with self.lock:
                while not self.queue.empty():
                    self.intercepted_request.delete('1.0', tk.END)

                    data = self.queue.get_nowait().decode("utf-8")
                    self.intercepted_request.insert(tk.END, data)
                    self.intercepted_request.see(tk.END)
                    self.master.update()  # update the GUI to display new data
        except queue.Empty:
            pass
        #self.master.after(100, self.update)
        #do stuff here after

    def intercept_toggle(self):
        if self.intercept_button['text'] == 'Intercept: off':
            self.intercept_button['text'] = 'Intercept: on'
            self.start_proxy()
            self.update()
        else:
            self.intercept_button['text'] = 'Intercept: off'
            self.stop_proxy()


class RootWindow:
    def __init__(self, master):
        self.master = master
        master.title("Zeruel Proxy")

        self.networking_thread = None

        window_width, window_height = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        self.master.geometry("%dx%d+0+0" % (window_width, window_height))
        self.tab_control = ttk.Notebook(self.master)

        self.intercept_tab = tk.Frame(self.tab_control, bg="#8c8787")
        self.repeater_tab = tk.Frame(self.tab_control, bg="#8c8787")
        self.scanner_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.intercept_tab, text="Intercept")
        self.tab_control.add(self.repeater_tab, text="Repeater")
        self.tab_control.add(self.scanner_tab, text="Scanner")

        self.tab_control.pack(expand=True, fill="both")

        self.intercept = Intercept(self.intercept_tab)
        self.repeater = Repeater(self.repeater_tab)

    def __del__(self):
        print("RootWindow Destroyed")


def app_loop(root, app):
    while True:
        root.update_idletasks()
        root.update()


def main():
    print("[[Zeruel Proxy]]")
    root = tk.Tk()
    root.wm_state('zoomed')
    app = RootWindow(root)
    app_loop(root, app)


if __name__ == "__main__":
    main()
