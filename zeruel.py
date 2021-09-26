import tkinter as tk
from tkinter import ttk

class Repeater:
    def __init__(self, master):
        print("Initialized Repeater")
        self.master = master

        lf_control_repeater = tk.LabelFrame(self.master, text="Repeater", bg="#a8a8a8", foreground='black')
        lf_control_repeater.pack(fill=tk.BOTH, expand=True)

        intercept_button = tk.Button(lf_control_repeater, text="Send", bg="#ededed", foreground='black', width = 20)
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
        pass

class Intercept:
    def __init__(self, master):
        print("Initialized Intercept")
        self.master = master


        labelframe_control = tk.LabelFrame(self.master, text="Intercepted Request", bg="#a8a8a8", foreground='black')
        labelframe_control.pack(side=tk.LEFT)

        intercept_button = tk.Button(labelframe_control, text="Intercept: off", bg="#ededed", foreground='black')
        intercept_button.pack(side=tk.TOP, anchor=tk.NW)

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
    
    def intercept_request(self):
        # this needs to be multithreaded
        request = "placeholder"
        return request

class RootWindow:
    def __init__(self, master):
        self.master = master
        master.title("Zeruel Proxy")
        self.resolution = self.get_monitor_resolution()
        master.geometry(f"{self.resolution[0]}x{self.resolution[1]}")

        tab_control = ttk.Notebook(self.master)

        intercept_tab = tk.Frame(tab_control, bg="#8c8787")
        repeater_tab = tk.Frame(tab_control, bg="#8c8787")
        scanner_tab = ttk.Frame(tab_control)

        tab_control.add(intercept_tab, text="Intercept")
        tab_control.add(repeater_tab, text="Repeater")
        tab_control.add(scanner_tab, text="Scanner")

        tab_control.pack(expand=True, fill="both")

        intercept = Intercept(intercept_tab)
        repeater = Repeater(repeater_tab)

    def get_monitor_resolution(self):
        temp_root = tk.Tk()
        temp_root.update_idletasks()
        temp_root.attributes('-fullscreen', True)
        temp_root.state('iconic')
        width = temp_root.winfo_screenwidth()
        height = temp_root.winfo_screenheight()
        temp_root.destroy()
        print(f"Resolution: {width}x{height}")
        return width, height

    def __del__(self):
        print("RootWindow Destroyed")

def main():
    print("[[Zeruel Proxy]]")
    root = tk.Tk()
    app = RootWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()