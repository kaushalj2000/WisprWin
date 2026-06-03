"""
main.py — WisprWin entry point.

Architecture:
  • Main thread   — CustomTkinter mainloop (the settings/dashboard window)
  • BG thread 1   — pystray tray icon
  • BG thread 2   — hotkey hook (keyboard LL hook, fallback poll)
  • BG thread 3+  — model loading / transcription (on demand)

Cross-thread safety:
  • Tray → GUI:  messages pushed to self._tray_q, drained every 100 ms via root.after()
  • BG  → GUI:  self._root.after(0, fn) scheduled from _set_icon()
"""

import sys
import os
import queue
import threading
import time
from pathlib import Path
import numpy as np

# ── Fix for pythonw.exe ───────────────────────────────────────────────────────
if sys.stdout is None or sys.stderr is None:
    log_path = Path(os.environ.get("APPDATA", "~")) / "WisprWin" / "wisprwin.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(log_path, "a", encoding="utf-8")
    if sys.stdout is None: sys.stdout = log_file
    if sys.stderr is None: sys.stderr = log_file

# ── make sure wisprwin/ is importable regardless of CWD ──────────────────────
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import pystray
from PIL import Image
import keyboard

import settings as cfg_mod
from recorder        import AudioDeviceError, Recorder
from system_recorder import SystemAudioError, SystemRecorder
from transcriber     import Transcriber
from injector        import paste_text

try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    _HAS_WINSOUND = False

ASSETS_DIR = HERE / "assets"


def _ensure_icons() -> None:
    needed = ["icon_idle.png", "icon_recording.png", "icon_processing.png"]
    if not all((ASSETS_DIR / n).exists() for n in needed):
        from make_icons import make_icons
        make_icons()

def _load_image(name: str) -> Image.Image:
    return Image.open(ASSETS_DIR / name)


# ─────────────────────────────────────────────────────────────────────────────

class WisprApp:
    def __init__(self) -> None:
        self.config     = cfg_mod.load_config()
        self.recorder   = Recorder()
        self.system_recorder = SystemRecorder()
        self.transcriber: Transcriber | None = None
        self.tray_icon: pystray.Icon | None = None

        # ── Mic dictation state ───────────────────────────────────────────
        self._physical_key_down   = False
        self._is_recording        = False
        self._record_start_t      = 0.0
        self._processing_lock     = threading.Lock()
        self._processing_started_at = None   # watchdog timestamp
        self._model_loading       = False
        self._polling             = False
        self._hook_id             = None     # keyboard.hook handle

        # ── System audio state ────────────────────────────────────────────
        self._system_recording    = False
        self._system_record_start = 0.0
        self._system_physical_down = False
        self._system_transcript_history = []

        # CTk root — set in run()
        self._root = None

        # Thread-safe queue for tray → GUI messages
        self._tray_q: queue.Queue = queue.Queue()

        # Status/History update callbacks (set by MainWindow)
        self._status_callback = None
        self._history_callback = None
        self._history = []

        # System audio UI callbacks (set by MainWindow)
        self._system_status_callback = None
        self._system_transcript_callback = None

        self._img_idle       = None
        self._img_recording  = None
        self._img_processing = None

    # ── Tray icon state ───────────────────────────────────────────────────────

    def _set_icon(self, state: str) -> None:
        """Update tray icon and push status to GUI (thread-safe)."""
        img_map = {
            "idle":       self._img_idle,
            "recording":  self._img_recording,
            "processing": self._img_processing,
        }
        img = img_map.get(state, self._img_idle)
        if self.tray_icon and img:
            self.tray_icon.icon = img

        # Schedule GUI update on main thread (root.after is NOT safe from
        # non-main threads, so we push to queue and poll from main thread)
        self._tray_q.put(("status", state))

    def _drain_tray_queue(self) -> None:
        """Called every 100 ms on the main thread to process cross-thread messages."""
        try:
            while True:
                msg = self._tray_q.get_nowait()
                kind = msg[0]
                if kind == "status":
                    if self._status_callback:
                        try:
                            self._status_callback(msg[1])
                        except Exception:
                            pass
                elif kind == "history":
                    if self._history_callback:
                        try:
                            self._history_callback(msg[1])
                        except Exception:
                            pass
                elif kind == "system_status":
                    if self._system_status_callback:
                        try:
                            self._system_status_callback(msg[1])
                        except Exception:
                            pass
                elif kind == "system_transcript":
                    if self._system_transcript_callback:
                        try:
                            self._system_transcript_callback(msg[1])
                        except Exception:
                            pass
                elif kind == "show":
                    self._do_show_window()
                elif kind == "quit":
                    self._do_quit()
        except queue.Empty:
            pass

        # Watchdog — if transcription hangs > 30 s, force-reset so the
        # app never gets stuck in "processing" state.
        started = self._processing_started_at
        if started is not None and (time.monotonic() - started) > 30:
            print("[main] WATCHDOG — processing stuck, forcing reset")
            self._processing_started_at = None
            try:
                self._processing_lock.release()
            except RuntimeError:
                pass
            self._set_icon("idle")

        if self._root:
            self._root.after(100, self._drain_tray_queue)

    # ── Hotkey handlers ───────────────────────────────────────────────────────

    def _toggle_recording(self) -> None:
        if self._model_loading:
            return
        if not self._is_recording:
            self._is_recording = True
            self._record_start_t = time.monotonic()
            try:
                self.recorder.start()
            except AudioDeviceError as e:
                print(f"[main] Audio device error: {e}")
                self._is_recording = False
                self._tray_q.put(("status", "error"))
                return
            self._set_icon("recording")
            if self.config.get("sound_feedback") and _HAS_WINSOUND:
                threading.Thread(target=lambda: winsound.Beep(880, 120), daemon=True).start()
        else:
            held_for = time.monotonic() - self._record_start_t
            if held_for < 0.3:
                return
            self._is_recording = False
            audio = self.recorder.stop()
            threading.Thread(target=self._process_audio, args=(audio,), daemon=True).start()

    def _process_audio(self, audio) -> None:
        if not self._processing_lock.acquire(blocking=False):
            return
        self._processing_started_at = time.monotonic()
        try:
            self._set_icon("processing")
            if self.transcriber is None:
                print("[main] Transcriber not ready yet.")
                return
            duration_s = len(audio) / 16_000 if audio is not None and len(audio) > 0 else 0
            rms  = float(np.sqrt(np.mean(audio ** 2))) if duration_s > 0 else 0.0
            peak = float(np.max(np.abs(audio))) if duration_s > 0 else 0.0
            print(f"[main] Audio: {duration_s:.2f}s  RMS: {rms:.6f}  Peak: {peak:.6f}")
            if duration_s < 0.5:
                print("[main] Recording too short — ignored.")
                return
            if rms < 0.001:
                print(f"[main] SILENT AUDIO (RMS={rms:.6f})")
                return
            text = self.transcriber.transcribe(audio)
            print(f"[main] Transcribed: {text!r}")
            if text:
                self._history.insert(0, {"text": text, "time": time.time()})
                self._history = self._history[:10]
                self._tray_q.put(("history", self._history))
                paste_text(text, restore_clipboard=self.config.get("restore_clipboard", True))
                if self.config.get("sound_feedback") and _HAS_WINSOUND:
                    winsound.Beep(660, 80)
        finally:
            self._processing_started_at = None
            self._set_icon("idle")
            try:
                self._processing_lock.release()
            except RuntimeError:
                pass  # watchdog may have already released

    # ── System audio session management ────────────────────────────────────────

    def _toggle_system_audio(self) -> None:
        """Toggle system audio recording on / off (called from hotkey)."""
        if self._model_loading:
            return
        if self._system_recording:
            self._stop_system_audio()
        else:
            self._start_system_audio()

    def _start_system_audio(self) -> None:
        """Begin capturing system audio via WASAPI loopback."""
        try:
            self.system_recorder.start()
        except SystemAudioError as e:
            print(f"[main] System audio error: {e}")
            self._tray_q.put(("system_status", "error"))
            return
        self._system_recording = True
        self._system_record_start = time.monotonic()
        self._tray_q.put(("system_status", "recording"))
        if self.config.get("sound_feedback") and _HAS_WINSOUND:
            threading.Thread(
                target=lambda: winsound.Beep(1000, 150), daemon=True
            ).start()
        print("[main] System audio recording started.")

    def _stop_system_audio(self) -> None:
        """Stop system audio capture and transcribe."""
        if not self._system_recording:
            return
        self._system_recording = False
        audio = self.system_recorder.stop()
        self._tray_q.put(("system_status", "processing"))
        if self.config.get("sound_feedback") and _HAS_WINSOUND:
            threading.Thread(
                target=lambda: winsound.Beep(700, 150), daemon=True
            ).start()
        threading.Thread(
            target=self._process_system_audio, args=(audio,), daemon=True
        ).start()

    def _process_system_audio(self, audio) -> None:
        """Transcribe system audio and push result to UI."""
        if not self._processing_lock.acquire(blocking=True, timeout=60):
            print("[main] System audio: could not acquire processing lock.")
            self._tray_q.put(("system_status", "idle"))
            return
        try:
            if self.transcriber is None:
                print("[main] Transcriber not ready yet.")
                self._tray_q.put(("system_status", "idle"))
                return

            duration_s = len(audio) / 16_000 if audio is not None and len(audio) > 0 else 0
            rms = float(np.sqrt(np.mean(audio ** 2))) if duration_s > 0 else 0.0
            print(f"[main] System audio: {duration_s:.2f}s  RMS: {rms:.6f}")

            if duration_s < 0.5:
                print("[main] System audio too short — ignored.")
                self._tray_q.put(("system_status", "idle"))
                return
            if rms < 0.001:
                print(f"[main] System audio SILENT (RMS={rms:.6f})")
                self._tray_q.put(("system_status", "idle"))
                return

            text = self.transcriber.transcribe(audio)
            print(f"[main] System audio transcribed: {text!r}")

            if text:
                entry = {
                    "text": text,
                    "time": time.time(),
                    "duration": duration_s,
                }
                self._system_transcript_history.insert(0, entry)
                self._system_transcript_history = \
                    self._system_transcript_history[:20]
                self._tray_q.put(
                    ("system_transcript", self._system_transcript_history)
                )
        finally:
            self._tray_q.put(("system_status", "idle"))
            try:
                self._processing_lock.release()
            except RuntimeError:
                pass

    # ── Hotkey registration ───────────────────────────────────────────────────

    def _hotkey_hook(self, event) -> bool:
        """Called by keyboard lib on every global key event (Windows LL hook)."""
        if not self._polling:
            return True

        # ── Mic dictation hotkey (hold-to-record) ─────────────────────────
        try:
            is_down = keyboard.is_pressed(self._target_hotkey)
        except Exception:
            is_down = False
        if is_down and not self._physical_key_down:
            self._physical_key_down = True
            self._toggle_recording()
        elif not is_down and self._physical_key_down:
            self._physical_key_down = False

        # ── System audio hotkey (toggle on/off) ──────────────────────────
        try:
            sys_down = keyboard.is_pressed(self._target_sys_hotkey)
        except Exception:
            sys_down = False
        if sys_down and not self._system_physical_down:
            self._system_physical_down = True
            self._toggle_system_audio()
        elif not sys_down and self._system_physical_down:
            self._system_physical_down = False

        return True

    def _hotkey_poll_loop(self):
        """Fallback high-frequency poll if keyboard.hook fails."""
        while self._polling:
            # ── Mic hotkey ─────────────────────────────────────────────────
            try:
                is_down = keyboard.is_pressed(self._target_hotkey)
            except Exception:
                is_down = False
            if is_down and not self._physical_key_down:
                self._physical_key_down = True
                self._toggle_recording()
            elif not is_down and self._physical_key_down:
                self._physical_key_down = False

            # ── System audio hotkey ────────────────────────────────────────
            try:
                sys_down = keyboard.is_pressed(self._target_sys_hotkey)
            except Exception:
                sys_down = False
            if sys_down and not self._system_physical_down:
                self._system_physical_down = True
                self._toggle_system_audio()
            elif not sys_down and self._system_physical_down:
                self._system_physical_down = False

            time.sleep(0.005)

    def _register_hotkey(self, hotkey: str, sys_hotkey: str | None = None) -> None:
        self._unregister_hotkeys()
        self._target_hotkey = hotkey.lower().strip()
        self._target_sys_hotkey = (
            sys_hotkey.lower().strip() if sys_hotkey
            else self.config.get("system_audio_hotkey", "right alt+/").lower().strip()
        )
        self._polling = True
        try:
            self._hook_id = keyboard.hook(self._hotkey_hook)
            print(f"[main] Hotkey hook registered: mic='{hotkey}', sys='{self._target_sys_hotkey}'")
        except Exception as e:
            print(f"[main] Keyboard hook failed ({e}), falling back to poll loop.")
            self._hook_id = None
            self._poll_thread = threading.Thread(target=self._hotkey_poll_loop, daemon=True)
            self._poll_thread.start()

    def _unregister_hotkeys(self) -> None:
        self._polling = False
        if self._hook_id is not None:
            try:
                keyboard.unhook(self._hook_id)
            except Exception:
                pass
            self._hook_id = None
        if hasattr(self, '_poll_thread'):
            try:
                self._poll_thread.join(timeout=0.5)
            except Exception:
                pass

    # ── Settings apply ────────────────────────────────────────────────────────

    def apply_settings(self, new_cfg: dict) -> None:
        """Called by the GUI when the user saves settings."""
        old_hotkey     = self.config.get("hotkey")
        old_sys_hotkey = self.config.get("system_audio_hotkey")
        old_model      = self.config.get("model")
        self.config = new_cfg.copy()
        cfg_mod.save_config(new_cfg)
        cfg_mod.set_startup(new_cfg.get("launch_at_startup", False))

        # Re-register hotkeys if either changed
        new_hotkey     = new_cfg.get("hotkey")
        new_sys_hotkey = new_cfg.get("system_audio_hotkey")
        if new_hotkey != old_hotkey or new_sys_hotkey != old_sys_hotkey:
            self._register_hotkey(new_hotkey, new_sys_hotkey)

        if new_cfg.get("model") != old_model and self.transcriber:
            def _swap():
                self._model_loading = True
                self._set_icon("processing")
                try:
                    self.transcriber.change_model(new_cfg["model"])
                    self.transcriber.set_language(new_cfg.get("language", "auto"))
                finally:
                    self._model_loading = False
                    self._set_icon("idle")
            threading.Thread(target=_swap, daemon=True).start()
        elif self.transcriber:
            self.transcriber.set_language(new_cfg.get("language", "auto"))

    def register_status_callback(self, cb) -> None:
        self._status_callback = cb

    def register_history_callback(self, cb) -> None:
        self._history_callback = cb

    def register_system_status_callback(self, cb) -> None:
        self._system_status_callback = cb

    def register_system_transcript_callback(self, cb) -> None:
        self._system_transcript_callback = cb

    # ── Window show/hide ──────────────────────────────────────────────────────

    def _do_show_window(self) -> None:
        if self._root:
            self._root.deiconify()
            self._root.lift()
            self._root.focus_force()

    def _hide_to_tray(self) -> None:
        if self._root:
            self._root.withdraw()

    # Called from pystray thread — push to queue:
    def _tray_show(self, icon=None, item=None) -> None:
        self._tray_q.put(("show",))

    def _tray_quit(self, icon=None, item=None) -> None:
        self._tray_q.put(("quit",))

    def _do_quit(self) -> None:
        print("[main] Quitting …")
        self._unregister_hotkeys()
        if self.tray_icon:
            threading.Thread(target=self.tray_icon.stop, daemon=True).start()
        if self._root:
            self._root.destroy()

    # ── Boot ─────────────────────────────────────────────────────────────────

    def run(self) -> None:
        _ensure_icons()
        self._img_idle       = _load_image("icon_idle.png")
        self._img_recording  = _load_image("icon_recording.png")
        self._img_processing = _load_image("icon_processing.png")

        # Audio device diagnostics
        try:
            import sounddevice as sd
            dev = sd.query_devices(kind='input')
            print(f"[main] Default input: {dev['name']}")
        except Exception as e:
            print(f"[main] Audio device query failed: {e}")

        # ── Create CTk root on main thread ────────────────────────────────
        import customtkinter as ctk
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        ctk.set_widget_scaling(1.0)  # prevent CTk from double-scaling on high-DPI

        self._root = ctk.CTk()
        self._root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

        # Build the main window UI into root
        from ui.main_window import MainWindow
        self._main_win = MainWindow(
            root=self._root,
            app=self,
        )

        # Start draining cross-thread messages
        self._root.after(100, self._drain_tray_queue)

        # ── Pystray in background thread ──────────────────────────────────
        menu = pystray.Menu(
            pystray.MenuItem("Open WisprWin", self._tray_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("✕  Quit", self._tray_quit),
        )
        self.tray_icon = pystray.Icon(
            name  = "WisprWin",
            icon  = self._img_processing,
            title = "WisprWin — Voice Dictation",
            menu  = menu,
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

        # ── Load model in background ──────────────────────────────────────
        def _load_model():
            self._model_loading = True
            self._set_icon("processing")
            try:
                self.transcriber = Transcriber(
                    model_name=self.config.get("model", "base"),
                    language=self.config.get("language", "auto"),
                )
            except Exception as e:
                print(f"[main] FATAL: Could not load model: {e}")
            finally:
                self._model_loading = False
                self._set_icon("idle")

        downloaded_models = cfg_mod.get_downloaded_models()
        if not downloaded_models:
            print("[main] No models found. Prompting user to download.")
            # Force Model Manager to open on startup
            self._root.after(500, self._main_win._open_model_manager)
            self._set_icon("idle")
        else:
            threading.Thread(target=_load_model, daemon=True).start()


        # ── Register hotkey ───────────────────────────────────────────────
        self._register_hotkey(
            self.config.get("hotkey", "right alt+."),
            self.config.get("system_audio_hotkey", "right alt+/"),
        )
        cfg_mod.set_startup(self.config.get("launch_at_startup", False))

        print("[main] WisprWin running. Hold hotkey to dictate.")
        self._root.mainloop()   # blocks main thread


if __name__ == "__main__":
    app = WisprApp()
    app.run()
