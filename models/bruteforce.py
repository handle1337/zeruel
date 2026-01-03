from urllib.parse import urlparse
import os


class BruteforceModel:
    def __init__(self):
        self.wordlist = []
        self.visited = set()
        self.host: str | None = None
        self.port = 80
        self.scheme = "http"
        self.recursive = False

    # Configuration
    def load_wordlist(self, path: str):
        if not os.path.isfile(path):
            raise FileNotFoundError(path)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            self.wordlist = [
                line.strip().strip("/")
                for line in f
                if line.strip() and not line.startswith("#")
            ]

    def set_target(self, base_url: str):
        parsed = urlparse(base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid base URL")

        if not parsed.hostname:
            raise ValueError("Invalid hostname in URL")

        self.host = parsed.hostname
        self.scheme = parsed.scheme
        self.port = parsed.port or (443 if self.scheme == "https" else 80)
        # reset per run
        self.visited.clear()

    def set_recursive(self, recursive: bool):
        self.recursive = recursive

    # Request generation
    def generate_requests(self):
        """
        Yields:
            (hostname, port, path, request_bytes)

        This now only yields initial wordlist paths.
        The controller will handle feeding back discovered directories.
        """
        if not self.host:
            raise RuntimeError("Target not configured")

        host = self.host

        for entry in self.wordlist:
            path = f"/{entry}"
            if path in self.visited:
                continue
            self.visited.add(path)
            yield host, self.port, path, self._build_request(path)

    def recurse_into_directory(self, directory_path: str):
        """
        Generates requests for a discovered directory.
        Called by the controller when a valid directory is found.

        Args:
            directory_path: The directory path to recurse into (e.g., "/admin")

        Yields:
            (hostname, port, path, request_bytes)
        """
        if not self.recursive:
            return

        if not self.host:
            return

        base = directory_path.rstrip("/") + "/"
        host = self.host

        for sub in self.wordlist:
            sub_path = base + sub
            if sub_path in self.visited:
                continue
            self.visited.add(sub_path)
            yield host, self.port, sub_path, self._build_request(sub_path)

    def should_recurse(self, path: str, status: int | None) -> bool:
        """
        Determines if we should recurse into this path based on:
        1. Status code indicates valid directory
        2. Path looks like a directory (no file extension or ends with /)

        Args:
            path: The path that was tested
            status: HTTP status code received

        Returns:
            True if we should recurse into this path
        """
        # Check status first
        if status is None or status not in (200, 301, 302, 403):
            return False

        # Check if path looks like a file (has extension)
        # Common web extensions to avoid recursing into
        file_extensions = (
            '.html', '.htm', '.php', '.asp', '.aspx', '.jsp', '.js',
            '.css', '.txt', '.xml', '.json', '.pdf', '.jpg', '.png',
            '.gif', '.zip', '.tar', '.gz', '.sql', '.bak', '.log'
        )

        path_lower = path.lower()
        if any(path_lower.endswith(ext) for ext in file_extensions):
            return False

        return True

    # Helpers
    def _build_request(self, path: str) -> bytes:
        return (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"User-Agent: Zeruel-Bruteforce\r\n"
            f"Accept: */*\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode()

    def _get_status(self, response: bytes) -> int | None:
        try:
            line = response.split(b"\r\n", 1)[0]
            return int(line.split()[1])
        except Exception:
            return None
