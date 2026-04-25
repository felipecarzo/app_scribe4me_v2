"""Configuracoes do Scribe4me v2 — sidecar."""

import json
import os
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "Scribe4me"


def _get_config_dir() -> Path:
    """Retorna diretorio de config cross-platform (sem depender de src.platform)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", "."))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / APP_NAME


APP_DATA_DIR = _get_config_dir()
_CONFIG_FILE = APP_DATA_DIR / "config.json"
_config_lock = threading.Lock()

DEFAULT_HOTKEYS = {
    "push_to_talk": "Ctrl+Alt+H",
    "toggle": "Ctrl+Alt+T",
    "cancel": "Ctrl+Alt+C",
    "quit": "Ctrl+Q",
}

SUPPORTED_API_BACKENDS = ["local", "openai", "groq", "gemini", "deepgram"]


def _load_config_data() -> dict:
    """Carrega o config.json inteiro como dict."""
    try:
        if _CONFIG_FILE.exists():
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _save_config_data(data: dict) -> None:
    """Salva o dict inteiro no config.json (thread-safe, atomic write)."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _CONFIG_FILE.with_suffix(".tmp")
    with _config_lock:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(_CONFIG_FILE)


def load_custom_prompt() -> str:
    """Carrega o prompt personalizado salvo, ou retorna string vazia."""
    return _load_config_data().get("custom_prompt", "")


def save_custom_prompt(prompt: str) -> None:
    """Salva o prompt personalizado no config.json."""
    data = _load_config_data()
    data["custom_prompt"] = prompt
    _save_config_data(data)


def load_hotkeys() -> dict[str, str]:
    """Carrega hotkeys do config.json, preenchendo com defaults."""
    saved = _load_config_data().get("hotkeys", {})
    result = dict(DEFAULT_HOTKEYS)
    for key in DEFAULT_HOTKEYS:
        if key in saved and saved[key]:
            result[key] = saved[key]
    return result


def save_hotkeys(hotkeys: dict[str, str]) -> None:
    """Salva hotkeys no config.json."""
    data = _load_config_data()
    data["hotkeys"] = hotkeys
    _save_config_data(data)


def load_output_mode() -> str:
    """Carrega modo de saida do config.json (cursor ou clipboard)."""
    return _load_config_data().get("output_mode", "cursor")


def save_output_mode(mode: str) -> None:
    """Salva modo de saida no config.json."""
    data = _load_config_data()
    data["output_mode"] = mode
    _save_config_data(data)


def load_api_keys() -> dict[str, str]:
    """Carrega as API keys salvas (dict backend -> key)."""
    return _load_config_data().get("api_keys", {})


def save_api_keys(keys: dict[str, str]) -> None:
    """Salva as API keys no config.json."""
    data = _load_config_data()
    data["api_keys"] = keys
    _save_config_data(data)


def load_api_config() -> dict:
    """Carrega configuracao de API (backend selecionado, realtime)."""
    defaults = {"backend": "local", "realtime": False}
    saved = _load_config_data().get("api_config", {})
    return {**defaults, **saved}


def save_api_config(cfg: dict) -> None:
    """Salva configuracao de API no config.json."""
    data = _load_config_data()
    data["api_config"] = cfg
    _save_config_data(data)


def is_first_run() -> bool:
    """Retorna True se o config.json nao existe ou tem first_run=True."""
    data = _load_config_data()
    if not data:
        return True
    return bool(data.get("first_run", False))


def mark_first_run_done() -> None:
    """Marca first_run como False no config.json."""
    data = _load_config_data()
    data["first_run"] = False
    _save_config_data(data)


def load_active_profile() -> str:
    """Retorna nome do profile ativo (default: Tech-Dev)."""
    return _load_config_data().get("active_profile", "Tech-Dev")


def save_active_profile(name: str) -> None:
    """Salva nome do profile ativo no config.json."""
    data = _load_config_data()
    data["active_profile"] = name
    _save_config_data(data)


@dataclass
class Config:
    """Config runtime do sidecar — sem hotkeys (gerenciados pelo Tauri)."""
    # Whisper
    model: str = "large-v3"
    language: str = "pt"
    device: str = "cuda"

    # API transcription
    api_backend: str = field(default_factory=lambda: load_api_config()["backend"])
    api_realtime: bool = field(default_factory=lambda: load_api_config()["realtime"])

    # Saida
    output_mode: str = field(default_factory=load_output_mode)

    # Audio
    sample_rate: int = 16000
    channels: int = 1
