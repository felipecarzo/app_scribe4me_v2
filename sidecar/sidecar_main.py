"""Scribe4me Sidecar — Backend Python para o Tauri.

Protocolo: JSON-RPC sobre stdin/stdout (JSON lines).
Cada linha e uma mensagem JSON completa.

Request:  {"id": 1, "method": "transcribe", "params": {...}}
Response: {"id": 1, "result": {...}}
Event:    {"event": "status_change", "data": {"status": "recording"}}
"""

import json
import logging
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any

from config import (
    SUPPORTED_API_BACKENDS,
    Config,
    is_first_run,
    load_active_profile,
    load_api_config,
    load_api_keys,
    load_custom_prompt,
    load_hotkeys,
    load_output_mode,
    mark_first_run_done,
    save_active_profile,
    save_api_config,
    save_api_keys,
    save_custom_prompt,
    save_hotkeys,
    save_output_mode,
    _load_config_data,
    _save_config_data,
)
from clipboard import OutputHandler
from hardware import detect_hardware, recommend_model
from profiles import (
    Profile,
    delete_profile as _delete_profile,
    get_profile_by_name,
    get_default_profile,
    list_profiles,
    save_profile as _save_profile,
)
from recorder import Recorder
from transcriber import Transcriber
from transcriber_api import create_api_transcriber
from voice_commands import VoiceCommandEngine

logger = logging.getLogger("scribe4me-sidecar")

# --- Globais do sidecar ---
_config: Config | None = None
_recorder: Recorder | None = None
_transcriber: Transcriber | None = None
_output: OutputHandler | None = None
_realtime_manager = None  # DeepgramRealtimeManager (lazy import)
_active_profile: Profile | None = None
_voice_engine: VoiceCommandEngine | None = None
_stdout_lock = threading.Lock()
_state_lock = threading.Lock()  # protege acesso a _config, _recorder, _transcriber, _realtime_manager


def send_response(req_id: int, result: Any = None, error: str | None = None) -> None:
    """Envia resposta para o Tauri via stdout (thread-safe)."""
    msg: dict[str, Any] = {"id": req_id}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    with _stdout_lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def send_event(event: str, data: dict[str, Any] | None = None) -> None:
    """Envia evento nao-solicitado para o Tauri via stdout (thread-safe)."""
    msg = {"event": event, "data": data or {}}
    with _stdout_lock:
        sys.stdout.write(json.dumps(msg) + "\n")
        sys.stdout.flush()


def _run_in_thread(fn, *args, **kwargs) -> threading.Thread:
    """Executa funcao em thread daemon (para operacoes longas)."""
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


# --- Handlers JSON-RPC ---


def _handle_ping(req_id: int, params: dict) -> None:
    send_response(req_id, {"pong": True})


def _handle_get_config(req_id: int, params: dict) -> None:
    api_cfg = load_api_config()
    raw = _load_config_data()
    profile = _active_profile or get_default_profile()
    send_response(req_id, {
        "backend": api_cfg["backend"],
        "model": _config.model if _config else "large-v3",
        "language": _config.language if _config else "pt",
        "output_mode": load_output_mode(),
        "realtime": api_cfg["realtime"],
        "hotkeys": load_hotkeys(),
        "api_keys": load_api_keys(),
        "custom_prompt": load_custom_prompt(),
        "theme": raw.get("theme", "system"),
        "first_run": is_first_run(),
        "active_profile": profile.name,
        "code_mode": profile.code_mode,
    })


def _handle_save_config(req_id: int, params: dict) -> None:
    global _config
    with _state_lock:
        _handle_save_config_inner(params)
    send_response(req_id, {"ok": True})


def _handle_save_config_inner(params: dict) -> None:
    """Aplica mudancas de config (chamado dentro de _state_lock)."""
    global _config
    if "output_mode" in params:
        save_output_mode(params["output_mode"])
        if _config:
            _config.output_mode = params["output_mode"]
    if "hotkeys" in params:
        save_hotkeys(params["hotkeys"])
    if "api_keys" in params:
        save_api_keys(params["api_keys"])
    if "custom_prompt" in params:
        save_custom_prompt(params["custom_prompt"])
        if _transcriber:
            _transcriber.set_custom_prompt(params["custom_prompt"])
    if "backend" in params or "realtime" in params:
        api_cfg = load_api_config()
        if "backend" in params:
            if params["backend"] not in SUPPORTED_API_BACKENDS:
                return  # ignora backend invalido
            api_cfg["backend"] = params["backend"]
            if _config:
                _config.api_backend = params["backend"]
        if "realtime" in params:
            api_cfg["realtime"] = params["realtime"]
            if _config:
                _config.api_realtime = params["realtime"]
        save_api_config(api_cfg)
    if "model" in params and _config:
        _config.model = params["model"]
    if "language" in params and _config:
        _config.language = params["language"]
    if "theme" in params:
        data = _load_config_data()
        data["theme"] = params["theme"]
        _save_config_data(data)
    if params.get("first_run") is False:
        mark_first_run_done()


def _handle_get_hardware(req_id: int, params: dict) -> None:
    hw = detect_hardware()
    rec = recommend_model(hw)
    send_response(req_id, {
        "has_cuda": hw.cuda_available,
        "vram_gb": round(hw.gpu_vram_mb / 1024, 1),
        "ram_gb": round(hw.ram_mb / 1024, 1),
        "gpu_name": hw.gpu_name,
        "cpu_cores": hw.cpu_cores,
        "recommended_model": rec,
    })


def _handle_load_model(req_id: int, params: dict) -> None:
    """Carrega modelo Whisper em background thread."""
    model_name = params.get("model", _config.model if _config else "large-v3")

    def _do_load():
        global _transcriber
        send_event("status_change", {"status": "loading", "text": f"Carregando {model_name}..."})
        load_t0 = time.monotonic()
        try:
            with _state_lock:
                if _transcriber is None:
                    _transcriber = Transcriber(
                        model=model_name,
                        language=_config.language if _config else "pt",
                        device=_config.device if _config else "cuda",
                    )
                if model_name != _transcriber._model_name:
                    _transcriber.reload_model(model_name)
                else:
                    _transcriber.load_model()
                    _transcriber.warm_up()
            load_ms = int((time.monotonic() - load_t0) * 1000)
            logger.info("Model '%s' loaded in %d ms (device=%s)", model_name, load_ms, _transcriber.device)
            send_event("status_change", {"status": "idle", "text": "Pronto"})
            send_response(req_id, {"ok": True, "device": _transcriber.device, "load_ms": load_ms})
        except Exception as e:
            logger.exception("Erro ao carregar modelo")
            send_event("status_change", {"status": "error", "text": str(e)})
            send_response(req_id, error=str(e))

    _run_in_thread(_do_load)


def _handle_start_recording(req_id: int, params: dict) -> None:
    global _recorder, _realtime_manager
    with _state_lock:
        if _recorder and _recorder.is_recording:
            send_response(req_id, error="Ja esta gravando")
            return

        _recorder = Recorder(
            sample_rate=_config.sample_rate if _config else 16000,
            channels=_config.channels if _config else 1,
        )

        # Se realtime esta habilitado, conectar chunk_callback ao Deepgram
        if _config and _config.api_realtime and _config.api_backend == "deepgram":
            api_keys = load_api_keys()
            dg_key = api_keys.get("deepgram", "")
            if dg_key:
                from realtime_manager import DeepgramRealtimeManager
                _realtime_manager = DeepgramRealtimeManager(
                    api_key=dg_key,
                    language="pt-BR" if _config.language.startswith("pt") else _config.language,
                    on_partial=lambda t: send_event("realtime_text", {"text": t, "is_final": False}),
                    on_final=lambda t: send_event("realtime_text", {"text": t, "is_final": True}),
                    on_fragment=lambda t: send_event("realtime_fragment", {"text": t}),
                )
                if _realtime_manager.start():
                    _recorder.chunk_callback = _realtime_manager.send_chunk
                else:
                    logger.warning("Falha ao conectar Deepgram realtime, gravando sem streaming")
                    _realtime_manager = None

        _recorder.start()
    send_event("status_change", {"status": "recording", "text": "Gravando..."})
    send_response(req_id, {"ok": True})


def _handle_stop_recording(req_id: int, params: dict) -> None:
    """Para gravacao e transcreve em background thread."""
    global _recorder, _realtime_manager

    with _state_lock:
        if not _recorder or not _recorder.is_recording:
            send_response(req_id, error="Nao esta gravando")
            return

        audio = _recorder.stop()

        # Se realtime, pegar texto do manager
        if _realtime_manager is not None:
            realtime_text = _realtime_manager.stop()
            _realtime_manager = None
            if realtime_text:
                _output_text(req_id, realtime_text)
                return

    if len(audio) == 0:
        send_event("status_change", {"status": "idle", "text": "Pronto"})
        send_response(req_id, {"text": "", "ok": True})
        return

    def _do_transcribe():
        send_event("status_change", {"status": "transcribing", "text": "Transcrevendo..."})
        try:
            text = _transcribe_audio(audio)
            _output_text(req_id, text)
        except Exception as e:
            logger.exception("Erro na transcricao")
            send_event("status_change", {"status": "error", "text": str(e)})
            send_response(req_id, error=str(e))

    _run_in_thread(_do_transcribe)


def _transcribe_audio(audio) -> str:
    """Transcreve audio usando backend configurado (local ou API)."""
    if _config and _config.api_backend != "local":
        api_keys = load_api_keys()
        api_transcriber = create_api_transcriber(
            _config.api_backend, api_keys, _config.language
        )
        if api_transcriber:
            return api_transcriber.transcribe(audio, _config.sample_rate)

    # Fallback: Whisper local
    global _transcriber
    if _transcriber is None:
        _transcriber = Transcriber(
            model=_config.model if _config else "large-v3",
            language=_config.language if _config else "pt",
            device=_config.device if _config else "cuda",
        )
        _transcriber.load_model()
        _transcriber.warm_up()
    return _transcriber.transcribe(audio)


def _apply_voice_commands(text: str) -> tuple[str, list[str]]:
    """Aplica voice commands se code_mode ativo. Retorna (texto_final, keypresses)."""
    if not _active_profile or not _active_profile.code_mode or not _voice_engine:
        return text, []

    results = _voice_engine.process(text)
    text_parts = []
    keypresses = []
    for r in results:
        if r.keypress:
            keypresses.append(r.keypress)
        elif r.text:
            text_parts.append(r.text)

    return "".join(text_parts), keypresses


def _output_text(req_id: int, text: str) -> None:
    """Envia texto transcrito para clipboard/cursor e responde."""
    processed_text, keypresses = _apply_voice_commands(text)

    if _output and _config:
        if keypresses:
            send_event("voice_keypresses", {"keys": keypresses})
        if processed_text:
            if _config.output_mode == "cursor":
                if _output.prepare_paste(processed_text):
                    send_event("paste_ready", {"text": processed_text})
            else:
                _output.copy_to_clipboard(processed_text)

    send_event("status_change", {"status": "idle", "text": "Pronto"})
    send_response(req_id, {"text": processed_text, "ok": True, "original_text": text})


def _handle_cancel_recording(req_id: int, params: dict) -> None:
    global _recorder, _realtime_manager
    with _state_lock:
        if _recorder and _recorder.is_recording:
            _recorder.stop()
        if _realtime_manager is not None:
            _realtime_manager.stop()
            _realtime_manager = None
    send_event("status_change", {"status": "idle", "text": "Cancelado"})
    send_response(req_id, {"ok": True})


def _handle_copy_to_clipboard(req_id: int, params: dict) -> None:
    text = params.get("text", "")
    if _output:
        _output.copy_to_clipboard(text)
    send_response(req_id, {"ok": True})


# Validation endpoints per provider (minimal request to confirm key works)
_API_TEST_ENDPOINTS: dict[str, tuple[str, str, str]] = {
    # provider: (url, header_name, header_value_template)
    "openai":   ("https://api.openai.com/v1/models",         "Authorization", "Bearer {key}"),
    "groq":     ("https://api.groq.com/openai/v1/models",    "Authorization", "Bearer {key}"),
    "deepgram": ("https://api.deepgram.com/v1/projects",     "Authorization", "Token {key}"),
    "gemini":   ("https://generativelanguage.googleapis.com/v1beta/models?key={key}", "", ""),
}


def _handle_test_api_key(req_id: int, params: dict) -> None:
    """Valida uma API key fazendo uma requisicao minima ao provider (em thread)."""
    provider = params.get("provider", "")
    key = params.get("key", "")

    def _do_test():
        if provider not in _API_TEST_ENDPOINTS or not key:
            send_response(req_id, error="Provider desconhecido ou chave vazia")
            return

        url_tpl, header_name, header_val_tpl = _API_TEST_ENDPOINTS[provider]
        url = url_tpl.replace("{key}", key)
        header_val = header_val_tpl.replace("{key}", key)

        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Scribe4me/2.0")
        if header_name:
            req.add_header(header_name, header_val)

        try:
            # NOTE: nao logar `url` — Gemini embute a key no query string
            t0 = time.monotonic()
            with urllib.request.urlopen(req, timeout=5) as resp:
                latency_ms = int((time.monotonic() - t0) * 1000)
                # Any 2xx means key is valid
                if resp.status < 300:
                    send_response(req_id, {"ok": True, "latency_ms": latency_ms})
                else:
                    send_response(req_id, error=f"HTTP {resp.status}")
        except urllib.error.HTTPError as e:
            # 401/403 = invalid key; 429 = valid key but rate-limited
            if e.code == 429:
                send_response(req_id, {"ok": True, "latency_ms": 0})
            else:
                send_response(req_id, error=f"Chave invalida (HTTP {e.code})")
        except Exception as e:
            send_response(req_id, error=str(e))

    _run_in_thread(_do_test)


# --- Handlers de Profiles ---


def _handle_list_profiles(req_id: int, params: dict) -> None:
    profiles = list_profiles()
    send_response(req_id, {
        "profiles": [
            {"name": p.name, "prompt": p.prompt, "code_mode": p.code_mode, "builtin": p.builtin}
            for p in profiles
        ]
    })


def _handle_get_active_profile(req_id: int, params: dict) -> None:
    profile = _active_profile or get_default_profile()
    send_response(req_id, {
        "name": profile.name,
        "prompt": profile.prompt,
        "code_mode": profile.code_mode,
        "builtin": profile.builtin,
    })


def _handle_set_active_profile(req_id: int, params: dict) -> None:
    global _active_profile
    name = params.get("name", "")
    profile = get_profile_by_name(name)
    if not profile:
        send_response(req_id, error=f"Profile nao encontrado: {name}")
        return
    with _state_lock:
        _active_profile = profile
    save_active_profile(name)
    logger.info("Profile ativo: %s (code_mode=%s)", name, profile.code_mode)
    send_response(req_id, {"ok": True, "name": profile.name, "code_mode": profile.code_mode})
    send_event("profile_changed", {"name": profile.name, "code_mode": profile.code_mode})


def _handle_save_profile(req_id: int, params: dict) -> None:
    global _active_profile
    name = params.get("name", "").strip()
    prompt = params.get("prompt", "").strip()
    code_mode = bool(params.get("code_mode", False))

    if not name:
        send_response(req_id, error="Nome do profile nao pode ser vazio")
        return
    if not prompt:
        send_response(req_id, error="Prompt nao pode ser vazio")
        return

    profile = _save_profile(name, prompt, code_mode)
    send_response(req_id, {"ok": True, "name": profile.name})


def _handle_delete_profile(req_id: int, params: dict) -> None:
    global _active_profile
    name = params.get("name", "")
    ok = _delete_profile(name)
    if not ok:
        send_response(req_id, error=f"Nao foi possivel deletar '{name}' (builtin ou nao existe)")
        return
    # Se era o profile ativo, volta para o default
    if _active_profile and _active_profile.name == name:
        with _state_lock:
            _active_profile = get_default_profile()
        save_active_profile(_active_profile.name)
    send_response(req_id, {"ok": True})


# --- Dispatch table ---

_HANDLERS = {
    "ping": _handle_ping,
    "get_config": _handle_get_config,
    "save_config": _handle_save_config,
    "get_hardware": _handle_get_hardware,
    "load_model": _handle_load_model,
    "start_recording": _handle_start_recording,
    "stop_recording": _handle_stop_recording,
    "cancel_recording": _handle_cancel_recording,
    "copy_to_clipboard": _handle_copy_to_clipboard,
    "test_api_key": _handle_test_api_key,
    "list_profiles": _handle_list_profiles,
    "get_active_profile": _handle_get_active_profile,
    "set_active_profile": _handle_set_active_profile,
    "save_profile": _handle_save_profile,
    "delete_profile": _handle_delete_profile,
}


def handle_request(req_id: int, method: str, params: dict[str, Any]) -> None:
    """Despacha um request JSON-RPC para o handler correto."""
    handler = _HANDLERS.get(method)
    if handler:
        try:
            handler(req_id, params)
        except Exception as e:
            logger.exception("Error handling %s", method)
            send_response(req_id, error=str(e))
    else:
        send_response(req_id, error=f"Unknown method: {method}")


def main() -> None:
    """Loop principal — le JSON lines de stdin e despacha."""
    global _config, _output

    _startup_t0 = time.monotonic()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    logger.info("Scribe4me sidecar starting...")
    send_event("status_change", {"status": "loading", "text": "Backend iniciando..."})

    # Inicializar config e output handler
    _config = Config()
    _output = OutputHandler()

    # Inicializar profiles e voice engine
    global _active_profile, _voice_engine
    _active_profile = get_profile_by_name(load_active_profile()) or get_default_profile()
    _voice_engine = VoiceCommandEngine()

    logger.info(
        "Config: backend=%s, model=%s, device=%s, output=%s, profile=%s (code_mode=%s)",
        _config.api_backend, _config.model, _config.device, _config.output_mode,
        _active_profile.name, _active_profile.code_mode,
    )

    startup_ms = int((time.monotonic() - _startup_t0) * 1000)
    logger.info("Sidecar ready in %d ms", startup_ms)

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
