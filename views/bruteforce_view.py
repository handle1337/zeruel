import tkinter as tk
from tkinter import ttk, filedialog


class BruteforceTab:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.controller = None

        lf = ttk.LabelFrame(self.root, text="Bruteforce")
        lf.pack(fill=tk.BOTH, expand=True)

        # Controls
        controls = ttk.Frame(lf)
        controls.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # Wordlist picker
        ttk.Label(controls, text="Wordlist:").grid(row=0, column=0, sticky=tk.W)
        self.wordlist_entry = ttk.Entry(controls, width=50)
        self.wordlist_entry.grid(row=0, column=1, padx=5)

        self.wordlist_btn = ttk.Button(
            controls, text="Browse", command=self._on_pick_wordlist
        )
        self.wordlist_btn.grid(row=0, column=2)

        # Base URL/host
        ttk.Label(controls, text="Base URL:").grid(row=1, column=0, sticky=tk.W)
        self.base_url_entry = ttk.Entry(controls, width=50)
        self.base_url_entry.grid(row=1, column=1, padx=5, pady=5)

        # Recursive checkbox
        self.recursive_var = tk.BooleanVar(value=False)
        self.recursive_cb = ttk.Checkbutton(
            controls, text="Recursive", variable=self.recursive_var
        )
        self.recursive_cb.grid(row=2, column=1, sticky=tk.W)

        # Start/Stop buttons
        buttons = ttk.Frame(lf)
        buttons.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.start_btn = ttk.Button(buttons, text="Start", command=self._on_start)
        self.stop_btn = ttk.Button(buttons, text="Stop", command=self._on_stop)

        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT)

        # Status / Progress
        status = ttk.LabelFrame(lf, text="Status")
        status.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_label = ttk.Label(status, text="Idle")
        self.status_label.pack(anchor=tk.W, padx=5, pady=2)

        self.progress_label = ttk.Label(status, text="Attempts: 0")
        self.progress_label.pack(anchor=tk.W, padx=5)

    # Controller binding
    def set_controller(self, controller):
        self.controller = controller

    # UI event handlers
    def _on_pick_wordlist(self):
        path = filedialog.askopenfilename()
        if path:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, path)

    def _on_start(self):
        if not self.controller:
            return

        self.controller.start(
            wordlist_path=self.wordlist_entry.get(),
            base_url=self.base_url_entry.get(),
            recursive=self.recursive_var.get(),
        )

    def _on_stop(self):
        if self.controller:
            self.controller.stop()

    # UI update helpers (called by controller)
    def set_status(self, text: str):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def set_progress(self, attempts: int):
        self.progress_label.config(text=f"Attempts: {attempts}")
        self.root.update_idletasks()

