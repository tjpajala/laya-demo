"""Starts and supervises `open-jev-serve` (Zefan-Cai/Open-Jev's own HTTP server)
as a local subprocess, and keeps it resident so the model is loaded once and
reused across every Open-Jev job rather than reloaded per run.
"""

from __future__ import annotations

import atexit
import subprocess
import threading
import time
import urllib.error
import urllib.request


class OpenJevServerManager:
    def __init__(self, checkpoint_path: str, host: str = "127.0.0.1", port: int = 8791, device: str = "cpu"):
        self.checkpoint_path = checkpoint_path
        self.host = host
        self.port = port
        self.device = device
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def ensure_running(self, timeout_s: float = 900.0) -> None:
        with self._lock:
            if self._proc is not None and self._proc.poll() is not None:
                self._proc = None
            if self._proc is not None and self._healthy():
                return
            self._start(timeout_s)

    def _healthy(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.base_url}/health", timeout=2) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError, TimeoutError):
            return False

    def _start(self, timeout_s: float) -> None:
        cmd = [
            "open-jev-serve",
            "--checkpoint", self.checkpoint_path,
            "--device", self.device,
            "--host", self.host,
            "--port", str(self.port),
        ]
        self._proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        atexit.register(self.stop)

        deadline = time.time() + timeout_s
        tail: list[str] = []
        while time.time() < deadline:
            if self._proc.poll() is not None:
                if self._proc.stdout is not None:
                    tail.append(self._proc.stdout.read())
                raise RuntimeError(f"open-jev-serve exited early: {''.join(tail)[-2000:]}")
            if self._healthy():
                return
            time.sleep(1.0)
        self.stop()
        raise TimeoutError(f"open-jev-serve did not become healthy within {timeout_s:.0f}s")

    def stop(self) -> None:
        proc, self._proc = self._proc, None
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
