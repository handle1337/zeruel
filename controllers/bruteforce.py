import threading
import time
from collections import deque

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

        # Queue for directories to recurse into
        self._recursion_queue = deque()

        # Track discoveries by phase
        self._phase1_discoveries = []
        self._phase2_discoveries = []

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
        # Do not allow clearing while running
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
            # Phase 1: Process initial wordlist
            self._ui_append_result("=== Phase 1: Initial Scan ===\n")
            for host, port, path, request in self.model.generate_requests():
                if not self._run_request(host, port, path, request, phase=1):
                    completed = False
                    break

            # Phase 2: Process discovered directories (recursive mode)
            if self.model.recursive and self._recursion_queue:
                self._ui_append_result(f"\n=== Phase 2: Recursive Scan ({len(self._recursion_queue)} directories queued) ===\n")

                while self._recursion_queue and self._running:
                    directory_path = self._recursion_queue.popleft()
                    self._ui_append_result(f"→ Recursing into: {directory_path}")

                    found_in_dir = 0
                    # Generate requests for this directory
                    for host, port, path, request in self.model.recurse_into_directory(directory_path):
                        if not self._run_request(host, port, path, request, phase=2):
                            completed = False
                            break

                        # Track if we found anything in this directory
                        if path in [p for p, _ in self._phase2_discoveries]:
                            found_in_dir += 1

                    if found_in_dir == 0:
                        self._ui_append_result(f"  (no paths found in {directory_path})")

                    self._ui_append_result("")  # Blank line for readability

                    if not self._running:
                        completed = False
                        break
            elif self.model.recursive and not self._recursion_queue:
                self._ui_append_result("\n=== Phase 2: No directories found to recurse ===\n")

            # Show final summary
            self._show_summary()

        finally:
            self._running = False
            final_state = "Completed" if completed else "Stopped"
            summary = self._build_summary()
            self._ui_status(f"{final_state}\n{summary}")

    def _run_request(self, host: str, port: int, path: str, request: bytes, phase: int = 1) -> bool:
        """
        Execute a single request and process the response.

        Args:
            phase: 1 for initial scan, 2 for recursive scan

        Returns:
            True if should continue, False if stopped
        """
        if not self._running:
            return False

        response = self.server.send_bruteforce(
            hostname=host,
            port=port,
            data=request,
        )

        status = self.model._get_status(response)
        self._attempted += 1
        self._classify_status(status)

        # Track hits (anything except 404)
        if status is not None and status != 404:
            self._hits += 1
            self._discovered_paths.append((path, status))

            # Track by phase
            if phase == 1:
                self._phase1_discoveries.append((path, status))
            else:
                self._phase2_discoveries.append((path, status))

            # Better formatting based on depth
            depth = path.count('/') - 1
            indent = "  " * depth
            self._ui_append_result(f"{indent}{path} [{status}]")

            # Check if we should recurse into this path
            if self.model.recursive and self.model.should_recurse(path, status):
                # Only queue if not already queued or visited for recursion
                if path not in self._recursion_queue:
                    self._recursion_queue.append(path)
                    self._ui_append_result(f"{indent}  └─ Queued for recursion")

        self._ui_progress(self._attempted)

        # tiny yield so UI stays responsive
        time.sleep(0.005)

        return True


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
        self._phase1_discoveries = []
        self._phase2_discoveries = []

    def _reset_state(self):
        self._attempted = 0
        self._hits = 0
        self._discovered_paths.clear()
        self._phase1_discoveries.clear()
        self._phase2_discoveries.clear()
        self._recursion_queue.clear()

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

    def _show_summary(self):
        """Display final summary of all discoveries"""
        self._ui_append_result("\n" + "="*50)
        self._ui_append_result("=== SCAN SUMMARY ===")
        self._ui_append_result("="*50 + "\n")

        # Phase 1 discoveries
        if self._phase1_discoveries:
            self._ui_append_result(f"Phase 1 Discoveries ({len(self._phase1_discoveries)}):")
            for path, status in self._phase1_discoveries:
                self._ui_append_result(f"  {path} [{status}]")
            self._ui_append_result("")
        else:
            self._ui_append_result("Phase 1 Discoveries: None\n")

        # Phase 2 discoveries
        if self._phase2_discoveries:
            self._ui_append_result(f"Phase 2 Discoveries ({len(self._phase2_discoveries)}):")
            for path, status in self._phase2_discoveries:
                self._ui_append_result(f"  {path} [{status}]")
            self._ui_append_result("")
        else:
            self._ui_append_result("Phase 2 Discoveries: None\n")

        # Overall stats
        self._ui_append_result("Overall Statistics:")
        self._ui_append_result(f"  Total Attempts: {self._attempted}")
        self._ui_append_result(f"  Total Hits: {self._hits}")
        self._ui_append_result(f"  404s: {self._results['404']}")
        self._ui_append_result(f"  2xx: {self._results['2xx']}")
        self._ui_append_result(f"  3xx: {self._results['3xx']}")
        self._ui_append_result(f"  403: {self._results['403']}")
        self._ui_append_result(f"  401: {self._results['401']}")
        self._ui_append_result(f"  Other: {self._results['other']}")

