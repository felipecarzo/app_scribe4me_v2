"""Smoke test para o binario compilado do sidecar (T6-08).

Executa o binario PyInstaller compilado e verifica que:
1. Inicia sem crash
2. Emite evento status_change loading
3. Emite evento status_change idle (pronto para receber requests)
4. Responde corretamente ao metodo ping

Pre-requisito: rodar build_sidecar.bat antes de executar estes testes.

Uso:
    cd sidecar
    python -m pytest tests/test_smoke_binary.py -v

Skip automatico se o binario nao existir (CI sem build step).
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Caminho esperado do binario compilado (relativo a sidecar/)
_SIDECAR_DIR = Path(__file__).parent.parent
_BINARY = _SIDECAR_DIR / "dist" / "scribe4me-sidecar" / "scribe4me-sidecar.exe"

# Em Linux/macOS o executavel nao tem extensao .exe
if sys.platform != "win32":
    _BINARY = _SIDECAR_DIR / "dist" / "scribe4me-sidecar" / "scribe4me-sidecar"


def _binary_available() -> bool:
    return _BINARY.exists()


skip_no_binary = pytest.mark.skipif(
    not _binary_available(),
    reason=f"Binario compilado nao encontrado: {_BINARY}. Execute build_sidecar.bat primeiro.",
)


class BinaryProcess:
    """Gerencia o processo do binario compilado para testes."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self._proc: subprocess.Popen | None = None
        self._events: list[dict] = []
        self._responses: list[dict] = []

    def start(self) -> None:
        self._proc = subprocess.Popen(
            [str(_BINARY)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )

    def _read_until_idle(self) -> bool:
        """Le stdout ate receber status_change idle ou timeout."""
        assert self._proc is not None
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if "event" in msg:
                    self._events.append(msg)
                    if msg.get("event") == "status_change":
                        status = msg.get("data", {}).get("status", "")
                        if status == "idle":
                            return True
                elif "id" in msg:
                    self._responses.append(msg)
            except json.JSONDecodeError:
                pass  # linhas de log nao-JSON (stderr redirecionado)
        return False

    def send(self, req: dict) -> dict | None:
        """Envia um request JSON-RPC e aguarda a resposta."""
        assert self._proc is not None
        req_id = req["id"]
        self._proc.stdin.write(json.dumps(req) + "\n")
        self._proc.stdin.flush()

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
                if "id" in msg and msg["id"] == req_id:
                    return msg
                if "event" in msg:
                    self._events.append(msg)
            except json.JSONDecodeError:
                pass
        return None

    def stop(self) -> None:
        if self._proc:
            try:
                self._proc.stdin.close()
            except OSError:
                pass
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def get_events_by_status(self, status: str) -> list[dict]:
        return [e for e in self._events if e.get("data", {}).get("status") == status]


@pytest.fixture
def binary_proc():
    proc = BinaryProcess()
    proc.start()
    yield proc
    proc.stop()


@skip_no_binary
class TestBinarySmoke:
    def test_binary_exists(self):
        """Binario esta presente em dist/."""
        assert _BINARY.exists(), f"Binario nao encontrado: {_BINARY}"
        assert _BINARY.stat().st_size > 0, "Binario esta vazio"

    def test_startup_emits_loading(self, binary_proc):
        """Sidecar emite status_change loading ao iniciar."""
        reached_idle = binary_proc._read_until_idle()
        loading_events = binary_proc.get_events_by_status("loading")
        assert len(loading_events) >= 1, (
            f"Esperado ao menos 1 evento loading, recebidos: {binary_proc._events}"
        )

    def test_startup_reaches_idle(self, binary_proc):
        """Sidecar atinge status idle dentro do timeout."""
        reached_idle = binary_proc._read_until_idle()
        assert reached_idle, (
            f"Sidecar nao atingiu idle em {binary_proc.timeout}s. "
            f"Eventos recebidos: {binary_proc._events}"
        )

    def test_ping_responds(self, binary_proc):
        """Sidecar responde ao metodo ping com pong=True."""
        binary_proc._read_until_idle()
        resp = binary_proc.send({"id": 1, "method": "ping", "params": {}})
        assert resp is not None, "Nenhuma resposta recebida para ping"
        assert "error" not in resp, f"Ping retornou erro: {resp.get('error')}"
        assert resp.get("result", {}).get("pong") is True, (
            f"Resposta inesperada: {resp}"
        )

    def test_get_config_responds(self, binary_proc):
        """get_config retorna estrutura valida."""
        binary_proc._read_until_idle()
        resp = binary_proc.send({"id": 2, "method": "get_config", "params": {}})
        assert resp is not None, "Nenhuma resposta recebida para get_config"
        assert "error" not in resp, f"get_config retornou erro: {resp.get('error')}"
        result = resp.get("result", {})
        assert "backend" in result, f"Campo 'backend' ausente: {result}"
        assert "model" in result, f"Campo 'model' ausente: {result}"
        assert "theme" in result, f"Campo 'theme' ausente: {result}"

    def test_unknown_method_returns_error(self, binary_proc):
        """Metodo desconhecido retorna error, nao crasha."""
        binary_proc._read_until_idle()
        resp = binary_proc.send({"id": 99, "method": "metodo_inexistente", "params": {}})
        assert resp is not None, "Nenhuma resposta para metodo desconhecido"
        assert "error" in resp, f"Esperado campo error, recebido: {resp}"
        assert "Unknown method" in resp["error"], f"Mensagem inesperada: {resp['error']}"
