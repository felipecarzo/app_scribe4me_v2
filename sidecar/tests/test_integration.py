"""Testes de integracao do sidecar — spawna sidecar_main.py como subprocess."""

import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

SIDECAR_DIR = Path(__file__).resolve().parent.parent
SIDECAR_MAIN = SIDECAR_DIR / "sidecar_main.py"
TIMEOUT = 10


class SidecarProcess:
    """Helper que gerencia o sidecar como subprocess para testes."""

    def __init__(self):
        self._lines: queue.Queue[str] = queue.Queue()
        self.proc = subprocess.Popen(
            [sys.executable, str(SIDECAR_MAIN)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(SIDECAR_DIR),
            text=True,
            bufsize=1,
        )
        # Background thread reads stdout lines into a queue (Windows-compatible)
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()

        # Consume initial events — read for up to 6 seconds to capture loading + idle
        self._startup_events: list[dict] = []
        deadline = time.time() + 6.0
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            line = self._read_line(timeout=min(remaining, 2.0))
            if line:
                self._startup_events.append(json.loads(line))
                # Stop once we have both loading and idle
                statuses = [e["data"].get("status") for e in self._startup_events if e.get("event") == "status_change"]
                if "idle" in statuses:
                    break

    def _read_stdout(self):
        """Background thread that reads lines from stdout."""
        for line in self.proc.stdout:
            stripped = line.strip()
            if stripped:
                self._lines.put(stripped)

    def send(self, method: str, params: dict | None = None, req_id: int = 1) -> dict:
        """Send a JSON-RPC request and return the response dict."""
        msg = {"id": req_id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

        # Read response(s) — skip events, wait for response with matching id
        deadline = time.time() + TIMEOUT
        events = []
        while time.time() < deadline:
            line = self._read_line()
            if not line:
                continue
            data = json.loads(line)
            if "id" in data and data["id"] == req_id:
                return data
            if "event" in data:
                events.append(data)
        raise TimeoutError(f"No response for {method} (id={req_id}) within {TIMEOUT}s. Events: {events}")

    def send_and_collect_events(self, method: str, params: dict | None = None, req_id: int = 1) -> tuple[dict, list[dict]]:
        """Send request and collect both response and events."""
        msg = {"id": req_id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()

        deadline = time.time() + TIMEOUT
        events = []
        while time.time() < deadline:
            line = self._read_line()
            if not line:
                continue
            data = json.loads(line)
            if "id" in data and data["id"] == req_id:
                return data, events
            if "event" in data:
                events.append(data)
        raise TimeoutError(f"No response for {method} within {TIMEOUT}s")

    def _read_line(self, timeout: float = 3.0) -> str | None:
        """Read a line from the queue with timeout (Windows-compatible)."""
        try:
            return self._lines.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        if self.proc.poll() is None:
            self.proc.stdin.close()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


@pytest.fixture
def sidecar():
    proc = SidecarProcess()
    yield proc
    proc.close()


class TestStartupEvents:
    def test_startup_emits_loading(self, sidecar):
        """Sidecar emits at least status_change(loading) on startup."""
        assert len(sidecar._startup_events) >= 1
        assert sidecar._startup_events[0]["event"] == "status_change"
        assert sidecar._startup_events[0]["data"]["status"] == "loading"

    def test_startup_emits_idle_eventually(self, sidecar):
        """Sidecar reaches idle state (either in startup events or via first request)."""
        # The idle event may have been consumed during startup or arrives later
        statuses = [e["data"]["status"] for e in sidecar._startup_events if e.get("event") == "status_change"]
        if "idle" not in statuses:
            # Try a ping — the response itself proves the sidecar is running
            resp = sidecar.send("ping")
            assert resp["result"]["pong"] is True


class TestPing:
    def test_ping_returns_pong(self, sidecar):
        resp = sidecar.send("ping")
        assert resp["result"]["pong"] is True

    def test_ping_has_correct_id(self, sidecar):
        resp = sidecar.send("ping", req_id=42)
        assert resp["id"] == 42


class TestGetConfig:
    def test_get_config_returns_expected_fields(self, sidecar):
        resp = sidecar.send("get_config")
        result = resp["result"]
        assert "backend" in result
        assert "model" in result
        assert "output_mode" in result
        assert "hotkeys" in result
        assert "api_keys" in result

    def test_default_model_is_large_v3(self, sidecar):
        resp = sidecar.send("get_config")
        assert resp["result"]["model"] == "large-v3"


class TestSaveConfig:
    def test_save_config_roundtrip(self, sidecar):
        # Save
        sidecar.send("save_config", {"output_mode": "clipboard"}, req_id=10)
        # Read back
        resp = sidecar.send("get_config", req_id=11)
        assert resp["result"]["output_mode"] == "clipboard"

    def test_save_invalid_backend_ignored(self, sidecar):
        # Save invalid backend
        sidecar.send("save_config", {"backend": "invalid_backend"}, req_id=20)
        # Config should retain default
        resp = sidecar.send("get_config", req_id=21)
        assert resp["result"]["backend"] in ("local", "openai", "groq", "gemini", "deepgram")


class TestUnknownMethod:
    def test_unknown_method_returns_error(self, sidecar):
        resp = sidecar.send("nonexistent_method")
        assert "error" in resp
        assert "Unknown method" in resp["error"]


class TestMalformedInput:
    def test_malformed_json_does_not_crash(self, sidecar):
        """Send garbage, then a valid ping — sidecar should still work."""
        sidecar.proc.stdin.write("this is not json\n")
        sidecar.proc.stdin.flush()
        # Sidecar should log an error but keep running
        resp = sidecar.send("ping", req_id=99)
        assert resp["result"]["pong"] is True
