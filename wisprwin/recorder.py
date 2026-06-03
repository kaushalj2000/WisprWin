"""
recorder.py — Microphone capture using sounddevice.

Always uses the Windows default input device (whatever is selected in
Sound Settings → Input). Changing the default mic in Windows while
WisprWin is running takes effect on the next recording automatically,
because a fresh InputStream is opened on every hotkey press.
"""

import threading
import numpy as np
import sounddevice as sd


SAMPLE_RATE = 16_000   # Whisper native sample rate
CHANNELS = 1           # Mono
DTYPE = "float32"


class AudioDeviceError(Exception):
    """Raised when the default audio input device cannot be opened."""
    pass


class Recorder:
    """
    Thread-safe microphone recorder.

    Uses the Windows default input device — change it in:
      Settings → System → Sound → Input
    and it takes effect on the next recording with no restart needed.

    Call start() on hotkey press, stop() on hotkey release.
    stop() blocks briefly until the stream closes and returns
    the captured audio as a 1-D float32 numpy array at 16 kHz.
    """

    def __init__(self) -> None:
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._recording = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open the microphone stream and begin buffering audio."""
        if self._recording:
            return  # guard against double-press

        with self._lock:
            self._chunks = []
            self._recording = True

        # device=None  →  always uses Windows default input (Sound Mapper)
        # A fresh stream is created every press so mid-session device
        # changes (e.g. plugging in a headset) are picked up automatically.
        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                device=None,
                callback=self._audio_callback,
            )
            self._stream.start()
        except Exception as e:
            self._recording = False
            self._stream = None
            raise AudioDeviceError(f"Could not open microphone: {e}") from e

        try:
            dev_info = sd.query_devices(self._stream.device, 'input')
            print(f"[recorder] Recording from: {dev_info['name']}")
        except Exception:
            pass

    def stop(self) -> np.ndarray:
        """
        Stop recording and return the captured audio.

        Returns a 1-D float32 numpy array (or empty array if nothing captured).
        """
        if not self._recording:
            return np.array([], dtype=np.float32)

        self._recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            chunks = list(self._chunks)
            self._chunks = []

        if not chunks:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(chunks, axis=0)
        return audio.flatten()  # ensure 1-D

    @property
    def is_recording(self) -> bool:
        return self._recording

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time,
        status,
    ) -> None:
        """Called by sounddevice on each audio chunk (runs in SD thread)."""
        if status:
            print(f"[recorder] sounddevice status: {status}")
        if self._recording:
            with self._lock:
                self._chunks.append(indata.copy())
