"""
ui/main_window.py — WisprWin main settings window.

Builds directly into the CTk root that was created on the main thread.
No separate thread needed — all GUI operations are safe.
"""

import threading
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from main import WisprApp

import settings as cfg_mod

# ── palette ──────────────────────────────────────────────────────────────────
BG           = "#0F0F1A"
SURFACE      = "#1A1A2E"
SURFACE_2    = "#16213E"
ACCENT       = "#7C3AED"
ACCENT_HV    = "#6D28D9"
ACCENT_LIGHT = "#A78BFA"
TEXT         = "#E2E8F0"
SUBTEXT      = "#94A3B8"
BORDER       = "#2D2D4A"
SUCCESS      = "#22C55E"
RED          = "#EF4444"
AMBER        = "#F59E0B"

STATUS_COLORS = {
    "idle":       (SUCCESS, "Idle"),
    "recording":  (RED,     "Recording"),
    "processing": (AMBER,   "Processing…"),
}

LANGUAGES = {
    "Auto Detect": "auto",
    "English":     "en",
    "Telugu":      "te",
    "Hindi":       "hi",
    "Spanish":     "es",
    "French":      "fr",
    "German":      "de",
    "Portuguese":  "pt",
    "Chinese":     "zh",
    "Japanese":    "ja",
    "Arabic":      "ar",
    "Korean":      "ko",
    "Russian":     "ru",
    "Italian":     "it",
}


class MainWindow:
    """
    Builds and manages the main WisprWin dashboard inside `root`.

    Parameters
    ----------
    root : ctk.CTk
        The main CTk window (already created on main thread).
    app  : WisprApp
        Reference to the app for config access and callbacks.
    """

    def __init__(self, root: ctk.CTk, app: "WisprApp") -> None:
        self._root = root
        self._app  = app
        self._model_manager: "ModelManagerWindow | None" = None

        self._build_window()
        self._build_ui()

        # Register our status updater with the app
        app.register_status_callback(self._update_status)

    # ── Window setup ─────────────────────────────────────────────────────────

    def _build_window(self) -> None:
        root = self._root
        root.title("WisprWin")
        root.configure(fg_color=BG)
        root.resizable(False, False)

        w, h = 520, 660
        x = (root.winfo_screenwidth()  - w) // 2
        y = (root.winfo_screenheight() - h) // 2
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.iconbitmap(default=str(
            __import__("pathlib").Path(__file__).resolve().parent.parent
            / "assets" / "icon.ico"
        ))

    # ── Status indicator (called from main thread via queue drain) ────────────

    def _update_status(self, state: str) -> None:
        color, label = STATUS_COLORS.get(state, STATUS_COLORS["idle"])
        try:
            self._status_dot.configure(text_color=color)
            self._status_label.configure(text=label, text_color=color)
        except Exception:
            pass

    # ── UI build ─────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        cfg = self._app.config

        # ── Header ────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self._root, fg_color=SURFACE, corner_radius=0, height=80)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=24, pady=16)

        title_f = ctk.CTkFrame(hdr_inner, fg_color="transparent")
        title_f.pack(side="left")
        ctk.CTkLabel(title_f, text="WisprWin",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(title_f, text="  v1.0",
                     font=ctk.CTkFont("Segoe UI", 14),
                     text_color=SUBTEXT).pack(side="left", pady=(4, 0))

        # Status badge
        status_f = ctk.CTkFrame(hdr_inner, fg_color=SURFACE_2, corner_radius=20)
        status_f.pack(side="right")
        self._status_dot = ctk.CTkLabel(status_f, text="●",
                                         font=ctk.CTkFont(size=14),
                                         text_color=AMBER, width=20)
        self._status_dot.pack(side="left", padx=(12, 4), pady=8)
        self._status_label = ctk.CTkLabel(status_f, text="Loading…",
                                           font=ctk.CTkFont("Segoe UI", 13),
                                           text_color=AMBER)
        self._status_label.pack(side="left", padx=(0, 14), pady=8)

        # ── Scrollable body ───────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self._root, fg_color=BG)
        body.pack(fill="both", expand=True)

        # ── HOTKEY ────────────────────────────────────────────────────────
        self._section(body, "HOTKEY")
        hk_card = self._card(body)
        ctk.CTkLabel(hk_card, text="Activation shortcut:",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=SUBTEXT
                     ).pack(anchor="w", padx=16, pady=(12, 2))
        self._hotkey_var = ctk.StringVar(value=cfg.get("hotkey", "right alt+."))
        ctk.CTkEntry(hk_card, textvariable=self._hotkey_var,
                     font=ctk.CTkFont("Segoe UI", 14),
                     fg_color=BG, border_color=BORDER,
                     text_color=TEXT, width=300, height=38
                     ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── LANGUAGE ──────────────────────────────────────────────────────
        self._section(body, "LANGUAGE")
        lang_card = self._card(body)
        lang_code = cfg.get("language", "auto")
        lang_name = next((k for k, v in LANGUAGES.items() if v == lang_code), "Auto Detect")
        self._lang_var = ctk.StringVar(value=lang_name)
        ctk.CTkLabel(lang_card, text="Transcription language:",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=SUBTEXT
                     ).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkOptionMenu(lang_card, variable=self._lang_var,
                          values=list(LANGUAGES.keys()),
                          font=ctk.CTkFont("Segoe UI", 13),
                          fg_color=BG, button_color=ACCENT,
                          button_hover_color=ACCENT_HV,
                          dropdown_fg_color=SURFACE,
                          dropdown_hover_color=ACCENT,
                          width=300, height=36
                          ).pack(anchor="w", padx=16, pady=(0, 12))

        # ── OPTIONS ───────────────────────────────────────────────────────
        self._section(body, "OPTIONS")
        opts_card = self._card(body)
        self._sound_var   = ctk.BooleanVar(value=cfg.get("sound_feedback", True))
        self._clip_var    = ctk.BooleanVar(value=cfg.get("restore_clipboard", True))
        self._startup_var = ctk.BooleanVar(value=cfg.get("launch_at_startup", False))
        self._switch_row(opts_card, "Sound feedback",
                         "Beep when recording starts and stops",
                         self._sound_var)
        self._switch_row(opts_card, "Restore clipboard",
                         "Restore clipboard content after paste",
                         self._clip_var)
        self._switch_row(opts_card, "Launch at Windows startup",
                         "Start WisprWin automatically when you log in",
                         self._startup_var)

        # ── MODEL ─────────────────────────────────────────────────────────
        self._section(body, "MODEL")
        model_card = self._card(body)
        model_row = ctk.CTkFrame(model_card, fg_color="transparent")
        model_row.pack(fill="x", padx=16, pady=12)
        self._active_model_label = ctk.CTkLabel(
            model_row,
            text=f"Active: {cfg.get('model', 'base')}",
            font=ctk.CTkFont("Segoe UI", 14, "bold"),
            text_color=ACCENT_LIGHT,
        )
        self._active_model_label.pack(side="left")
        ctk.CTkButton(model_row, text="Manage Models",
                      font=ctk.CTkFont("Segoe UI", 13, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HV,
                      corner_radius=8, height=36,
                      command=self._open_model_manager
                      ).pack(side="right")

        # ── Separator hint ─────────────────────────────────────────────────
        hint_f = ctk.CTkFrame(body, fg_color="transparent")
        hint_f.pack(fill="x", padx=24, pady=(8, 4))
        ctk.CTkLabel(hint_f,
                     text="Closing this window hides it to the system tray. Right-click the tray icon to quit.",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=SUBTEXT, wraplength=460, justify="left"
                     ).pack(anchor="w")

        # ── Bottom buttons ─────────────────────────────────────────────────
        btn_f = ctk.CTkFrame(self._root, fg_color=BG, height=70)
        btn_f.pack(fill="x", side="bottom")
        btn_f.pack_propagate(False)
        inner = ctk.CTkFrame(btn_f, fg_color="transparent")
        inner.pack(fill="x", padx=24, pady=16)
        ctk.CTkButton(inner, text="Save",
                      font=ctk.CTkFont("Segoe UI", 14, "bold"),
                      fg_color=ACCENT, hover_color=ACCENT_HV,
                      corner_radius=8, width=120, height=40,
                      command=self._save
                      ).pack(side="right")
        ctk.CTkButton(inner, text="Hide to Tray",
                      font=ctk.CTkFont("Segoe UI", 13),
                      fg_color=SURFACE, hover_color=BORDER,
                      corner_radius=8, width=130, height=40,
                      command=self._app._hide_to_tray
                      ).pack(side="right", padx=(0, 10))

    # ── UI helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _section(parent, label: str) -> None:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", padx=24, pady=(16, 4))
        ctk.CTkLabel(f, text=label,
                     font=ctk.CTkFont("Segoe UI", 10, "bold"),
                     text_color=SUBTEXT).pack(side="left")

    @staticmethod
    def _card(parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12,
                            border_width=1, border_color=BORDER)
        card.pack(fill="x", padx=24, pady=(0, 4))
        return card

    @staticmethod
    def _switch_row(parent, title: str, subtitle: str, var: ctk.BooleanVar) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=8)
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(txt, text=title,
                     font=ctk.CTkFont("Segoe UI", 13), text_color=TEXT
                     ).pack(anchor="w")
        ctk.CTkLabel(txt, text=subtitle,
                     font=ctk.CTkFont("Segoe UI", 11), text_color=SUBTEXT
                     ).pack(anchor="w")
        ctk.CTkSwitch(row, text="", variable=var,
                      onvalue=True, offvalue=False,
                      fg_color=BORDER, progress_color=ACCENT,
                      button_color=TEXT, button_hover_color=ACCENT_LIGHT,
                      width=46).pack(side="right")

    # ── Model Manager ─────────────────────────────────────────────────────────

    def _open_model_manager(self) -> None:
        if self._model_manager is not None:
            try:
                self._model_manager.focus()
                return
            except Exception:
                self._model_manager = None

        from ui.model_manager import ModelManagerWindow
        self._model_manager = ModelManagerWindow(
            parent=self._root,
            app=self._app,
            on_model_changed=self._on_model_changed,
        )

    def _on_model_changed(self, model_name: str) -> None:
        self._app.config["model"] = model_name
        self._active_model_label.configure(text=f"Active: {model_name}")

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        hotkey = self._hotkey_var.get().strip().lower()
        if not hotkey:
            return

        new_cfg = dict(self._app.config)
        new_cfg["hotkey"]            = hotkey
        new_cfg["language"]          = LANGUAGES.get(self._lang_var.get(), "auto")
        new_cfg["sound_feedback"]    = self._sound_var.get()
        new_cfg["restore_clipboard"] = self._clip_var.get()
        new_cfg["launch_at_startup"] = self._startup_var.get()

        self._app.apply_settings(new_cfg)

        # Brief visual confirmation
        self._show_save_toast()

    def _show_save_toast(self) -> None:
        """Flash a brief 'Saved!' message."""
        toast = ctk.CTkLabel(
            self._root, text="  ✓  Settings saved  ",
            font=ctk.CTkFont("Segoe UI", 13, "bold"),
            text_color=SUCCESS, fg_color="#0D2818",
            corner_radius=8,
        )
        toast.place(relx=0.5, rely=0.96, anchor="center")
        self._root.after(2000, toast.destroy)
