"""
transcriber.py — Local Whisper transcription (CPU or CUDA).

Loads the model once at startup and reuses it for every transcription.
Supports hot-swapping the model at runtime via change_model().
"""

import threading
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

from settings import MODELS_DIR


# Whisper expects float32 audio normalised to [-1, 1] at 16 kHz
SAMPLE_RATE = 16_000


class Transcriber:
    """
    Wraps openai-whisper for synchronous transcription.

    Parameters
    ----------
    model_name : str
        One of 'tiny', 'base', 'small', 'medium', 'large-v3'.
    language : str
        'auto' for auto-detect, or a language code like 'en', 'hi'.
    on_progress : callable | None
        Optional callback(fraction: float) called during model download.
    """

    def __init__(
        self,
        model_name: str = "base",
        language: str = "auto",
        on_progress=None,
    ) -> None:
        self._model_name = model_name
        self._language = language
        self._on_progress = on_progress
        self._lock = threading.Lock()
        self._model = None

        self._load_model(model_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe a 1-D float32 numpy array captured at 16 kHz.

        Returns the stripped transcription string, or '' on empty audio.
        """
        if audio is None or len(audio) == 0:
            return ""

        # Whisper needs float32 in [-1, 1]
        audio = audio.astype(np.float32)

        lang = None if self._language == "auto" else self._language

        with self._lock:
            # faster-whisper returns a generator of segments
            segments, info = self._model.transcribe(
                audio,
                language=lang,
                beam_size=5,
                vad_filter=True, # Recommended for faster-whisper
            )
            
            # Iterate through generator to perform actual transcription
            text = "".join(segment.text for segment in segments)

        return text.strip()

    def change_model(self, model_name: str) -> None:
        """Hot-swap the Whisper model (blocks until new model is loaded)."""
        if model_name == self._model_name:
            return
        self._load_model(model_name)
        self._model_name = model_name

    def set_language(self, language: str) -> None:
        self._language = language

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def language(self) -> str:
        return self._language

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load_model(self, model_name: str) -> None:
        """Load (or download) a Whisper model into memory."""
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        
        print(f"[transcriber] Loading model '{model_name}' on {device} …")
        with self._lock:
            self._model = WhisperModel(
                model_name,
                device=device,
                compute_type=compute_type,
                download_root=str(MODELS_DIR)
            )
        print(f"[transcriber] Model '{model_name}' ready on {device}.")

    def _is_cuda(self) -> bool:
        """True if the loaded model is on a CUDA device."""
        import torch
        return torch.cuda.is_available()
