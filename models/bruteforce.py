from urllib.parse import urlparse
import os


class BruteforceModel:
    def __init__(self):
        self.wordlist = []
        self.visited = set()

        self.host = None
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
        """
        if not self.host:
            raise RuntimeError("Target not configured")

        for entry in self.wordlist:
            path = f"/{entry}"

            if path in self.visited:
                continue

            self.visited.add(path)
            yield self.host, self.port, path, self._build_request(path)

            # structural recursion
            if self.recursive:
                yield from self._recurse_into(path)

    def _recurse_into(self, base_path: str):
        """
        Generates /base/word paths
        """
        base = base_path.rstrip("/") + "/"

        for sub in self.wordlist:
            sub_path = base + sub

            if sub_path in self.visited:
                continue

            self.visited.add(sub_path)
            yield self.host, self.port, sub_path, self._build_request(sub_path)

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

