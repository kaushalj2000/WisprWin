"""
system_recorder.py — Capture system audio via WASAPI loopback.

Uses PyAudioWPatch to record the audio output of the default
playback device (speakers/headphones).  This captures ALL system
audio — meetings, videos, music, etc. — without needing virtual
audio cables or special drivers.

The output is always a 1-D float32 numpy array at 16 kHz mono,
ready to feed directly into Whisper.
"""

import threading
import numpy as np


class SystemAudioError(Exception):
    """Raised when the WASAPI loopback device cannot be opened."""
    pass


class SystemRecorder:
    """
    Thread-safe system audio recorder using WASAPI loopback.

    Captures whatever audio is currently playing through the default
    Windows output device (speakers / headphones).

    Call start() to begin capturing system output.
    Call stop() to end capture and return audio as 16 kHz mono float32.
    """

    WHISPER_RATE = 16_000  # Whisper native sample rate

    def __init__(self) -> None:
        self._chunks: list[bytes] = []
        self._stream = None
        self._pyaudio = None
        self._lock = threading.Lock()
        self._recording = False
        self._sample_rate: int = 0       # native device rate (e.g. 48000)
        self._channels: int = 0          # native channel count
        self._sample_width: int = 0      # bytes per sample

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Open WASAPI loopback stream and begin buffering system audio."""
        if self._recording:
            return  # guard against double-press

        try:
            import pyaudiowpatch as pyaudio
        except ImportError:
            raise SystemAudioError(
                "PyAudioWPatch is not installed. "
                "Run: pip install PyAudioWPatch"
            )

        with self._lock:
            self._chunks = []
            self._recording = True

        try:
            self._pyaudio = pyaudio.PyAudio()

            # Find the default WASAPI loopback device
            wasapi_info = self._pyaudio.get_host_api_info_by_type(
                pyaudio.paWASAPI
            )
            default_speakers_idx = wasapi_info["defaultOutputDevice"]
            default_speakers = self._pyaudio.get_device_info_by_index(
                default_speakers_idx
            )

            # Get the loopback counterpart of the default speakers
            if not default_speakers.get("isLoopbackDevice"):
                # Find the loopback version of this device
                loopback = None
                for i in range(self._pyaudio.get_device_count()):
                    dev = self._pyaudio.get_device_info_by_index(i)
                    if (dev.get("isLoopbackDevice") and
                            dev["name"].startswith(default_speakers["name"])):
                        loopback = dev
                        break

                if loopback is None:
                    raise SystemAudioError(
                        f"Could not find loopback device for: "
                        f"{default_speakers['name']}"
                    )
            else:
                loopback = default_speakers

            self._sample_rate = int(loopback["defaultSampleRate"])
            self._channels = max(int(loopback["maxInputChannels"]), 1)
            self._sample_width = self._pyaudio.get_sample_size(pyaudio.paInt16)

            print(
                f"[sys_recorder] Capturing from: {loopback['name']} "
                f"({self._sample_rate} Hz, {self._channels} ch)"
            )

            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=int(loopback["index"]),
                frames_per_buffer=1024,
                stream_callback=self._audio_callback,
            )
            self._stream.start_stream()

        except SystemAudioError:
            self._cleanup()
            raise
        except Exception as e:
            self._cleanup()
            raise SystemAudioError(
                f"Could not open system audio loopback: {e}"
            ) from e

    def stop(self) -> np.ndarray:
        """
        Stop recording and return the captured system audio.

        Returns a 1-D float32 numpy array at 16 kHz mono,
        normalised to [-1, 1] — ready for Whisper.
        Returns an empty array if nothing was captured.
        """
        if not self._recording:
            return np.array([], dtype=np.float32)

        self._recording = False

        # Stop and close the stream
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        # Grab buffered chunks
        with self._lock:
            chunks = list(self._chunks)
            self._chunks = []

        # Terminate PyAudio instance
        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

        if not chunks:
            return np.array([], dtype=np.float32)

        # Decode raw bytes → int16 → float32 normalised
        raw = b"".join(chunks)
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        # Stereo → mono
        if self._channels > 1:
            audio = self._stereo_to_mono(audio, self._channels)

        # Resample to 16 kHz if needed
        if self._sample_rate != self.WHISPER_RATE:
            audio = self._resample_to_16k(audio, self._sample_rate)

        return audio

    @property
    def is_recording(self) -> bool:
        return self._recording

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _audio_callback(self, in_data, frame_count, time_info, status_flags):
        """PyAudio stream callback — buffer raw bytes."""
        import pyaudiowpatch as pyaudio
        if self._recording and in_data:
            with self._lock:
                self._chunks.append(in_data)
        return (None, pyaudio.paContinue)

    def _cleanup(self) -> None:
        """Clean up resources on error."""
        self._recording = False
        if self._stream is not None:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._pyaudio is not None:
            try:
                self._pyaudio.terminate()
            except Exception:
                pass
            self._pyaudio = None

    @staticmethod
    def _stereo_to_mono(audio: np.ndarray, channels: int) -> np.ndarray:
        """Downmix multi-channel interleaved audio to mono."""
        # Reshape into (samples, channels) and average
        n_samples = len(audio) // channels
        audio = audio[: n_samples * channels]  # trim any partial frame
        audio = audio.reshape(-1, channels)
        return audio.mean(axis=1).astype(np.float32)

    @staticmethod
    def _resample_to_16k(audio: np.ndarray, orig_sr: int) -> np.ndarray:
        """Resample audio from orig_sr to 16 kHz using scipy."""
        from scipy.signal import resample

        if orig_sr == SystemRecorder.WHISPER_RATE:
            return audio

        # Calculate the number of output samples
        duration = len(audio) / orig_sr
        target_samples = int(duration * SystemRecorder.WHISPER_RATE)

        if target_samples == 0:
            return np.array([], dtype=np.float32)

        resampled = resample(audio, target_samples)
        return resampled.astype(np.float32)
