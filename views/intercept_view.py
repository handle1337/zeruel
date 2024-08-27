import tkinter as tk
from tkinter import ttk
import threading


class InterceptTab:
    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller

        labelframe_control = ttk.LabelFrame(self.root, text="Intercepted Request")
        labelframe_control.pack(side=tk.LEFT)

        self.intercept_button = ttk.Button(labelframe_control, text="Intercept: off",
                                          width=20, command=self._on_intercept_toggle)
        self.forward_button = ttk.Button(labelframe_control, text="Forward Request",
                                        width=20, command=self._on_forward_request)
        self.intercept_button.pack(side=tk.TOP, anchor=tk.NW)
        self.forward_button.pack(side=tk.TOP, anchor=tk.NW)

        self.intercepted_request_widget = tk.Text(labelframe_control,
                                                  borderwidth=3,
                                                  relief=tk.GROOVE,
                                                  width=200,
                                                  height=80,
                                                  font=("Roboto", 14),
                                                  )
        self.intercepted_request_widget.bind("<Button-3>", self.rc_menu_popup)
        self.rc_menu = tk.Menu(root, tearoff=False)
        #     self.rc_menu.add_command(label="Send to repeater", command=self.send_req_to_repeater)

        self.intercepted_request_widget.pack()

    def rc_menu_popup(self, e):
        self.rc_menu.tk_popup(e.x_root, e.y_root)

    # TODO eventually we wanna be able to send the req to any tab

    def get_intercepted_request(self) -> str:
        request = self.intercepted_request_widget.get("1.0",
                                               'end-1c')  # we use end-1c as to not add a newline
        return request

    def clear(self):
        self.intercepted_request_widget.delete('1.0', tk.END)

    def _on_forward_request(self):
        request = self.get_intercepted_request()
        self.controller.forward_request(request)

        self.clear()
        self.controller.update()

    def update_intercepted_request_widget(self, data: str = None):
        if data:
            self.intercepted_request_widget.insert(tk.END, data)
            self.intercepted_request_widget.see(tk.END)
            self.root.update()

    def _on_intercept_toggle(self):
        if not self.controller.intercepting:
            self.intercept_button['text'] = 'Intercept: on'
            self.controller.toggle_intercept(True)
            self.controller.start_intercepting()
            self.controller.update()
        else:
            self.intercept_button['text'] = 'Intercept: off'
            self.controller.stop_intercepting()
            self.controller.toggle_intercept(False)
            self.clear()
