import queue
import threading
import tkinter as tk
from controllers import queue_manager
from util import net


class RepeaterTab:
    def __init__(self, root: tk.Tk):
        print("Initialized Repeater")
        self.root = root

        lf_control_repeater = tk.LabelFrame(self.root, text="Repeater", bg="#a8a8a8", foreground='black')
        lf_control_repeater.pack(fill=tk.BOTH, expand=True)

        send_request_button = tk.Button(lf_control_repeater,
                                     text="Send",
                                     bg="#ededed",
                                     foreground='black',
                                     width=20,
                                     command=self._send_request)
        send_request_button.pack(side=tk.TOP, anchor=tk.NW)

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

    def _get_request(self) -> str:
        request = self.request_text.get("1.0",
                                               'end-1c')  # we use end-1c as to not add a newline
        return request

    def _send_request(self):
        request = self._get_request()
        encoded_request = request.encode()
        print(encoded_request)
        threading.Thread(target=net.send_request, args=(encoded_request,)).start()
        self.update_response_text_widget()

    @staticmethod
    def update_textbox_widget(root, data: str):
        root.delete('1.0', tk.END)
        root.insert(tk.END, data)
        root.see(tk.END)

    def update_response_text_widget(self):
        try:
            response = queue_manager.server_response_queue.get_nowait()
        except queue.Empty:
            response = None
        if response:
            self.update_textbox_widget(self.response_text, response)
        else:
            self.response_text.after(100, self.update_response_text_widget)

