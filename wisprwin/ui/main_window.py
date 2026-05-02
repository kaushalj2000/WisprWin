import time
import threading
import customtkinter as ctk
from typing import Callable, Optional
import settings as cfg_mod

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM SAAS PALETTE
# ══════════════════════════════════════════════════════════════════════════════
WIN_BG       = "#F3EFE6"
SIDEBAR_BG   = "#F3EFE6"
CARD_BG      = "#FFFFFF"
CARD_HOVER   = "#FAFAF9"
CONTROL_BG   = "#FFFFFF"
BORDER       = "#E6DEC8"
BORDER_HOVER = "#D4C8B0"

ACCENT       = "#4F46E5"
ACCENT_HOVER = "#4338CA"
TEXT         = "#1C1917"
TEXT_MUTED   = "#78716C"

GREEN        = "#059669"
GREEN_BG     = "#D1FAE5"
RED          = "#DC2626"
RED_BG       = "#FEE2E2"
AMBER        = "#D97706"
AMBER_BG     = "#FEF3C7"
BLUE         = "#2563EB"
BLUE_BG      = "#DBEAFE"
PURPLE       = "#7C3AED"
PURPLE_BG    = "#EDE9FE"

FONT_FAMILY  = "Segoe UI Variable Display"

def F(size, bold=False):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold" if bold else "normal")

LANGUAGES = {
    "Auto Detect": "auto", "English": "en", "Telugu": "te",
    "Hindi": "hi", "Spanish": "es", "French": "fr",
    "German": "de", "Portuguese": "pt", "Chinese": "zh",
    "Japanese": "ja", "Arabic": "ar", "Korean": "ko",
    "Russian": "ru", "Italian": "it",
}
INV_LANG = {v: k for k, v in LANGUAGES.items()}

# Models Data
MODELS = [
    {"name":"tiny", "repo":"openai/whisper-tiny", "size":"75 MB", "vram":"~1GB VRAM", "speed":"⚡ Very Fast", "acc":"🎯 Basic", "lang":"🌍 Multilingual", "desc":"Fastest model. Good for quick notes but struggles with heavy accents.", "rec":False},
    {"name":"base", "repo":"openai/whisper-base", "size":"145 MB", "vram":"~1GB VRAM", "speed":"⚡ Fast", "acc":"🎯 Fair", "lang":"🌍 Multilingual", "desc":"A good starting point for general transcription.", "rec":False},
    {"name":"small", "repo":"openai/whisper-small", "size":"465 MB", "vram":"~2GB VRAM", "speed":"⚡ Fast", "acc":"🎯 Good", "lang":"🌍 Multilingual", "desc":"The best balance of speed and accuracy for most standard machines.", "rec":False},
    {"name":"medium", "repo":"openai/whisper-medium", "size":"1.5 GB", "vram":"~4GB VRAM", "speed":"⚡ Moderate", "acc":"🎯 Very Good", "lang":"🌍 Multilingual", "desc":"High accuracy. Recommended if you have a decent dedicated GPU.", "rec":False},
    {"name":"large-v3", "repo":"openai/whisper-large-v3", "size":"3 GB", "vram":"~8GB VRAM", "speed":"⚡ Slow", "acc":"🎯 Excellent", "lang":"🌍 Multilingual", "desc":"Maximum accuracy available. Requires a high-end GPU for good speeds.", "rec":False},
    {"name":"large-v3-turbo", "repo":"openai/whisper-large-v3-turbo", "size":"800 MB", "vram":"~3GB VRAM", "speed":"⚡ Fast", "acc":"🎯 Excellent", "lang":"🌍 Multilingual", "desc":"The optimal choice. Extremely accurate and highly optimized for speed.", "rec":True},
    {"name":"distil-large-v2", "repo":"distil-whisper/large-v2", "size":"750 MB", "vram":"~3GB VRAM", "speed":"⚡ Very Fast", "acc":"🎯 Very Good", "lang":"🇺🇸 English Only", "desc":"Optimized specifically for extremely fast English transcription.", "rec":False},
    {"name":"distil-large-v3", "repo":"distil-whisper/large-v3", "size":"750 MB", "vram":"~3GB VRAM", "speed":"⚡ Very Fast", "acc":"🎯 Excellent", "lang":"🇺🇸 English Only", "desc":"The fastest state-of-the-art model for English speakers.", "rec":False},
]

class MainWindow:
    def __init__(self, root: ctk.CTk, app: "WisprApp"):
        self.root = root
        self.app = app
        
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        ctk.set_appearance_mode("light")
        
        self.root.title("WisprWin")
        self.root.geometry("1100x750")
        self.root.minsize(950, 650)
        self.root.configure(fg_color=WIN_BG)
        
        try:
            import pathlib
            ico = pathlib.Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
            self.root.iconbitmap(default=str(ico))
        except Exception:
            pass
            
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.current_frame = None
        self.frames = {}
        
        # State
        self._dling: set[str] = set()
        self._model_refs: dict = {}
        self._pulse_id = None
        self.cfg = self.app.config.copy()
        
        # UI Elements
        self._var_hotkey = ctk.StringVar(value=self.cfg.get("hotkey", "right alt + ."))
        self._var_lang = ctk.StringVar(value=INV_LANG.get(self.cfg.get("language", "auto"), "Auto Detect"))
        
        self._var_sound = ctk.BooleanVar(value=self.cfg.get("sound_feedback", True))
        self._var_startup = ctk.BooleanVar(value=self.cfg.get("launch_at_startup", False))
        self._var_clipboard = ctk.BooleanVar(value=self.cfg.get("restore_clipboard", True))

        self._build_sidebar()
        self._build_home_view()
        self._build_models_view()
        self._build_settings_view()
        
        self.select_view("home")
        
        # Callbacks
        self.app.register_status_callback(self._on_status)
        self.app.register_history_callback(self._on_history)
        
        self._var_hotkey.trace_add("write", self._save)
        self._var_lang.trace_add("write", self._save)
        self._var_sound.trace_add("write", self._save)
        self._var_startup.trace_add("write", self._save)
        self._var_clipboard.trace_add("write", self._save)

    def _save(self, *args):
        self.cfg["hotkey"] = self._var_hotkey.get()
        self.cfg["language"] = LANGUAGES.get(self._var_lang.get(), "auto")
        self.cfg["sound_feedback"] = self._var_sound.get()
        self.cfg["launch_at_startup"] = self._var_startup.get()
        self.cfg["restore_clipboard"] = self._var_clipboard.get()
        self.app.apply_settings(self.cfg)

    # ── Sidebar ─────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self.root, width=260, fg_color="transparent", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(20, 0), pady=30)
        sidebar.grid_rowconfigure(4, weight=1)
        
        title_fr = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_fr.pack(fill="x", padx=10, pady=(0, 40))
        
        try:
            from PIL import Image
            import pathlib
            logo_path = pathlib.Path(__file__).resolve().parent.parent / "assets" / "icon_idle.png"
            logo_img = ctk.CTkImage(light_image=Image.open(logo_path), size=(36, 36))
            logo = ctk.CTkLabel(title_fr, text="", image=logo_img)
        except Exception:
            logo = ctk.CTkLabel(title_fr, text="W", font=F(18, True), text_color="#FFFFFF", fg_color=ACCENT, width=36, height=36, corner_radius=18)
            
        logo.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(title_fr, text="WisprWin", font=F(20, True), text_color=TEXT).pack(side="left")

        self.nav_btns = {}
        self.nav_btns["home"] = self._nav_button(sidebar, "Dashboard", "home", "📊")
        self.nav_btns["models"] = self._nav_button(sidebar, "Model Catalog", "models", "🧠")
        self.nav_btns["settings"] = self._nav_button(sidebar, "Preferences", "settings", "⚙️")

        status_fr = ctk.CTkFrame(sidebar, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
        status_fr.pack(side="bottom", fill="x", padx=10, pady=10)
        self._lbl_status_dot = ctk.CTkLabel(status_fr, text="●", font=F(14), text_color=GREEN)
        self._lbl_status_dot.pack(side="left", padx=(20, 10), pady=16)
        self._lbl_status_txt = ctk.CTkLabel(status_fr, text="Ready to dictate", font=F(13, True), text_color=TEXT)
        self._lbl_status_txt.pack(side="left")

    def _nav_button(self, parent, text, view_name, icon):
        btn = ctk.CTkButton(parent, text=f"  {icon}   {text}", font=F(15, True), fg_color="transparent", 
                            text_color=TEXT_MUTED, hover_color=BORDER, 
                            anchor="w", height=46, corner_radius=12,
                            command=lambda: self.select_view(view_name))
        btn.pack(fill="x", padx=10, pady=4)
        return btn

    def select_view(self, view_name):
        for name, btn in self.nav_btns.items():
            if name == view_name:
                btn.configure(fg_color="#FFFFFF", text_color=TEXT)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)
        if self.current_frame:
            self.current_frame.grid_forget()
        self.current_frame = self.frames.get(view_name, self.frames["home"])
        self.current_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=30)
        if view_name == "models":
            self._pop_models()

    # ── Status ───────────────────────────────────────────────────────────────
    def _on_status(self, state: str):
        cmap = {"idle": (GREEN, "Ready to dictate"), "recording": (RED, "Recording..."), "processing": (ACCENT, "Processing...")}
        c, t = cmap.get(state, cmap["idle"])
        try:
            self._lbl_status_dot.configure(text_color=c)
            self._lbl_status_txt.configure(text=t)
        except Exception: pass
        if self._pulse_id:
            try: self.root.after_cancel(self._pulse_id)
            except: pass
            self._pulse_id = None
        if state == "recording":
            self._do_pulse(True)

    def _do_pulse(self, vis: bool):
        try:
            self._lbl_status_dot.configure(text_color=RED if vis else TEXT_MUTED)
            self._pulse_id = self.root.after(500, lambda: self._do_pulse(not vis))
        except: pass

    # ── Dashboard (Home) View ───────────────────────────────────────────────
    def _build_home_view(self):
        fr = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.frames["home"] = fr
        
        header_fr = ctk.CTkFrame(fr, fg_color="transparent")
        header_fr.pack(fill="x", pady=(0, 30))
        ctk.CTkLabel(header_fr, text="Dashboard", font=F(34, True), text_color=TEXT).pack(side="left")
        
        metrics_fr = ctk.CTkFrame(fr, fg_color="transparent")
        metrics_fr.pack(fill="x", pady=(0, 30))
        metrics_fr.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        
        self._metric_card(metrics_fr, 0, "Time Saved", "Coming soon", "+0% this week", ACCENT)
        self._metric_card(metrics_fr, 1, "Words Transcribed", "0", "Ready", GREEN)
        
        m3 = ctk.CTkFrame(metrics_fr, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        m3.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(m3, text="Active Engine", font=F(14), text_color=TEXT_MUTED).pack(anchor="w", padx=24, pady=(24, 4))
        
        self._lbl_active_model = ctk.CTkLabel(m3, text=self.cfg.get("model", "None"), font=F(22, True), text_color=TEXT)
        self._lbl_active_model.pack(anchor="w", padx=24)
        
        import ctranslate2
        is_gpu = ctranslate2.get_cuda_device_count() > 0
        gpu_txt = "⚡ GPU Accelerated" if is_gpu else "💻 CPU Mode"
        gpu_col = GREEN if is_gpu else TEXT_MUTED
        gpu_bg = GREEN_BG if is_gpu else CARD_BG
        ctk.CTkLabel(m3, text=gpu_txt, font=F(13, True), text_color=gpu_col, fg_color=gpu_bg, corner_radius=6).pack(anchor="w", padx=24, pady=(12, 24))

        bottom_fr = ctk.CTkFrame(fr, fg_color="transparent")
        bottom_fr.pack(fill="x", expand=True)
        bottom_fr.grid_columnconfigure(0, weight=2)
        bottom_fr.grid_columnconfigure(1, weight=3)
        
        config_col = ctk.CTkFrame(bottom_fr, fg_color="transparent")
        config_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        ctk.CTkLabel(config_col, text="Quick Settings", font=F(18, True), text_color=TEXT).pack(anchor="w", pady=(0, 16))
        
        hk_card = self._settings_card(config_col)
        ctk.CTkLabel(hk_card, text="Dictation Shortcut", font=F(15, True), text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkEntry(hk_card, textvariable=self._var_hotkey, font=F(14), fg_color=CONTROL_BG, border_color=BORDER, text_color=TEXT, height=40, corner_radius=8).pack(fill="x", padx=24, pady=(0, 24))

        lang_card = self._settings_card(config_col)
        ctk.CTkLabel(lang_card, text="Spoken Language", font=F(15, True), text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 4))
        
        # Custom Frame Button for right-aligned arrow
        self._lang_btn_fr = ctk.CTkFrame(lang_card, height=40, fg_color=CONTROL_BG, border_width=1, border_color=BORDER, corner_radius=8)
        self._lang_btn_fr.pack(fill="x", padx=24, pady=(0, 24))
        self._lang_btn_fr.pack_propagate(False)
        
        self._lang_btn_lbl = ctk.CTkLabel(self._lang_btn_fr, text=self._var_lang.get(), font=F(14), text_color=TEXT)
        self._lang_btn_lbl.pack(side="left", padx=12)
        
        self._lang_btn_arr = ctk.CTkLabel(self._lang_btn_fr, text="▼", font=F(12), text_color=TEXT_MUTED)
        self._lang_btn_arr.pack(side="right", padx=12)
        
        # Hover styling
        def _on_enter(e): self._lang_btn_fr.configure(border_color=TEXT_MUTED)
        def _on_leave(e): self._lang_btn_fr.configure(border_color=BORDER)
        
        self._lang_btn_fr.bind("<Enter>", _on_enter)
        self._lang_btn_fr.bind("<Leave>", _on_leave)
        
        # Create frame exactly once to avoid CTk garbage collection bugs
        self._lang_dd_frame = ctk.CTkScrollableFrame(lang_card, height=180, fg_color=CARD_BG, 
                                                     border_width=1, border_color=BORDER, corner_radius=8)
        
        for lang in list(LANGUAGES.keys()):
            b = ctk.CTkButton(self._lang_dd_frame, text=lang, font=F(14), fg_color="transparent", 
                              text_color=TEXT, hover_color=CARD_HOVER, anchor="w",
                              command=lambda val=lang: _select(val))
            b.pack(fill="x", pady=2)
            
        self._dd_is_open = False
        
        def _toggle_lang(e=None):
            if self._dd_is_open:
                self._lang_dd_frame.pack_forget()
                self._dd_is_open = False
                self._lang_btn_arr.configure(text="▼")
            else:
                self._lang_dd_frame.pack(fill="x", padx=24, pady=(0, 24))
                self._dd_is_open = True
                self._lang_btn_arr.configure(text="▲")
                
        def _select(val):
            self._var_lang.set(val)
            self._lang_btn_lbl.configure(text=val)
            if self._dd_is_open:
                self._lang_dd_frame.pack_forget()
                self._dd_is_open = False
                self._lang_btn_arr.configure(text="▼")
                
        self._lang_btn_fr.bind("<Button-1>", _toggle_lang)
        self._lang_btn_lbl.bind("<Button-1>", _toggle_lang)
        self._lang_btn_arr.bind("<Button-1>", _toggle_lang)

        activity_col = ctk.CTkFrame(bottom_fr, fg_color="transparent")
        activity_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        ctk.CTkLabel(activity_col, text="Recent Transcriptions", font=F(18, True), text_color=TEXT).pack(anchor="w", pady=(0, 16))
        
        self._history_container = self._settings_card(activity_col)
        ctk.CTkLabel(self._history_container, text="No recent transcriptions.", font=F(14), text_color=TEXT_MUTED).pack(pady=30)
        
    def _metric_card(self, parent, col, title, value, subtitle, color):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col==0 else 10, 10 if col!=2 else 0))
        ctk.CTkLabel(card, text=title, font=F(14), text_color=TEXT_MUTED).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(card, text=value, font=F(28, True), text_color=TEXT).pack(anchor="w", padx=24)
        ctk.CTkLabel(card, text=subtitle, font=F(13), text_color=color).pack(anchor="w", padx=24, pady=(8, 24))

    def _on_history(self, history: list):
        try:
            for w in self._history_container.winfo_children(): w.destroy()
            if not history:
                ctk.CTkLabel(self._history_container, text="No recent transcriptions.", font=F(14), text_color=TEXT_MUTED).pack(pady=30)
                return
            for i, item in enumerate(history):
                self._activity_item(self._history_container, item["time"], item["text"])
                if i < len(history) - 1:
                    ctk.CTkFrame(self._history_container, fg_color=BORDER, height=1).pack(fill="x", padx=24)
        except Exception as e: 
            print(f"History update err: {e}")

    def _activity_item(self, parent, timestamp, text):
        import time
        import pyperclip
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", padx=24, pady=16)
        
        top_fr = ctk.CTkFrame(fr, fg_color="transparent")
        top_fr.pack(fill="x")
        
        t_str = time.strftime("%I:%M %p", time.localtime(timestamp))
        words = len(text.split())
        
        ctk.CTkLabel(top_fr, text=t_str, font=F(12, True), text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(top_fr, text=f"{words} words", font=F(12), text_color=TEXT_MUTED).pack(side="left", padx=10)
        
        def _copy():
            pyperclip.copy(text)
        
        btn = ctk.CTkButton(top_fr, text="📋 Copy", font=F(11, True), width=50, height=24, corner_radius=6, fg_color="transparent", text_color=TEXT_MUTED, hover_color=BORDER, border_width=1, border_color=BORDER, command=_copy)
        btn.pack(side="right")
        
        ctk.CTkLabel(fr, text=f'"{text}"', font=F(14), text_color=TEXT, justify="left", wraplength=400).pack(anchor="w", pady=(8, 0))

    # ── Models View ────────────────────────────────────────────────────────
    def _build_models_view(self):
        fr = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.frames["models"] = fr
        
        header_fr = ctk.CTkFrame(fr, fg_color="transparent")
        header_fr.pack(fill="x", pady=(0, 30))
        
        title_fr = ctk.CTkFrame(header_fr, fg_color="transparent")
        title_fr.pack(side="left")
        ctk.CTkLabel(title_fr, text="Model Catalog", font=F(34, True), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title_fr, text="Download and manage offline transcription engines.", font=F(15), text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        
        ctk.CTkButton(header_fr, text="Refresh", font=F(14, True), text_color=TEXT, width=100, height=40, corner_radius=10, fg_color=CARD_BG, hover_color=CARD_HOVER, border_width=1, border_color=BORDER, command=self._pop_models).pack(side="right")

        self._models_container = ctk.CTkFrame(fr, fg_color="transparent")
        self._models_container.pack(fill="both", expand=True)

    def _pop_models(self):
        for w in self._models_container.winfo_children(): w.destroy()
        self._model_refs.clear()
        
        dl = set(cfg_mod.get_downloaded_models())
        act = self.cfg.get("model", "base")
        
        for m in MODELS:
            name = m["name"]
            self._model_card(self._models_container, m, name == act, name in dl)

    def _model_card(self, parent, m, is_active, is_downloaded):
        card = self._settings_card(parent)
        card.grid_columnconfigure(1, weight=1)
        
        info_fr = ctk.CTkFrame(card, fg_color="transparent")
        info_fr.grid(row=0, column=1, sticky="w", padx=30, pady=24)
        
        title_row = ctk.CTkFrame(info_fr, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text=m["repo"], font=F(18, True), text_color=TEXT).pack(side="left")
        
        if m.get("rec"):
            ctk.CTkLabel(title_row, text="Recommended", font=F(12, True), text_color=ACCENT, fg_color="#E0E7FF", corner_radius=8).pack(side="left", padx=(14, 0))
            
        tags_row = ctk.CTkFrame(info_fr, fg_color="transparent")
        tags_row.pack(anchor="w", pady=(8, 8))
        
        def _tag(p, text, color, bg):
            ctk.CTkLabel(p, text=f" {text} ", font=F(11, True), text_color=color, fg_color=bg, corner_radius=6).pack(side="left", padx=(0, 8))
            
        _tag(tags_row, m["speed"], BLUE, BLUE_BG)
        _tag(tags_row, m["acc"], GREEN, GREEN_BG)
        _tag(tags_row, m["lang"], PURPLE, PURPLE_BG)
        _tag(tags_row, m["vram"], AMBER, AMBER_BG)
        _tag(tags_row, m["size"], TEXT_MUTED, BORDER)

        ctk.CTkLabel(info_fr, text=m["desc"], font=F(14), text_color=TEXT_MUTED).pack(anchor="w")
        
        act_fr = ctk.CTkFrame(card, fg_color="transparent")
        act_fr.grid(row=0, column=2, sticky="e", padx=30, pady=24)
        
        self._model_refs[m["name"]] = act_fr
        self._update_model_action(m["name"], is_active, is_downloaded)

    def _update_model_action(self, name, is_active, is_downloaded):
        af = self._model_refs.get(name)
        if not af: return
        for w in af.winfo_children(): w.destroy()
        
        if name in self._dling:
            ctk.CTkLabel(af, text="Downloading...", font=F(14, True), text_color=ACCENT).pack(side="right")
            return

        if is_active:
            ctk.CTkLabel(af, text="✓ Active", font=F(15, True), text_color=GREEN).pack(side="right")
        elif is_downloaded:
            ctk.CTkButton(af, text="Delete", font=F(14, True), width=80, height=40, corner_radius=10, fg_color="transparent", text_color=RED, border_width=1, border_color=BORDER, hover_color=RED_BG, command=lambda: self._del_model(name)).pack(side="left", padx=(0, 12))
            ctk.CTkButton(af, text="Set Active", font=F(14, True), text_color=TEXT, width=110, height=40, corner_radius=10, fg_color=CARD_BG, border_width=1, border_color=BORDER, hover_color=BORDER_HOVER, command=lambda: self._set_model(name)).pack(side="left")
        else:
            ctk.CTkButton(af, text="Download", font=F(14, True), width=110, height=40, corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF", command=lambda: self._dl_model(name)).pack(side="left")

    def _dl_model(self, name):
        self._dling.add(name)
        self._update_model_action(name, False, False)
        def w():
            try:
                import ctranslate2
                gpu = ctranslate2.get_cuda_device_count() > 0
                d, ct = ("cuda","float16") if gpu else ("cpu","int8")
                from faster_whisper import WhisperModel
                m = WhisperModel(name, device=d, compute_type=ct, download_root=str(cfg_mod.MODELS_DIR))
                del m
                self.root.after(0, lambda: self._done_dl(name, True))
            except Exception as e:
                print(f"Download fail: {e}")
                self.root.after(0, lambda: self._done_dl(name, False))
        threading.Thread(target=w, daemon=True).start()

    def _done_dl(self, name, ok):
        self._dling.discard(name)
        self._pop_models()

    def _set_model(self, name):
        self.cfg["model"] = name
        self.app.apply_settings(self.cfg)
        self._lbl_active_model.configure(text=name)
        self._pop_models()

    def _del_model(self, name):
        if name == self.cfg.get("model"):
            return # Cannot delete active
        cfg_mod.delete_model(name)
        self._pop_models()

    # ── Preferences View ───────────────────────────────────────────────────
    def _build_settings_view(self):
        fr = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.frames["settings"] = fr
        
        header_fr = ctk.CTkFrame(fr, fg_color="transparent")
        header_fr.pack(fill="x", pady=(0, 30))
        ctk.CTkLabel(header_fr, text="Preferences", font=F(34, True), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(header_fr, text="Manage application behavior and hardware optimization.", font=F(15), text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(fr, text="Application Behavior", font=F(16, True), text_color=TEXT).pack(anchor="w", pady=(10, 10), padx=4)
        
        behav_card = ctk.CTkFrame(fr, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        behav_card.pack(fill="x", pady=(0, 20))
        
        self._toggle_row(behav_card, "Sound Feedback", "Play a subtle beep when starting or stopping recording.", self._var_sound, is_first=True)
        ctk.CTkFrame(behav_card, fg_color=BORDER, height=1).pack(fill="x", padx=24)
        self._toggle_row(behav_card, "Restore Clipboard", "Restore your original clipboard contents after pasting the transcript.", self._var_clipboard)
        ctk.CTkFrame(behav_card, fg_color=BORDER, height=1).pack(fill="x", padx=24)
        self._toggle_row(behav_card, "Launch at Startup", "Automatically start WisprWin in the background when you log in.", self._var_startup, is_last=True)

        ctk.CTkLabel(fr, text="Hardware & Performance", font=F(16, True), text_color=TEXT).pack(anchor="w", pady=(10, 10), padx=4)
        
        hw_card = self._settings_card(fr)
        hw_card.grid_columnconfigure(0, weight=1)
        
        hw_info = ctk.CTkFrame(hw_card, fg_color="transparent")
        hw_info.grid(row=0, column=0, sticky="w", padx=30, pady=24)
        
        title_row = ctk.CTkFrame(hw_info, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text="CUDA Acceleration", font=F(18, True), text_color=TEXT).pack(side="left")
        
        import ctranslate2
        is_gpu = ctranslate2.get_cuda_device_count() > 0
        txt, color, bg = ("Active", GREEN, GREEN_BG) if is_gpu else ("Inactive", TEXT_MUTED, CARD_BG)
        ctk.CTkLabel(title_row, text=txt, font=F(12, True), text_color=color, fg_color=bg, corner_radius=8).pack(side="left", padx=(14, 0))
        
        desc = "Your GPU is handling inference." if is_gpu else "Running on CPU. Install CUDA for 10x faster transcriptions."
        ctk.CTkLabel(hw_info, text=desc, font=F(14), text_color=TEXT_MUTED).pack(anchor="w", pady=(8, 0))

    def _toggle_row(self, parent, title, subtitle, variable, is_first=False, is_last=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        pt = 24 if is_first else 16
        pb = 24 if is_last else 16
        row.pack(fill="x", padx=30, pady=(pt, pb))
        
        info_fr = ctk.CTkFrame(row, fg_color="transparent")
        info_fr.pack(side="left")
        ctk.CTkLabel(info_fr, text=title, font=F(16, True), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(info_fr, text=subtitle, font=F(13), text_color=TEXT_MUTED).pack(anchor="w", pady=(2, 0))
        
        sw = ctk.CTkSwitch(row, text="", variable=variable, progress_color=ACCENT, fg_color="#E6DEC8", button_color="#F3EFE6", button_hover_color="#E8E2D2", width=50)
        sw.pack(side="right")

    def _settings_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=8)
        return card
