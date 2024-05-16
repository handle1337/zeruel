import tkinter as tk

class RepeaterTab:
    def __init__(self, master, proxy_server):
        print("Initialized Repeater")
        self.master = master
        self.proxy_server = proxy_server

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