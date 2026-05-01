"""
ui/settings_window.py — compatibility shim.

The settings panel is now the main window (ui/main_window.py).
This file is kept so any external scripts importing open_settings
don't break. WisprWin itself no longer calls open_settings.
"""

# Re-export for backward compatibility
from ui.main_window import MainWindow  # noqa: F401
