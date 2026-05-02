"""
ui/model_manager.py — WisprWin Model Manager.

All sizes are ACTUAL PIXELS (set_widget_scaling=1.0 in main.py).
Cards use a flat single-padding layout — no nested row frames.
"""

import threading
from typing import Callable, TYPE_CHECKING

import customtkinter as ctk
import settings as cfg_mod

if TYPE_CHECKING:
    from main import WisprApp

# ══════════════════════════════════════════════════════════════════════════════
BG       = "#1C1C1E"
CARD     = "#2C2C2E"
CARD_HV  = "#363638"
INPUT    = "#242426"
HEADER   = "#242428"

ACC      = "#60A5FA"
ACC_HV   = "#3B82F6"
ACC_SOFT = "#1E3A5F"
ACC_TXT  = "#93C5FD"

TXT      = "#F5F5F7"
TXT2     = "#A1A1AA"
TXT3     = "#71717A"

BRD      = "#3A3A3C"
BRD_LT   = "#52525B"

GREEN    = "#34D399"
GREEN_HV = "#22C55E"
GREEN_BG = "#14291E"
RED      = "#F87171"
RED_BG   = "#291414"
AMBER    = "#FBBF24"
AMBER_HV = "#F59E0B"
AMBER_BG = "#292211"

ACTIVE_BG = "#1A2744"

FONT = "Segoe UI"
# ══════════════════════════════════════════════════════════════════════════════

def F(sz: int, b: bool = False) -> ctk.CTkFont:
    return ctk.CTkFont(family=FONT, size=sz, weight="bold" if b else "normal")

_SPD = {5:"Very Fast",4:"Fast",3:"Medium",2:"Slow",1:"Very Slow"}
_ACC = {5:"Excellent",4:"Very Good",3:"Good",2:"Fair",1:"Basic"}
_SC  = {5:GREEN,4:GREEN,3:AMBER,2:RED,1:RED}

MODELS = [
    {"name":"tiny","size":"75 MB","speed":5,"accuracy":2,
     "lang":"99 languages","desc":"Quick notes, weak hardware"},
    {"name":"base","size":"145 MB","speed":4,"accuracy":3,
     "lang":"99 languages","desc":"Good starting point"},
    {"name":"small","size":"465 MB","speed":4,"accuracy":4,
     "lang":"99 languages","desc":"Best balance of speed & accuracy"},
    {"name":"medium","size":"1.5 GB","speed":3,"accuracy":4,
     "lang":"99 languages","desc":"Higher accuracy, moderate speed"},
    {"name":"large-v3","size":"3 GB","speed":2,"accuracy":5,
     "lang":"99 languages","desc":"Maximum accuracy — needs GPU"},
    {"name":"large-v3-turbo","size":"800 MB","speed":4,"accuracy":5,
     "lang":"99 languages","desc":"Best overall — highly recommended",
     "rec":True},
    {"name":"distil-large-v2","size":"750 MB","speed":5,"accuracy":4,
     "lang":"English only","desc":"Fast & accurate — English only"},
    {"name":"distil-large-v3","size":"750 MB","speed":5,"accuracy":5,
     "lang":"English only","desc":"Best English-only model"},
]


class ModelManagerWindow:
    def __init__(self, parent, app: "WisprApp",
                 on_model_changed: Callable[[str], None]) -> None:
        self._app = app
        self._cb = on_model_changed
        self._dling: set[str] = set()
        self._refs: dict = {}

        self._w = ctk.CTkToplevel(parent)
        self._w.title("WisprWin · Models")
        self._w.configure(fg_color=BG)
        self._w.resizable(True, True)
        self._w.minsize(700, 500)
        sw = self._w.winfo_screenwidth()
        sh = self._w.winfo_screenheight()
        w, h = 780, int(sh * 0.80)
        self._w.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self._w.attributes("-topmost", True)
        self._build()

    def focus(self):
        self._w.lift(); self._w.focus_force()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = ctk.CTkFrame(self._w, fg_color=HEADER, corner_radius=0, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        hi = ctk.CTkFrame(hdr, fg_color="transparent")
        hi.pack(fill="x", padx=28, expand=True)
        ctk.CTkLabel(hi, text="Model Manager", font=F(22, True), text_color=TXT).pack(side="left")
        ctk.CTkLabel(hi, text="Download & manage Whisper models",
                     font=F(13), text_color=TXT3).pack(side="left", padx=(14,0))

        self._sc = ctk.CTkScrollableFrame(self._w, fg_color=BG,
                                          scrollbar_button_color=BRD,
                                          scrollbar_button_hover_color=BRD_LT)
        self._sc.pack(fill="both", expand=True, padx=8, pady=8)
        self._pop()

    def _pop(self):
        for w in self._sc.winfo_children(): w.destroy()
        self._refs.clear()
        dl = set(cfg_mod.get_downloaded_models())
        act = self._app.config.get("model", "base")

        if not dl:
            self._empty()

        for m in MODELS:
            n = m["name"]
            self._card(m, n in dl, n == act, m.get("rec", False))

    # ── Empty state ───────────────────────────────────────────────────────────

    def _empty(self):
        b = ctk.CTkFrame(self._sc, fg_color=CARD, corner_radius=10,
                         border_width=1, border_color=ACC)
        b.pack(fill="x", padx=16, pady=(4,16))
        ctk.CTkLabel(b, text="No models downloaded", font=F(16, True),
                     text_color=TXT).pack(pady=(20,4))
        ctk.CTkLabel(b, text="Pick a model below and click Download. The RECOMMENDED model is a great starting point.",
                     font=F(14), text_color=TXT2, wraplength=550,
                     justify="center").pack(padx=20, pady=(0,20))

    # ── Card — FLAT layout, no nested row frames ─────────────────────────────

    def _card(self, m, is_dl, is_act, is_rec):
        name = m["name"]

        if is_act:
            bg, bc = ACTIVE_BG, ACC
        elif is_rec:
            bg, bc = CARD, AMBER
        else:
            bg, bc = CARD, BRD

        c = ctk.CTkFrame(self._sc, fg_color=bg, corner_radius=10,
                         border_width=1, border_color=bc)
        c.pack(fill="x", padx=16, pady=(0,6))

        # Use grid for pixel-perfect control — no frame nesting
        c.grid_columnconfigure(0, weight=1)  # left side expands
        c.grid_columnconfigure(1, weight=0)  # right side fixed

        # Row 0: Name + badges | Action buttons
        name_f = ctk.CTkFrame(c, fg_color="transparent")
        name_f.grid(row=0, column=0, sticky="w", padx=16, pady=(12,0))

        ctk.CTkLabel(name_f, text=name, font=F(15, True), text_color=TXT).pack(side="left")
        if is_rec:
            ctk.CTkLabel(name_f, text=" REC ", font=F(10, True),
                         text_color=AMBER, fg_color=AMBER_BG,
                         corner_radius=6).pack(side="left", padx=(8,0))
        if is_act:
            ctk.CTkLabel(name_f, text=" ACTIVE ", font=F(10, True),
                         text_color=GREEN, fg_color=GREEN_BG,
                         corner_radius=6).pack(side="left", padx=(6,0))

        af = ctk.CTkFrame(c, fg_color="transparent")
        af.grid(row=0, column=1, sticky="e", padx=16, pady=(12,0))
        self._act(af, name, is_dl, is_act)

        # Row 1: Chips — directly in card, no wrapper frame
        chips = ctk.CTkFrame(c, fg_color="transparent")
        chips.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(6,0))

        lc = AMBER if "English" in m["lang"] else TXT2
        for lb, v, co in [("Size",m["size"],TXT2),
                          ("Speed",_SPD[m["speed"]],_SC[m["speed"]]),
                          ("Accuracy",_ACC[m["accuracy"]],_SC[m["accuracy"]]),
                          ("Lang",m["lang"],lc)]:
            ch = ctk.CTkFrame(chips, fg_color=INPUT, corner_radius=6)
            ch.pack(side="left", padx=(0,6))
            ctk.CTkLabel(ch, text=f"{lb}:", font=F(12), text_color=TXT3
                         ).pack(side="left", padx=(8,2), pady=4)
            ctk.CTkLabel(ch, text=v, font=F(12, True), text_color=co
                         ).pack(side="left", padx=(0,8), pady=4)

        # Row 2: Description
        ctk.CTkLabel(c, text=m["desc"], font=F(13), text_color=TXT3
                     ).grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(4,12))

        self._refs[name] = {"c": c, "af": af}

    # ── Action ────────────────────────────────────────────────────────────────

    def _act(self, p, name, is_dl, is_act):
        for w in p.winfo_children(): w.destroy()

        if name in self._dling:
            bar = ctk.CTkProgressBar(p, width=120, height=8,
                                     fg_color=BRD, progress_color=ACC,
                                     corner_radius=4, mode="indeterminate")
            bar.pack(side="left", padx=(0,8)); bar.start()
            ctk.CTkLabel(p, text="Downloading…", font=F(12), text_color=ACC_TXT).pack(side="left")
            return

        if is_act:
            return

        if is_dl:
            ctk.CTkButton(p, text="Set Active", font=F(13, True),
                          fg_color=GREEN_HV, hover_color=GREEN, text_color="#FFF",
                          corner_radius=8, height=34, width=100,
                          command=lambda: self._set(name)).pack(side="left", padx=(0,6))
            ctk.CTkButton(p, text="Delete", font=F(12),
                          fg_color="transparent", hover_color=RED_BG,
                          border_width=1, border_color=RED, text_color=RED,
                          corner_radius=8, height=34, width=72,
                          command=lambda: self._del(name)).pack(side="left")
        else:
            ctk.CTkButton(p, text="Download", font=F(13, True),
                          fg_color=ACC_HV, hover_color=ACC, text_color="#FFF",
                          corner_radius=8, height=34, width=100,
                          command=lambda: self._dl(name)).pack(side="left")

    # ── Download ──────────────────────────────────────────────────────────────

    def _dl(self, name):
        if name in self._dling: return
        self._dling.add(name)
        r = self._refs.get(name)
        if r: self._act(r["af"], name, False, False)

        def w():
            try:
                import ctranslate2
                gpu = ctranslate2.get_cuda_device_count() > 0
                d, ct = ("cuda","float16") if gpu else ("cpu","int8")
                from faster_whisper import WhisperModel
                m = WhisperModel(name, device=d, compute_type=ct,
                                 download_root=str(cfg_mod.MODELS_DIR)); del m
                self._w.after(0, lambda: self._done(name, True))
            except Exception as e:
                print(f"[mm] Download fail '{name}': {e}")
                self._w.after(0, lambda: self._done(name, False))

        threading.Thread(target=w, daemon=True).start()

    def _done(self, name, ok):
        self._dling.discard(name)
        if ok: self._pop(); return
        r = self._refs.get(name)
        if not r: return
        af = r["af"]
        for w in af.winfo_children(): w.destroy()
        ctk.CTkLabel(af, text="Failed", font=F(12), text_color=RED).pack(side="left", padx=(0,8))
        ctk.CTkButton(af, text="Retry", font=F(12, True),
                      fg_color=AMBER, hover_color=AMBER_HV, text_color="#000",
                      corner_radius=8, height=30, width=66,
                      command=lambda: self._dl(name)).pack(side="left")

    def _set(self, name):
        self._app.config["model"] = name
        cfg_mod.save_config(self._app.config)
        self._cb(name); self._pop()

    def _del(self, name):
        if name == self._app.config.get("model"):
            self._warn("Cannot delete the active model.\nSet another as active first.")
            return
        if cfg_mod.delete_model(name): self._pop()
        else: self._warn(f"Could not delete '{name}'.\nFile may be in use.")

    # ── Warn ──────────────────────────────────────────────────────────────────

    def _warn(self, msg):
        d = ctk.CTkToplevel(self._w)
        d.title("WisprWin"); d.configure(fg_color=BG)
        d.resizable(False, False); d.attributes("-topmost", True); d.grab_set()
        w, h = 420, 220
        sw, sh = d.winfo_screenwidth(), d.winfo_screenheight()
        d.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        c = ctk.CTkFrame(d, fg_color=CARD, corner_radius=12,
                         border_width=1, border_color=AMBER)
        c.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(c, text="⚠", font=F(24), text_color=AMBER).pack(pady=(20,8))
        mb = ctk.CTkFrame(c, fg_color=INPUT, corner_radius=8)
        mb.pack(fill="x", padx=16, pady=(0,12))
        ctk.CTkLabel(mb, text=msg, font=F(14), text_color=TXT,
                     justify="center", wraplength=350).pack(padx=14, pady=14)
        ctk.CTkButton(c, text="Got it", font=F(14, True),
                      fg_color=ACC_HV, hover_color=ACC, corner_radius=8,
                      height=40, command=d.destroy).pack(fill="x", padx=16, pady=(0,16))
