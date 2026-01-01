import threading
import time

from views.bruteforce_view import BruteforceTab
from models.bruteforce import BruteforceModel


class BruteforceController:
    def __init__(self, root, intercept_controller):
        """
        root: ttk.Frame from RootWindow (notebook tab frame)
        intercept_controller: InterceptController instance
        """

        # We reuse the same server thread used by intercept/repeater
        self.server = intercept_controller.server

        # view
        self.view = BruteforceTab(root)
        self.view.set_controller(self)

        # model
        self.model = BruteforceModel()

        # state
        self._running = False
        self._thread = None
        self._attempted = 0

    # UI entry points
    def start(self, wordlist_path: str, base_url: str, recursive: bool):
        if self._running:
            return

        if not wordlist_path or not base_url:
            self.view.set_status("Missing wordlist or base URL")
            return

        try:
            self.model.load_wordlist(wordlist_path)
        except Exception as e:
            self.view.set_status(f"Wordlist error: {e}")
            return

        self.model.set_target(base_url)
        self.model.set_recursive(recursive)

        self._attempted = 0
        self._running = True

        self.view.set_status("Running")
        self.view.set_progress(0)

        # Start background thread
        self._thread = threading.Thread(
            target=self._run,
            daemon=True
        )
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.view.set_status("Stopped")

    # Background worker
    def _run(self):
        """
        Background bruteforce loop.
        Model generates requests, controller sends them.
        """
        try:
            for request_bytes in self.model.generate_requests():
                if not self._running:
                    break

                # We send directly via server thread
                self.server.send_data(request_bytes)
                self._attempted += 1

                # Update UI
                self.view.set_progress(self._attempted)

                # Throttling (prevents UI starvation)
                time.sleep(0.01)

        finally:
            self._running = False
            self.view.set_status("Idle")
