"""Captura de audio do microfone."""

import logging
import threading
from typing import Callable

logger = logging.getLogger("scribe4me.recorder")

import numpy as np
import sounddevice as sd


class Recorder:
    """Grava audio do microfone em chunks, acumula em buffer numpy."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self._sample_rate = sample_rate
        self._channels = channels
        self._buffer: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._recording = False
        self.chunk_callback: Callable[[np.ndarray], None] | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> None:
        """Inicia gravacao do microfone."""
        if self._recording:
            return

        self._buffer.clear()
        self._stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=self._channels,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        self._recording = True

    def stop(self) -> np.ndarray:
        """Para gravacao e retorna audio como numpy array (float32, mono, 16kHz).

        Retorna array vazio se nao estava gravando.
        """
        if not self._recording:
            return np.array([], dtype=np.float32)

        self._recording = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._buffer:
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self._buffer, axis=0).flatten()
            self._buffer.clear()

        return audio

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info, status
    ) -> None:
        """Callback do sounddevice — acumula chunks no buffer e notifica streaming."""
        if status:
            logger.warning("sounddevice: %s", status)
        chunk = indata.copy()
        with self._lock:
            self._buffer.append(chunk)
        if self.chunk_callback is not None:
            self.chunk_callback(chunk.flatten())
