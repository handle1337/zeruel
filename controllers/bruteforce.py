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

        # Reuse existing server thread (shared with intercept/repeater)
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

        # results
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


    # UI entry points
    def start(self, wordlist_path: str, base_url: str, recursive: bool):
        if self._running:
            return

        if not wordlist_path or not base_url:
            self.view.set_status("Missing wordlist or base URL")
            return

        try:
            self.model.load_wordlist(wordlist_path)
            self.model.set_target(base_url)
            self.model.set_recursive(recursive)
        except Exception as e:
            self.view.set_status(str(e))
            return

        self._attempted = 0
        self._running = True

        self.view.set_status("Running")
        self.view.set_progress(0)

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
        completed = True
        try:
            for host, port, path, request in self.model.generate_requests():
                if not self._running:
                    completed = False
                    break

                response = self.server.send_bruteforce(
                    hostname=host,
                    port=port,
                    data=request
                )
                status = self.model._get_status(response)
                self._attempted += 1

                # classify response
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

                # hit detection
                if status and status != 404:
                    self._hits += 1
                    self._discovered_paths.append((path, status))

                # update UI
                self.view.set_progress(self._attempted)
                self.view.set_status(self._build_status_text())

                time.sleep(0.01)

        finally:
            self._running = False
            prefix = "Completed" if completed else "Stopped"
            self.view.set_status(
                f"{prefix}\n"
                f"{self._build_status_text()}"
            )

    # helper function to make status text
    def _build_status_text(self) -> str:
        return (
            f"Hits: {self._hits}\n"
            f"404: {self._results['404']}\n"
            f"Attempts: {self._attempted}\n\n"
            f"{self._format_discoveries()}"
        )

    # helper function to format discoveries
    def _format_discoveries(self) -> str:
        return "\n".join(
            f"{path} {status}"
            for path, status in self._discovered_paths[-5:]
        )
