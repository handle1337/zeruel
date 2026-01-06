import tkinter as tk
from tkinter import ttk, filedialog


class BruteforceTab:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.controller = None

        # Root frame
        lf = ttk.LabelFrame(self.root, text="Bruteforce")
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Controls
        controls = ttk.LabelFrame(lf, text="Configuration")
        controls.pack(fill=tk.X, padx=5, pady=5)

        # Wordlist
        ttk.Label(controls, text="Wordlist").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=4
        )
        self.wordlist_entry = ttk.Entry(controls, width=48)
        self.wordlist_entry.grid(
            row=0, column=1, padx=5, pady=4, sticky=tk.W
        )

        self.wordlist_btn = ttk.Button(
            controls, text="Browse", command=self._on_pick_wordlist
        )
        self.wordlist_btn.grid(row=0, column=2, padx=5)

        # Base URL
        ttk.Label(controls, text="Base URL").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=4
        )
        self.base_url_entry = ttk.Entry(controls, width=48)
        self.base_url_entry.grid(
            row=1, column=1, padx=5, pady=4, sticky=tk.W
        )

        # Recursive
        self.recursive_var = tk.BooleanVar(value=False)
        self.recursive_cb = ttk.Checkbutton(
            controls, text="Recursive brute-force", variable=self.recursive_var
        )
        self.recursive_cb.grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=4
        )

        controls.columnconfigure(1, weight=1)

        # Action buttons
        actions = ttk.Frame(lf)
        actions.pack(fill=tk.X, padx=5, pady=(0, 5))

        self.start_btn = ttk.Button(actions, text="Start", command=self._on_start)
        self.stop_btn = ttk.Button(actions, text="Stop", command=self._on_stop)
        self.clear_btn = ttk.Button(actions, text="Clear", command=self._on_clear)

        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.clear_btn.pack(side=tk.LEFT)

        # Status
        status = ttk.LabelFrame(lf, text="Status")
        status.pack(fill=tk.X, padx=5, pady=5)

        self.status_label = ttk.Label(
            status,
            text="Idle",
            justify=tk.LEFT,
        )
        self.status_label.pack(anchor=tk.W, padx=5, pady=(4, 2))

        self.progress_label = ttk.Label(
            status,
            text="Attempts: 0",
        )
        self.progress_label.pack(anchor=tk.W, padx=5, pady=(0, 4))

        # Discovered paths (placeholder UI)
        results = ttk.LabelFrame(lf, text="Discovered Paths")
        results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.results_box = tk.Text(
            results,
            height=8,
            wrap="none",
            state=tk.DISABLED,
        )
        self.results_box.pack(
            fill=tk.BOTH,
            expand=True,
            padx=5,
            pady=5,
        )

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

    def _on_clear(self):
        if self.controller:
            self.controller.clear()


    # UI update helpers
    def set_status(self, text: str):
        self.status_label.config(text=text)
        self.root.update_idletasks()

    def set_progress(self, attempts: int):
        self.progress_label.config(text=f"Attempts: {attempts}")
        self.root.update_idletasks()

    def append_result(self, text: str):
        self.results_box.config(state=tk.NORMAL)
        self.results_box.insert(tk.END, text + "\n")
        self.results_box.see(tk.END)
        self.results_box.config(state=tk.DISABLED)

    def clear_results(self):
        self.results_box.config(state=tk.NORMAL)
        self.results_box.delete("1.0", tk.END)
        self.results_box.config(state=tk.DISABLED)

