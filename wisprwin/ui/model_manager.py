"""
ui/model_manager.py — Model Manager window for WisprWin.

Clean card layout with explicit text labels (no cryptic icons/stars).
Download runs in a background thread. All UI updates are posted back
to the main thread via CTkToplevel.after(), which is safe because this
window is created and lives on the main thread.
"""

import threading
from typing import Callable, TYPE_CHECKING

import customtkinter as ctk

import settings as cfg_mod

if TYPE_CHECKING:
    from main import WisprApp

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
SUCCESS_BG   = "#0D2818"
RED          = "#EF4444"
RED_BG       = "#2D0A0A"
AMBER        = "#F59E0B"
AMBER_BG     = "#2D1A00"
HIGHLIGHT_BG = "#1E1B4B"

# Speed / accuracy text labels (stars → words)
_SPEED_LABELS    = {5: "Very Fast", 4: "Fast", 3: "Medium", 2: "Slow",  1: "Very Slow"}
_ACCURACY_LABELS = {5: "Excellent", 4: "Very Good", 3: "Good",  2: "Fair", 1: "Basic"}
_SPEED_COLORS    = {5: SUCCESS, 4: SUCCESS, 3: AMBER, 2: RED, 1: RED}
_ACCURACY_COLORS = {5: SUCCESS, 4: SUCCESS, 3: AMBER, 2: RED, 1: RED}

# ── model catalog ────────────────────────────────────────────────────────────
# speed/accuracy are integers 1-5 mapped to text labels above.
# languages_count: actual number or "English only".
MODEL_CATALOG = [
    {
        "name": "tiny",
        "size": "75 MB",
        "speed": 5,
        "accuracy": 2,
        "languages": "99 languages",
        "best_for": "Quick notes, weak or old hardware",
    },
    {
        "name": "base",
        "size": "145 MB",
        "speed": 4,
        "accuracy": 3,
        "languages": "99 languages",
        "best_for": "Good starting point for most users",
    },
    {
        "name": "small",
        "size": "465 MB",
        "speed": 4,
        "accuracy": 4,
        "languages": "99 languages",
        "best_for": "Best balance of speed and accuracy",
    },
    {
        "name": "medium",
        "size": "1.5 GB",
        "speed": 3,
        "accuracy": 4,
        "languages": "99 languages",
        "best_for": "Higher accuracy at moderate speed",
    },
    {
        "name": "large-v3",
        "size": "3 GB",
        "speed": 2,
        "accuracy": 5,
        "languages": "99 languages",
        "best_for": "Maximum accuracy — slow on CPU, needs GPU",
    },
    {
        "name": "large-v3-turbo",
        "size": "800 MB",
        "speed": 4,
        "accuracy": 5,
        "languages": "99 languages",
        "best_for": "Best overall choice — highly recommended",
        "recommended": True,
    },
    {
        "name": "distil-large-v2",
        "size": "750 MB",
        "speed": 5,
        "accuracy": 4,
        "languages": "English only",
        "best_for": "Fast and accurate — English speakers only",
    },
    {
        "name": "distil-large-v3",
        "size": "750 MB",
        "speed": 5,
        "accuracy": 5,
        "languages": "English only",
        "best_for": "Best English-only model available",
    },
]


class ModelManagerWindow:
    """Model Manager as a CTkToplevel (lives on the main thread — no threading issues)."""

    def __init__(
        self,
        parent: ctk.CTk,
        app: "WisprApp",
        on_model_changed: Callable[[str], None],
    ) -> None:
        self._app = app
        self._on_model_changed = on_model_changed
        self._downloading: set[str] = set()
        self._card_refs: dict[str, dict] = {}

        self._win = ctk.CTkToplevel(parent)
        self._win.title("WisprWin · Model Manager")
        self._win.configure(fg_color=BG)
        self._win.resizable(True, True)
        self._win.minsize(680, 500)

        w, h = 720, 700
        x = (self._win.winfo_screenwidth()  - w) // 2
        y = (self._win.winfo_screenheight() - h) // 2
        self._win.geometry(f"{w}x{h}+{x}+{y}")
        self._win.attributes("-topmost", True)

        self._build_ui()

    def focus(self) -> None:
        self._win.lift()
        self._win.focus_force()

    def destroy(self) -> None:
        try:
            self._win.destroy()
        except Exception:
            pass

    # ── Build UI ─────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # Header
        hdr = ctk.CTkFrame(self._win, fg_color=SURFACE, corner_radius=0, height=90)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="x", padx=28, pady=14)
        ctk.CTkLabel(hdr_inner, text="Model Manager",
                     font=ctk.CTkFont("Segoe UI", 22, "bold"),
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(hdr_inner,
                     text="Download Whisper models · Each model is stored locally on your PC",
                     font=ctk.CTkFont("Segoe UI", 12), text_color=SUBTEXT
                     ).pack(anchor="w", pady=(2, 0))

        # Column header row
        col_hdr = ctk.CTkFrame(self._win, fg_color="transparent", height=28)
        col_hdr.pack(fill="x", padx=28, pady=(8, 0))
        col_hdr.pack_propagate(False)
        for txt, anchor, side in [
            ("Model", "w", "left"),
            ("File Size", "w", "left"),
            ("Speed", "w", "left"),
            ("Accuracy", "w", "left"),
            ("Languages", "w", "left"),
        ]:
            ctk.CTkLabel(col_hdr, text=txt,
                         font=ctk.CTkFont("Segoe UI", 10, "bold"),
                         text_color=SUBTEXT, width=90
                         ).pack(side=side, padx=(0, 4))

        # Scrollable list
        self._scroll = ctk.CTkScrollableFrame(
            self._win, fg_color=BG,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=ACCENT,
        )
        self._scroll.pack(fill="both", expand=True, padx=12, pady=8)

        self._populate_cards()

    def _populate_cards(self) -> None:
        """Build all cards based on current downloaded/active state."""
        for child in self._scroll.winfo_children():
            child.destroy()
        self._card_refs.clear()

        downloaded   = set(cfg_mod.get_downloaded_models())
        active_model = self._app.config.get("model", "base")

        for info in MODEL_CATALOG:
            name        = info["name"]
            is_dl       = name in downloaded
            is_active   = name == active_model
            is_rec      = info.get("recommended", False)
            self._build_card(info, is_downloaded=is_dl, is_active=is_active, is_recommended=is_rec)

    def _build_card(self, info: dict, is_downloaded: bool, is_active: bool, is_recommended: bool) -> None:
        name = info["name"]
        speed_n    = info["speed"]
        acc_n      = info["accuracy"]
        speed_txt  = _SPEED_LABELS[speed_n]
        acc_txt    = _ACCURACY_LABELS[acc_n]
        speed_col  = _SPEED_COLORS[speed_n]
        acc_col    = _ACCURACY_COLORS[acc_n]
        lang_col   = AMBER if info["languages"] == "English only" else TEXT

        card_bg     = HIGHLIGHT_BG if is_active else SURFACE
        border_col  = ACCENT       if is_active else (ACCENT_LIGHT if is_recommended else BORDER)
        border_w    = 2            if is_active else 1

        card = ctk.CTkFrame(self._scroll, fg_color=card_bg, corner_radius=12,
                            border_width=border_w, border_color=border_col)
        card.pack(fill="x", pady=5, padx=4)

        # ── Row 1: Name + badges + action button ──────────────────────────
        row1 = ctk.CTkFrame(card, fg_color="transparent")
        row1.pack(fill="x", padx=16, pady=(12, 0))

        # Left: name + badges
        left = ctk.CTkFrame(row1, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(left, text=name,
                     font=ctk.CTkFont("Segoe UI", 15, "bold"),
                     text_color=TEXT).pack(side="left")

        if is_recommended:
            ctk.CTkLabel(left, text="  RECOMMENDED  ",
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=AMBER, fg_color=AMBER_BG,
                         corner_radius=6).pack(side="left", padx=(10, 0))

        if is_active:
            ctk.CTkLabel(left, text="  ACTIVE  ",
                         font=ctk.CTkFont("Segoe UI", 9, "bold"),
                         text_color=SUCCESS, fg_color=SUCCESS_BG,
                         corner_radius=6).pack(side="left", padx=(8, 0))

        # Right: action area (holds button or progress)
        action_f = ctk.CTkFrame(row1, fg_color="transparent")
        action_f.pack(side="right")
        self._render_action(action_f, name, is_downloaded, is_active)

        # ── Row 2: Metadata chips ─────────────────────────────────────────
        row2 = ctk.CTkFrame(card, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=(8, 0))

        self._chip(row2, "File Size",  info["size"],  TEXT)
        self._chip(row2, "Speed",      speed_txt,     speed_col)
        self._chip(row2, "Accuracy",   acc_txt,       acc_col)
        self._chip(row2, "Languages",  info["languages"], lang_col)

        # ── Row 3: Description ────────────────────────────────────────────
        row3 = ctk.CTkFrame(card, fg_color="transparent")
        row3.pack(fill="x", padx=16, pady=(4, 12))
        ctk.CTkLabel(row3, text=info["best_for"],
                     font=ctk.CTkFont("Segoe UI", 12), text_color=SUBTEXT
                     ).pack(anchor="w")

        # Store refs for dynamic updates
        self._card_refs[name] = {"card": card, "action_f": action_f}

    @staticmethod
    def _chip(parent, label: str, value: str, value_color: str) -> None:
        """A small label+value pair."""
        f = ctk.CTkFrame(parent, fg_color=SURFACE_2, corner_radius=6)
        f.pack(side="left", padx=(0, 8), pady=2)
        ctk.CTkLabel(f, text=label + ": ",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=SUBTEXT).pack(side="left", padx=(8, 0), pady=4)
        ctk.CTkLabel(f, text=value,
                     font=ctk.CTkFont("Segoe UI", 11, "bold"),
                     text_color=value_color).pack(side="left", padx=(0, 8), pady=4)

    def _render_action(self, parent: ctk.CTkFrame, name: str,
                       is_downloaded: bool, is_active: bool) -> None:
        """Render the correct button(s) in the action area."""
        for child in parent.winfo_children():
            child.destroy()

        if name in self._downloading:
            # Progress indicator
            prog = ctk.CTkProgressBar(parent, width=140, height=12,
                                       fg_color=BORDER, progress_color=ACCENT,
                                       corner_radius=6, mode="indeterminate")
            prog.pack(side="left", padx=(0, 8))
            prog.start()
            ctk.CTkLabel(parent, text="Downloading…",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=ACCENT_LIGHT).pack(side="left")
            return

        if is_active:
            # No button needed — badge already shown on name row
            return

        if is_downloaded:
            ctk.CTkButton(parent, text="Set as Active",
                          font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          fg_color=SUCCESS, hover_color="#16A34A",
                          text_color="#FFFFFF",
                          corner_radius=8, height=32, width=120,
                          command=lambda n=name: self._set_active(n)
                          ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(parent, text="Delete",
                          font=ctk.CTkFont("Segoe UI", 11),
                          fg_color=SURFACE_2, hover_color=RED,
                          text_color=SUBTEXT,
                          corner_radius=8, height=32, width=70,
                          command=lambda n=name: self._delete_model(n)
                          ).pack(side="left")
        else:
            ctk.CTkButton(parent, text="Download",
                          font=ctk.CTkFont("Segoe UI", 12, "bold"),
                          fg_color=ACCENT, hover_color=ACCENT_HV,
                          corner_radius=8, height=32, width=110,
                          command=lambda n=name: self._start_download(n)
                          ).pack(side="left")

    # ── Actions ──────────────────────────────────────────────────────────────

    def _start_download(self, name: str) -> None:
        if name in self._downloading:
            return
        self._downloading.add(name)

        # Immediately refresh the action button to show progress
        refs = self._card_refs.get(name)
        if refs:
            self._render_action(refs["action_f"], name, False, False)

        def _do() -> None:
            try:
                import torch
                device       = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"
                from faster_whisper import WhisperModel
                m = WhisperModel(name, device=device, compute_type=compute_type,
                                 download_root=str(cfg_mod.MODELS_DIR))
                del m
                self._win.after(0, lambda: self._on_download_done(name, True))
            except Exception as e:
                print(f"[model_manager] Download failed '{name}': {e}")
                self._win.after(0, lambda err=str(e): self._on_download_done(name, False, err))

        threading.Thread(target=_do, daemon=True).start()

    def _on_download_done(self, name: str, success: bool, error: str = "") -> None:
        self._downloading.discard(name)
        refs = self._card_refs.get(name)
        if not refs:
            return

        if success:
            # Rebuild card to show Set as Active + Delete
            self._refresh_cards()
        else:
            # Show retry in action area
            af = refs["action_f"]
            for ch in af.winfo_children():
                ch.destroy()
            ctk.CTkLabel(af, text="Download failed",
                         font=ctk.CTkFont("Segoe UI", 11),
                         text_color=RED).pack(side="left", padx=(0, 8))
            ctk.CTkButton(af, text="Retry",
                          font=ctk.CTkFont("Segoe UI", 11),
                          fg_color=AMBER, hover_color="#D97706",
                          text_color="#000000",
                          corner_radius=8, height=30, width=70,
                          command=lambda: self._start_download(name)
                          ).pack(side="left")

    def _set_active(self, name: str) -> None:
        self._app.config["model"] = name
        cfg_mod.save_config(self._app.config)
        self._on_model_changed(name)
        self._refresh_cards()

    def _delete_model(self, name: str) -> None:
        if name == self._app.config.get("model"):
            self._warn_dialog(
                "Cannot delete the active model.\nPlease set another model as active first."
            )
            return

        ok = cfg_mod.delete_model(name)
        if ok:
            self._refresh_cards()
        else:
            self._warn_dialog(f"Could not delete model '{name}'.\nCheck if the file is in use.")

    def _refresh_cards(self) -> None:
        """Rebuild all cards with fresh downloaded/active state."""
        self._populate_cards()

    def _warn_dialog(self, msg: str) -> None:
        dlg = ctk.CTkToplevel(self._win)
        dlg.title("WisprWin")
        dlg.configure(fg_color=SURFACE)
        dlg.resizable(False, False)
        dlg.attributes("-topmost", True)
        w2, h2 = 360, 150
        x = (dlg.winfo_screenwidth()  - w2) // 2
        y = (dlg.winfo_screenheight() - h2) // 2
        dlg.geometry(f"{w2}x{h2}+{x}+{y}")
        ctk.CTkLabel(dlg, text=msg,
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=AMBER, justify="center",
                     wraplength=320).pack(pady=(24, 12))
        ctk.CTkButton(dlg, text="OK",
                      font=ctk.CTkFont("Segoe UI", 13),
                      fg_color=ACCENT, hover_color=ACCENT_HV,
                      corner_radius=8, width=80, height=34,
                      command=dlg.destroy).pack()
