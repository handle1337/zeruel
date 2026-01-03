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

        # Shared server (intercept/repeater/bruteforce)
        self.server = intercept_controller.server

        # View
        self.view = BruteforceTab(root)
        self.view.set_controller(self)

        # Model
        self.model = BruteforceModel()

        # Runtime state
        self._running = False
        self._thread = None
        self._attempted = 0

        self._reset_results()


    # Public UI entry points
    def start(self, wordlist_path: str, base_url: str, recursive: bool):
        if self._running:
            return

        if not wordlist_path or not base_url:
            self._ui_status("Missing wordlist or base URL")
            return

        try:
            self.model.load_wordlist(wordlist_path)
            self.model.set_target(base_url)
            self.model.set_recursive(recursive)
        except Exception as e:
            self._ui_status(str(e))
            return

        self._reset_state()
        self._ui_clear_results()
        self._running = True

        self._ui_status("Running")
        self._ui_progress(0)

        self._thread = threading.Thread(
            target=self._run,
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self._ui_status("Stopping...")

    def clear(self):
        # Do not allow clearing while runnign
        if self._running:
            self._ui_status("Stop the scan before clearing")
            return

        self._reset_state()
        self._ui_clear_results()
        self._ui_progress(0)
        self._ui_status("Idle")


    # Background worker
    def _run(self):
        completed = True
        try:
            for host, port, path, request in self.model.generate_requests():
                if not self._running:
                    completed = False
                    break

                response = self.server.send_bruteforce(
                    hostname=host,
                    port=port,
                    data=request,
                )

                status = self.model._get_status(response)
                self._attempted += 1
                self._classify_status(status)

                if status is not None and status != 404:
                    self._hits += 1
                    self._discovered_paths.append((path, status))
                    self._ui_append_result(f"{path} [{status}]")

                self._ui_progress(self._attempted)

                # tiny yield so UI stays responsive
                time.sleep(0.005)

        finally:
            self._running = False
            final_state = "Completed" if completed else "Stopped"
            summary = self._build_summary()
            self._ui_status(f"{final_state}\n{summary}")


    # Internal helpers
    def _reset_results(self):
        self._results = {
            "2xx": 0,
            "3xx": 0,
            "401": 0,
            "403": 0,
            "404": 0,
            "other": 0,
        }
        self._hits = 0
        self._discovered_paths = []

    def _reset_state(self):
        self._attempted = 0
        self._hits = 0
        self._discovered_paths.clear()

        for k in self._results:
            self._results[k] = 0

    def _classify_status(self, status):
        if status is None:
            self._results["other"] += 1
        elif 200 <= status < 300:
            self._results["2xx"] += 1
        elif 300 <= status < 400:
            self._results["3xx"] += 1
        elif status == 401:
            self._results["401"] += 1
        elif status == 403:
            self._results["403"] += 1
        elif status == 404:
            self._results["404"] += 1
        else:
            self._results["other"] += 1

    def _build_summary(self) -> str:
        return (
            f"Hits: {self._hits}\n"
            f"404s: {self._results['404']}"
        )


    # Thread-safe UI helpers
    def _ui_status(self, text: str):
        self.view.root.after(0, self.view.set_status, text)

    def _ui_progress(self, attempts: int):
        self.view.root.after(0, self.view.set_progress, attempts)

    def _ui_append_result(self, text: str):
        self.view.root.after(0, self.view.append_result, text)

    def _ui_clear_results(self):
        self.view.root.after(0, self.view.clear_results)

