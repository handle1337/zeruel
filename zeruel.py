import queue
import sys
import socket
import ssl
from threading import Thread, Lock
import tkinter as tk
from tkinter import ttk

HOST = ""
PORT = 7121

# TODO: when intercept is turned off, we must forward requests immediately
# TODO: must also implement ssl.... somehow
# TODO: instead of turning the proxy on and off we should just change how we handle reqs
class Server(Thread):
    def __init__(self, host, port, server_request_queue, client_request_queue, lock):
        super().__init__()
        self.running = False
        self.server_socket = None
        self.host = host
        self.port = port
        self.buffer_size = 8192
        self.server_request_queue = server_request_queue
        self.client_request_queue = client_request_queue
        self.lock = lock

        self.client_data = None

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,
                                          1)  # This is a necessary step since we need to reuse the port immediately
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            print(f"{self.server_socket}")
        except KeyboardInterrupt:
            self.stop()
            sys.exit(1)
        except socket.error as e:
            print(e)
        self.handle_client()

    def handle_client(self):
        while self.running:
            self.client_socket, client_address = self.server_socket.accept()
            print(f"{self.client_socket} {client_address[0]} {client_address[1]}")

            # We stop taking in new data while we deal with the current req
            #with self.lock:
                # get request from client/browser
            self.client_data = self.client_socket.recv(self.buffer_size)
            request = self.parse_data(self.client_data)

            if request:
                send_data_thread = Thread(target=self.send_data, args=(request["server"],
                                        request["port"],
                                        request["data"]))
                if "CONNECT" in str(self.client_data):
                    send_data_thread.start()
                else: 
                    print("\nsending to gui\n")
                    self.client_request_queue.put(self.client_data)  # we display this in the GUI
                    self.server_request_queue.put(self.parse_data(self.client_data)) # we queue parsed data to be used when forwarding request

                    break # we stop receiving connections until req is forwarded
                    # make this only the case when intercepting
        if not send_data_thread.is_alive():
            pass
            #send_data_thread.join()


    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
            print("killed proxy")
            print(f"client {self.client_socket}")

    @staticmethod
    def parse_data(data):
        if not data:
            return
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
        if not self.client_data:
            print("no data")
            return
        request = self.parse_data(self.client_data)
        send_data_thread = Thread(target=self.send_data, args=(request["server"],
                       request["port"],
                       request["data"]))
        self.client_data = None
        send_data_thread.start()


    def send_data(self, hostname, port, data):
        hostname = hostname.decode('utf-8')
        print("\nsend data\n")
        remote_socket = None
        try:
  
            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((hostname, port))
            #print("\ndata " + data.decode('utf-8'))
            print("\nwebserver " + hostname)
            print("\nport " + str(port))

            context = ssl.create_default_context()
            if port == 80:
                remote_socket.sendall(data)
                while True:
                    chunk = remote_socket.recv(self.buffer_size)
                    if not chunk:
                        break
                    print("reply " + chunk.decode('utf-8'))
                    self.client_socket.sendall(chunk) # send back to browser 


            # with context.wrap_socket(remote_socket, server_hostname=hostname) as wrapped_socket:
            #     wrapped_socket.sendall(data)
            #     while True:
            #         chunk = wrapped_socket.recv(self.buffer_size)
            #         if not chunk:
            #             break
            #         #print("reply " + chunk.decode('utf-8'))
            #         self.client_socket.sendall(chunk) # send back to browser    

        except Exception as e:
            remote_socket.close()
            print(f"err: {e}")
        remote_socket.close()


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
        self.intercepting = False

        self.request_sent = False

        self.server_queue = queue.Queue()
        self.client_queue = queue.Queue()
        self.lock = Lock()

        self.server_thread = None

        labelframe_control = tk.LabelFrame(self.master, text="Intercepted Request", bg="#a8a8a8", foreground='black')
        labelframe_control.pack(side=tk.LEFT)

        self.intercept_button = tk.Button(labelframe_control, text="Intercept: off", bg="#ededed", foreground='black',
                                          width=20, command=self.intercept_toggle)
        self.forward_button = tk.Button(labelframe_control, text="Forward Request", bg="#ededed", foreground='black',
                                        width=20, command=self.forward_request_action)
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


    def forward_request_action(self):
        if self.server_thread and self.server_thread.running:
                if not self.server_queue.empty():  
                    request = self.server_queue.get()
                    print(f"From Server queue: {request}")
                    webserver = request["server"]
                    port = request["port"]
                    data = request["data"]
                    Thread(target=self.server_thread.send_data, args=(webserver, port, data)).start()
                    self.request_sent = True
                else:
                    print("queue empty")

        self.intercepted_request.delete('1.0', tk.END)
        self.update_step()

    def start_proxy(self):
        self.server_thread = Server(HOST, PORT, self.server_queue, self.client_queue, self.lock)
        self.server_thread.start()

    def stop_proxy(self):
        self.server_thread.stop()
        self.server_thread.join()

    def update_step(self):
        if not self.client_queue.empty():
            self.intercepted_request.delete('1.0', tk.END)

            data = self.client_queue.get_nowait().decode("utf-8")
            self.intercepted_request.insert(tk.END, data)
            self.intercepted_request.see(tk.END)
            self.master.update()  # update the GUI to display new data
        

    def update_loop(self):
        if self.intercepting:
            self.update_step()
            self.master.after(100, self.update_loop)

    def intercept_toggle(self):
        if self.intercepting == False:
            self.intercepting = True
            self.intercept_button['text'] = 'Intercept: on'
            self.start_proxy()
            self.update_loop()
        else:
            self.intercepting = False
            self.intercept_button['text'] = 'Intercept: off'
            self.stop_proxy()
            self.update_step()


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
