import customtkinter as ctk

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM SAAS PALETTE (WARM CREAM / LIGHT MODE)
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

FONT_FAMILY  = "Segoe UI Variable Display"

def F(size, bold=False):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight="bold" if bold else "normal")

class PremiumSaaSUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        ctk.set_widget_scaling(1.0)
        ctk.set_window_scaling(1.0)
        ctk.set_appearance_mode("light")
        
        self.title("WisprWin")
        self.geometry("1100x750")
        self.minsize(950, 650)
        self.configure(fg_color=WIN_BG)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.current_frame = None
        self.frames = {}
        
        self._build_sidebar()
        self._build_home_view()
        self._build_models_view()
        self._build_settings_view()
        
        self.select_view("home")

    # ── Sidebar Navigation ──────────────────────────────────────────────────
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=260, fg_color="transparent", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(20, 0), pady=30)
        sidebar.grid_rowconfigure(4, weight=1)
        
        title_fr = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_fr.pack(fill="x", padx=10, pady=(0, 40))
        
        logo = ctk.CTkLabel(title_fr, text="W", font=F(18, True), text_color="#FFFFFF", fg_color=ACCENT, width=36, height=36, corner_radius=18)
        logo.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(title_fr, text="WisprWin", font=F(20, True), text_color=TEXT).pack(side="left")

        self.nav_btns = {}
        self.nav_btns["home"] = self._nav_button(sidebar, "Dashboard", "home", "📊")
        self.nav_btns["models"] = self._nav_button(sidebar, "Model Catalog", "models", "🧠")
        self.nav_btns["settings"] = self._nav_button(sidebar, "Preferences", "settings", "⚙️")

        status_fr = ctk.CTkFrame(sidebar, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
        status_fr.pack(side="bottom", fill="x", padx=10, pady=10)
        ctk.CTkLabel(status_fr, text="●", font=F(14), text_color=GREEN).pack(side="left", padx=(20, 10), pady=16)
        ctk.CTkLabel(status_fr, text="Ready to dictate", font=F(13, True), text_color=TEXT).pack(side="left")

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

    # ── Dashboard (Home) View ───────────────────────────────────────────────
    def _build_home_view(self):
        fr = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["home"] = fr
        
        header_fr = ctk.CTkFrame(fr, fg_color="transparent")
        header_fr.pack(fill="x", pady=(0, 30))
        ctk.CTkLabel(header_fr, text="Dashboard", font=F(34, True), text_color=TEXT).pack(side="left")
        
        metrics_fr = ctk.CTkFrame(fr, fg_color="transparent")
        metrics_fr.pack(fill="x", pady=(0, 30))
        metrics_fr.grid_columnconfigure((0, 1, 2), weight=1, uniform="col")
        
        self._metric_card(metrics_fr, 0, "Time Saved", "4h 23m", "+12% this week", ACCENT)
        self._metric_card(metrics_fr, 1, "Words Transcribed", "12,450", "High accuracy", GREEN)
        
        m3 = ctk.CTkFrame(metrics_fr, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        m3.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(m3, text="Active Engine", font=F(14), text_color=TEXT_MUTED).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(m3, text="large-v3-turbo", font=F(22, True), text_color=TEXT).pack(anchor="w", padx=24)
        ctk.CTkLabel(m3, text="⚡ GPU Accelerated", font=F(13, True), text_color=GREEN, fg_color=GREEN_BG, corner_radius=6).pack(anchor="w", padx=24, pady=(12, 24))

        bottom_fr = ctk.CTkFrame(fr, fg_color="transparent")
        bottom_fr.pack(fill="x", expand=True)
        bottom_fr.grid_columnconfigure(0, weight=2)
        bottom_fr.grid_columnconfigure(1, weight=3)
        
        config_col = ctk.CTkFrame(bottom_fr, fg_color="transparent")
        config_col.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        ctk.CTkLabel(config_col, text="Quick Settings", font=F(18, True), text_color=TEXT).pack(anchor="w", pady=(0, 16))
        
        hk_card = self._settings_card(config_col)
        ctk.CTkLabel(hk_card, text="Dictation Shortcut", font=F(15, True), text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkEntry(hk_card, font=F(14), fg_color=CONTROL_BG, border_color=BORDER, text_color=TEXT, height=40, corner_radius=8, placeholder_text="Right Alt + .").pack(fill="x", padx=24, pady=(0, 24))

        lang_card = self._settings_card(config_col)
        ctk.CTkLabel(lang_card, text="Spoken Language", font=F(15, True), text_color=TEXT).pack(anchor="w", padx=24, pady=(20, 4))
        ctk.CTkOptionMenu(lang_card, values=["Auto Detect", "English", "Spanish"], font=F(14), fg_color=CONTROL_BG, text_color=TEXT, button_color=CONTROL_BG, button_hover_color=BORDER, dropdown_fg_color=CARD_BG, dropdown_text_color=TEXT, corner_radius=8, height=40).pack(fill="x", padx=24, pady=(0, 24))

        activity_col = ctk.CTkFrame(bottom_fr, fg_color="transparent")
        activity_col.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        ctk.CTkLabel(activity_col, text="Recent Transcriptions", font=F(18, True), text_color=TEXT).pack(anchor="w", pady=(0, 16))
        
        act_card = self._settings_card(activity_col)
        self._activity_item(act_card, "Just now", "The new UI is looking significantly better...", "12 words")
        self._divider(act_card)
        self._activity_item(act_card, "2 hours ago", "Make sure to push the latest commit to the repo.", "10 words")
        self._divider(act_card)
        self._activity_item(act_card, "Yesterday", "Meeting notes: Discussed the new premium SaaS direction and metrics integration.", "14 words")
        
    def _metric_card(self, parent, col, title, value, subtitle, color):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        card.grid(row=0, column=col, sticky="nsew", padx=(0 if col==0 else 10, 10 if col!=2 else 0))
        ctk.CTkLabel(card, text=title, font=F(14), text_color=TEXT_MUTED).pack(anchor="w", padx=24, pady=(24, 4))
        ctk.CTkLabel(card, text=value, font=F(28, True), text_color=TEXT).pack(anchor="w", padx=24)
        ctk.CTkLabel(card, text=subtitle, font=F(13), text_color=color).pack(anchor="w", padx=24, pady=(8, 24))

    def _activity_item(self, parent, time, text, meta):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", padx=24, pady=16)
        
        top_fr = ctk.CTkFrame(fr, fg_color="transparent")
        top_fr.pack(fill="x")
        ctk.CTkLabel(top_fr, text=time, font=F(12, True), text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(top_fr, text=meta, font=F(12), text_color=TEXT_MUTED).pack(side="right")
        ctk.CTkLabel(fr, text=f'"{text}"', font=F(14), text_color=TEXT, justify="left", wraplength=400).pack(anchor="w", pady=(8, 0))

    def _divider(self, parent):
        ctk.CTkFrame(parent, fg_color=BORDER, height=1).pack(fill="x", padx=24)


    # ── Models View ────────────────────────────────────────────────────────
    def _build_models_view(self):
        fr = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["models"] = fr
        
        header_fr = ctk.CTkFrame(fr, fg_color="transparent")
        header_fr.pack(fill="x", pady=(0, 30))
        
        title_fr = ctk.CTkFrame(header_fr, fg_color="transparent")
        title_fr.pack(side="left")
        ctk.CTkLabel(title_fr, text="Model Catalog", font=F(34, True), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(title_fr, text="Download and manage offline transcription engines.", font=F(15), text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 0))
        
        ctk.CTkButton(header_fr, text="Refresh", font=F(14, True), text_color=TEXT, width=100, height=40, corner_radius=10, fg_color=CARD_BG, hover_color=CARD_HOVER, border_width=1, border_color=BORDER).pack(side="right")

        self._model_card(fr, "large-v3-turbo", "800 MB", is_active=True, is_downloaded=True, is_rec=True)
        self._model_card(fr, "base", "145 MB", is_active=False, is_downloaded=True, is_rec=False)
        self._model_card(fr, "medium", "1.5 GB", is_active=False, is_downloaded=False, is_rec=False)

    def _model_card(self, parent, name, size, is_active, is_downloaded, is_rec):
        card = self._settings_card(parent)
        card.grid_columnconfigure(1, weight=1)
        
        info_fr = ctk.CTkFrame(card, fg_color="transparent")
        info_fr.grid(row=0, column=1, sticky="w", padx=30, pady=24)
        
        title_row = ctk.CTkFrame(info_fr, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text=name, font=F(18, True), text_color=TEXT).pack(side="left")
        
        if is_rec:
            ctk.CTkLabel(title_row, text="Recommended", font=F(12, True), text_color=ACCENT, fg_color="#E0E7FF", corner_radius=8).pack(side="left", padx=(14, 0))
            
        ctk.CTkLabel(info_fr, text=f"Size: {size} • 99 Languages • Requires 2GB RAM", font=F(14), text_color=TEXT_MUTED).pack(anchor="w", pady=(8, 0))
        
        act_fr = ctk.CTkFrame(card, fg_color="transparent")
        act_fr.grid(row=0, column=2, sticky="e", padx=30, pady=24)
        
        if is_active:
            ctk.CTkLabel(act_fr, text="✓ Active", font=F(15, True), text_color=GREEN).pack(side="right")
        elif is_downloaded:
            ctk.CTkButton(act_fr, text="Delete", font=F(14, True), width=80, height=40, corner_radius=10, fg_color="transparent", text_color=RED, border_width=1, border_color=BORDER, hover_color=RED_BG).pack(side="left", padx=(0, 12))
            ctk.CTkButton(act_fr, text="Set Active", font=F(14, True), text_color=TEXT, width=110, height=40, corner_radius=10, fg_color=CARD_BG, border_width=1, border_color=BORDER, hover_color=BORDER_HOVER).pack(side="left")
        else:
            ctk.CTkButton(act_fr, text="Download", font=F(14, True), width=110, height=40, corner_radius=10, fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#FFFFFF").pack(side="left")

    # ── Preferences View ───────────────────────────────────────────────────
    def _build_settings_view(self):
        fr = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.frames["settings"] = fr
        
        header_fr = ctk.CTkFrame(fr, fg_color="transparent")
        header_fr.pack(fill="x", pady=(0, 30))
        ctk.CTkLabel(header_fr, text="Preferences", font=F(34, True), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(header_fr, text="Manage application behavior and hardware optimization.", font=F(15), text_color=TEXT_MUTED).pack(anchor="w", pady=(4, 0))

        # Behavior Settings (List Group Card)
        ctk.CTkLabel(fr, text="Application Behavior", font=F(16, True), text_color=TEXT).pack(anchor="w", pady=(10, 10), padx=4)
        
        behav_card = ctk.CTkFrame(fr, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        behav_card.pack(fill="x", pady=(0, 20))
        
        self._toggle_row(behav_card, "Sound Feedback", "Play a subtle beep when starting or stopping recording.", True, is_first=True)
        self._divider(behav_card)
        self._toggle_row(behav_card, "Restore Clipboard", "Restore your original clipboard contents after pasting the transcript.", True)
        self._divider(behav_card)
        self._toggle_row(behav_card, "Launch at Startup", "Automatically start WisprWin in the background when you log in.", False, is_last=True)

        # Hardware Settings
        ctk.CTkLabel(fr, text="Hardware & Performance", font=F(16, True), text_color=TEXT).pack(anchor="w", pady=(10, 10), padx=4)
        
        hw_card = self._settings_card(fr)
        hw_card.grid_columnconfigure(0, weight=1)
        
        hw_info = ctk.CTkFrame(hw_card, fg_color="transparent")
        hw_info.grid(row=0, column=0, sticky="w", padx=30, pady=24)
        
        title_row = ctk.CTkFrame(hw_info, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text="CUDA Acceleration", font=F(18, True), text_color=TEXT).pack(side="left")
        ctk.CTkLabel(title_row, text="Active", font=F(12, True), text_color=GREEN, fg_color=GREEN_BG, corner_radius=8).pack(side="left", padx=(14, 0))
        
        ctk.CTkLabel(hw_info, text="Your GPU is currently handling all AI inference, resulting in 10x faster transcriptions.", font=F(14), text_color=TEXT_MUTED).pack(anchor="w", pady=(8, 0))
        
        ctk.CTkButton(hw_card, text="Manage Drivers", font=F(14, True), text_color=TEXT, width=130, height=40, corner_radius=10, fg_color="transparent", hover_color=BORDER_HOVER, border_width=1, border_color=BORDER).grid(row=0, column=1, sticky="e", padx=30, pady=24)

    def _toggle_row(self, parent, title, subtitle, default_state, is_first=False, is_last=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        pt = 24 if is_first else 16
        pb = 24 if is_last else 16
        row.pack(fill="x", padx=30, pady=(pt, pb))
        
        info_fr = ctk.CTkFrame(row, fg_color="transparent")
        info_fr.pack(side="left")
        ctk.CTkLabel(info_fr, text=title, font=F(16, True), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(info_fr, text=subtitle, font=F(13), text_color=TEXT_MUTED).pack(anchor="w", pady=(2, 0))
        
        # Removed custom switch_width/height as they break CTk's circle rendering.
        # Changed button_color to the cream background color for better contrast.
        sw = ctk.CTkSwitch(row, text="", progress_color=ACCENT, fg_color="#E6DEC8", button_color="#F3EFE6", button_hover_color="#E8E2D2", width=50)
        sw.pack(side="right")
        if default_state:
            sw.select()

    # ── Helpers ────────────────────────────────────────────────────────────
    def _settings_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
        card.pack(fill="x", pady=8)
        return card

if __name__ == "__main__":
    app = PremiumSaaSUI()
    app.mainloop()
