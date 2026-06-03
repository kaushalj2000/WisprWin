"""
injector.py — Paste text into the currently focused window.

Strategy:
  1. Save existing clipboard (text only) via win32clipboard
  2. Copy transcribed text to clipboard via win32clipboard
  3. Wait for hotkey modifiers to release
  4. Send Ctrl+V into the focused text field
  5. Restore original clipboard

win32clipboard is used directly to eliminate race conditions and
settle-time uncertainty that come with pyperclip.
"""

import time

import keyboard
import pyautogui

try:
    import win32clipboard
    import win32con
    _HAS_WIN32CLIP = True
except ImportError:
    _HAS_WIN32CLIP = False
    import pyperclip

_CLIPBOARD_SETTLE = 0.02
_PASTE_SETTLE = 0.25

pyautogui.PAUSE = 0


def _get_clipboard_text() -> str:
    """Return current clipboard text, or '' on failure."""
    if not _HAS_WIN32CLIP:
        try:
            return pyperclip.paste() or ""
        except Exception:
            return ""
    try:
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) or ""
        except TypeError:
            data = ""
        win32clipboard.CloseClipboard()
        return data
    except Exception:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
        return ""


def _set_clipboard_text(text: str) -> None:
    """Set clipboard text synchronously."""
    if not _HAS_WIN32CLIP:
        pyperclip.copy(text)
        return
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        win32clipboard.CloseClipboard()
    except Exception:
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
        raise


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

    original = _get_clipboard_text() if restore_clipboard else ""

    try:
        _set_clipboard_text(text)
    except Exception as e:
        print(f"[injector] Failed to copy to clipboard: {e}")
        return

    time.sleep(_CLIPBOARD_SETTLE)

    # Wait for physical modifiers held by the user to release so
    # they don't interfere with Ctrl+V.
    timeout = time.time() + 2.0
    while time.time() < timeout:
        if (
            not keyboard.is_pressed("alt")
            and not keyboard.is_pressed("right alt")
            and not keyboard.is_pressed("shift")
            and not keyboard.is_pressed("ctrl")
        ):
            break
        time.sleep(0.02)

    try:
        pyautogui.hotkey("ctrl", "v")
    except Exception as e:
        print(f"[injector] pyautogui paste failed: {e}")
        try:
            keyboard.send("ctrl+v")
        except Exception as inner:
            print(f"[injector] keyboard paste failed: {inner}")

    time.sleep(_PASTE_SETTLE)

    if restore_clipboard:
        try:
            _set_clipboard_text(original)
        except Exception:
            pass  # non-critical
