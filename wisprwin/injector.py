"""
injector.py — Paste text into the currently focused window.

Strategy:
  1. Optionally save existing clipboard content
  2. Copy transcribed text to clipboard
  3. Send Ctrl+V to active window via pyautogui
  4. Optionally restore original clipboard
"""

import time
import pyperclip
import pyautogui

# Give the OS a moment to settle between clipboard operations (seconds)
_CLIPBOARD_SETTLE = 0.05
_PASTE_SETTLE = 0.10


def paste_text(text: str, restore_clipboard: bool = True) -> None:
    """
    Paste *text* into whatever window currently has focus.

    Parameters
    ----------
    text : str
        The transcribed string to inject.
    restore_clipboard : bool
        If True, the original clipboard content is restored after pasting.
    """
    if not text:
        return

    # --- 1. Save current clipboard ---
    original = ""
    if restore_clipboard:
        try:
            original = pyperclip.paste()
        except Exception:
            original = ""

    # --- 2. Put our text on the clipboard ---
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(f"[injector] Failed to copy to clipboard: {e}")
        return

    time.sleep(_CLIPBOARD_SETTLE)

    # --- 3. Paste into active window ---
    # Physical modifiers held down (like Right Alt) will break Ctrl+V.
    # We wait briefly for the user to let go of them.
    import keyboard
    timeout = time.time() + 2.0
    while time.time() < timeout:
        if not keyboard.is_pressed("alt") and not keyboard.is_pressed("right alt") and not keyboard.is_pressed("shift"):
            break
        time.sleep(0.05)

    try:
        keyboard.send("ctrl+v")
    except Exception as e:
        print(f"[injector] Failed to send Ctrl+V: {e}")

    time.sleep(_PASTE_SETTLE)

    # --- 4. Restore original clipboard ---
    if restore_clipboard and original:
        try:
            pyperclip.copy(original)
        except Exception:
            pass  # non-critical — original was probably non-text
