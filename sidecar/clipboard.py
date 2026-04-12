"""Envio do texto transcrito para clipboard.

Nota v2: A simulacao de Ctrl+V (paste at cursor) foi movida para o lado Rust/Tauri.
O sidecar apenas copia para o clipboard via pyperclip e emite um evento
'paste_ready' para que o Tauri faca a simulacao de tecla.
"""

import logging

import pyperclip

logger = logging.getLogger("scribe4me.clipboard")


class OutputHandler:
    """Envia texto transcrito para o clipboard."""

    def __init__(self):
        self._last_text: str = ""

    @property
    def last_text(self) -> str:
        return self._last_text

    def copy_to_clipboard(self, text: str) -> None:
        """Copia texto para o clipboard do sistema."""
        if not text:
            return
        self._last_text = text
        pyperclip.copy(text)
        logger.info("Copiado para clipboard (%d chars)", len(text))

    def prepare_paste(self, text: str) -> bool:
        """Copia texto para clipboard e retorna True se pronto para paste.

        O caller (sidecar_main) deve emitir evento 'paste_ready' para que
        o Tauri simule Ctrl+V no lado Rust.
        """
        if not text:
            return False
        self.copy_to_clipboard(text)
        return True
