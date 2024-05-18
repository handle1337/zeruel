import tkinter as tk
import threading


class InterceptTab:
    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller

        labelframe_control = tk.LabelFrame(self.root, text="Intercepted Request", bg="#a8a8a8", foreground='black')
        labelframe_control.pack(side=tk.LEFT)

        self.intercept_button = tk.Button(labelframe_control, text="Intercept: off", bg="#ededed", foreground='black',
                                          width=20, command=self.on_intercept_toggle)
        self.forward_button = tk.Button(labelframe_control, text="Forward Request", bg="#ededed", foreground='black',
                                        width=20, command=self.on_forward_request)
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
        self.intercepted_request.bind("<Button-3>", self.rc_menu_popup)
        self.rc_menu = tk.Menu(root, tearoff=False)
        #     self.rc_menu.add_command(label="Send to repeater", command=self.send_req_to_repeater)

        self.intercepted_request.pack()

    def rc_menu_popup(self, e):
        self.rc_menu.tk_popup(e.x_root, e.y_root)

    # TODO eventually we wanna be able to send the req to any tab

    def get_intercepted_request(self) -> str:
        request = self.intercepted_request.get("1.0",
                                               'end-1c')  # we use end-1c as to not add a newline
        return request

    def clear(self):
        self.intercepted_request.delete('1.0', tk.END)

    def on_forward_request(self):
        request = self.get_intercepted_request()
        self.controller.forward_request(request)

        self.clear()
        self.controller.update_step()

    def update_intercepted_request_widget(self, data: str = None):
        if data:
            self.intercepted_request.insert(tk.END, data)
            self.intercepted_request.see(tk.END)
            self.root.update()

    def on_intercept_toggle(self):
        if not self.controller.intercepting:
            self.intercept_button['text'] = 'Intercept: on'
            self.controller.toggle_intercept(True)
            self.controller.start_intercepting()
            self.controller.update_loop()
        else:
            self.intercept_button['text'] = 'Intercept: off'
            self.controller.stop_intercepting()
            self.controller.toggle_intercept(False)
            self.clear()
