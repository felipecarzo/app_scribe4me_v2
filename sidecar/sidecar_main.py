"""Scribe4me Sidecar — Backend Python para o Tauri.

Protocolo: JSON-RPC sobre stdin/stdout (JSON lines).
Cada linha e uma mensagem JSON completa.

Request:  {"id": 1, "method": "transcribe", "params": {...}}
Response: {"id": 1, "result": {...}}
Event:    {"event": "status_change", "data": {"status": "recording"}}
"""

import json
import sys
import logging
from typing import Any

logger = logging.getLogger("scribe4me-sidecar")


def send_response(req_id: int, result: Any = None, error: str | None = None) -> None:
    """Envia resposta para o Tauri via stdout."""
    msg: dict[str, Any] = {"id": req_id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def send_event(event: str, data: dict[str, Any] | None = None) -> None:
    """Envia evento nao-solicitado para o Tauri via stdout."""
    msg = {"event": event, "data": data or {}}
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def handle_request(req_id: int, method: str, params: dict[str, Any]) -> None:
    """Despacha um request JSON-RPC para o handler correto."""
    try:
        if method == "ping":
            send_response(req_id, {"pong": True})

        elif method == "get_config":
            # TODO: Fase 2 — ler config real do disco
            send_response(req_id, {
                "backend": "local",
                "model": "large-v3",
                "output_mode": "cursor",
                "realtime": False,
            })

        elif method == "save_config":
            # TODO: Fase 2 — persistir config
            logger.info("save_config: %s", params)
            send_response(req_id, {"ok": True})

        elif method == "get_hardware":
            # TODO: Fase 2 — importar hardware.py real
            send_response(req_id, {
                "has_cuda": False,
                "vram_gb": 0,
                "ram_gb": 16,
                "recommended_model": "large-v3",
            })

        elif method == "start_recording":
            send_event("status_change", {"status": "recording", "text": "Gravando..."})
            # TODO: Fase 3 — iniciar recorder.py
            send_response(req_id, {"ok": True})

        elif method == "stop_recording":
            send_event("status_change", {"status": "transcribing", "text": "Transcrevendo..."})
            # TODO: Fase 3 — parar gravacao e transcrever
            send_response(req_id, {"ok": True})

        elif method == "cancel_recording":
            send_event("status_change", {"status": "idle", "text": "Cancelado"})
            send_response(req_id, {"ok": True})

        else:
            send_response(req_id, error=f"Unknown method: {method}")

    except Exception as e:
        logger.exception("Error handling %s", method)
        send_response(req_id, error=str(e))


def main() -> None:
    """Loop principal — le JSON lines de stdin e despacha."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,  # logs vao pra stderr, protocolo vai pra stdout
    )
    logger.info("Scribe4me sidecar starting...")
    send_event("status_change", {"status": "loading", "text": "Backend iniciando..."})

    # TODO: Fase 2 — carregar config, inicializar hardware detection
    send_event("status_change", {"status": "idle", "text": "Pronto"})

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            handle_request(msg["id"], msg["method"], msg.get("params", {}))
        except json.JSONDecodeError:
            logger.error("Invalid JSON: %s", line)
        except KeyError as e:
            logger.error("Missing field %s in: %s", e, line)


if __name__ == "__main__":
    main()
