"""
settings.py — Config load/save and Windows startup registry management.
"""

import json
import os
import sys
import winreg
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_NAME = "WisprWin"
APPDATA_DIR = Path(os.environ.get("APPDATA", "~")) / APP_NAME
CONFIG_PATH = APPDATA_DIR / "config.json"
MODELS_DIR = APPDATA_DIR / "models"

# ---------------------------------------------------------------------------
# Default config schema (matches PRD)
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "hotkey": "right alt+.",
    "model": "large-v3-turbo",
    "language": "auto",
    "sound_feedback": True,
    "restore_clipboard": True,
    "launch_at_startup": False,
}


def ensure_dirs() -> None:
    """Create AppData dirs if they don't exist."""
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """
    Load config from disk.  Missing keys are filled from DEFAULT_CONFIG
    so that new options added later don't crash old installs.
    """
    ensure_dirs()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
            # Merge: stored values win, missing keys fall back to defaults
            merged = {**DEFAULT_CONFIG, **stored}
            return merged
        except (json.JSONDecodeError, OSError):
            pass  # corrupt file — fall through to defaults
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    """Atomically write config to disk."""
    ensure_dirs()
    tmp = CONFIG_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    tmp.replace(CONFIG_PATH)


# ---------------------------------------------------------------------------
# Windows startup registry
# ---------------------------------------------------------------------------
STARTUP_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"


def _get_launcher_path() -> str:
    """
    Returns the path to start_wispr.bat (next to wisprwin/ folder).
    Works both when running from source and when packaged as .exe.
    """
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        return sys.executable
    else:
        # Running from source — point to start_wispr.bat one level up
        here = Path(__file__).resolve().parent  # wisprwin/
        bat = here.parent / "start_wispr.bat"
        return str(bat)


def set_startup(enabled: bool) -> None:
    """Add or remove WisprWin from Windows HKCU startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_KEY,
            0,
            winreg.KEY_SET_VALUE,
        )
        if enabled:
            launcher = _get_launcher_path()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'cmd /c "{launcher}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass  # already removed
        winreg.CloseKey(key)
    except OSError as e:
        print(f"[settings] Could not modify startup registry: {e}")


def get_startup_enabled() -> bool:
    """Returns True if WisprWin is registered to launch at startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_KEY,
            0,
            winreg.KEY_READ,
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Model management helpers (used by Model Manager UI)
# ---------------------------------------------------------------------------

def get_downloaded_models() -> list[str]:
    """
    Return a list of model names that have been downloaded to MODELS_DIR.

    faster-whisper (via huggingface_hub) stores models in directories like:
      models--Systran--faster-whisper-large-v3-turbo/
    We check for these directory patterns.
    """
    ensure_dirs()
    downloaded = []

    # Known model name → HuggingFace repo mapping
    _MODEL_REPOS = {
        "tiny":             "Systran/faster-whisper-tiny",
        "base":             "Systran/faster-whisper-base",
        "small":            "Systran/faster-whisper-small",
        "medium":           "Systran/faster-whisper-medium",
        "large-v3":         "Systran/faster-whisper-large-v3",
        "large-v3-turbo":   "Systran/faster-whisper-large-v3-turbo",
        "distil-large-v2":  "Systran/faster-distil-whisper-large-v2",
        "distil-large-v3":  "Systran/faster-distil-whisper-large-v3",
    }

    for model_name, repo in _MODEL_REPOS.items():
        # huggingface_hub stores in: models--{org}--{repo_name}/
        dir_name = f"models--{repo.replace('/', '--')}"
        model_path = MODELS_DIR / dir_name
        if model_path.exists() and model_path.is_dir():
            # Check if snapshots directory has content (actual downloaded files)
            snapshots = model_path / "snapshots"
            if snapshots.exists() and any(snapshots.iterdir()):
                downloaded.append(model_name)

    return downloaded


def delete_model(model_name: str) -> bool:
    """
    Delete a downloaded model from disk.
    Returns True if successfully deleted, False otherwise.
    """
    import shutil

    _MODEL_REPOS = {
        "tiny":             "Systran/faster-whisper-tiny",
        "base":             "Systran/faster-whisper-base",
        "small":            "Systran/faster-whisper-small",
        "medium":           "Systran/faster-whisper-medium",
        "large-v3":         "Systran/faster-whisper-large-v3",
        "large-v3-turbo":   "Systran/faster-whisper-large-v3-turbo",
        "distil-large-v2":  "Systran/faster-distil-whisper-large-v2",
        "distil-large-v3":  "Systran/faster-distil-whisper-large-v3",
    }

    repo = _MODEL_REPOS.get(model_name)
    if not repo:
        return False

    dir_name = f"models--{repo.replace('/', '--')}"
    model_path = MODELS_DIR / dir_name

    if model_path.exists():
        try:
            shutil.rmtree(model_path)
            print(f"[settings] Deleted model '{model_name}' from {model_path}")
            return True
        except Exception as e:
            print(f"[settings] Failed to delete model '{model_name}': {e}")
            return False

    return False
