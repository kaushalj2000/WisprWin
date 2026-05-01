# PRD: WisprType for Windows (Local Voice Dictation)

## Overview
A lightweight Windows desktop app that lets users hold a hotkey, speak, and have transcribed text automatically typed into any active window — 100% local, no internet, no account, no cost.

---

## Goals
- Replicate WisprType's core UX on Windows
- All processing happens on-device using local Whisper models
- Works system-wide in any app (browser, VSCode, Notepad, etc.)
- No cloud dependency, no telemetry, no login

---

## Tech Stack

| Component | Library |
|---|---|
| Language | Python 3.12+ |
| Transcription | `openai-whisper` (local inference) |
| Audio capture | `sounddevice` + `numpy` |
| Hotkey detection | `keyboard` |
| Text injection | `pyperclip` + `pyautogui` |
| System tray UI | `pystray` + `Pillow` |
| Settings storage | `json` (local config file) |
| Packaging | `PyInstaller` (single `.exe`) |

---

## Core Features

### F1 — Hold-to-Record
- User holds a configurable hotkey (default: `Right Alt`)
- Audio recording starts immediately on keydown
- Recording stops on keyup
- Visual/audio feedback: system tray icon changes color while recording, optional beep on start/stop

### F2 — Local Transcription
- Audio is passed to locally loaded Whisper model
- Transcription runs entirely on CPU (or GPU if available via CUDA)
- Result is trimmed of leading/trailing whitespace

### F3 — Auto-Paste to Active Window
- After transcription, text is copied to clipboard via `pyperclip`
- `pyautogui.hotkey("ctrl", "v")` pastes into whichever window is focused
- Previous clipboard content is restored after paste

### F4 — System Tray App
- App runs silently in the Windows system tray
- Tray icon states: Idle (white), Recording (red), Processing (yellow)
- Right-click tray menu with options: Settings, Change Model, Quit

### F5 — Settings Panel
- Simple GUI via `tkinter`
- Options:
  - **Hotkey:** user can set any key combo
  - **Whisper Model:** dropdown — Tiny, Base, Small, Medium, Large-v3
  - **Language:** Auto-detect or fixed (e.g., English, Hindi)
  - **Sound feedback:** toggle beep on/off
  - **Restore clipboard:** toggle on/off
  - **Launch at startup:** toggle Windows startup entry

### F6 — Model Management
- On first run, download selected Whisper model (~75MB–1.5GB) to `%APPDATA%\WisprWin\models\`
- Show download progress in settings panel
- Allow switching models anytime (loads new model into memory)

---

## User Flow

```
App starts → loads in system tray → loads Whisper model into memory
     ↓
User holds hotkey → tray icon turns RED → mic starts recording
     ↓
User releases hotkey → tray icon turns YELLOW → Whisper transcribes audio
     ↓
Text pasted into active window → tray icon returns to WHITE
```

---

## File Structure

```
wisprwin/
├── main.py                   # Entry point, tray + hotkey loop
├── recorder.py               # Mic capture logic (sounddevice)
├── transcriber.py            # Whisper model load + transcribe
├── injector.py               # Clipboard + pyautogui paste
├── settings.py               # Load/save config.json
├── ui/
│   └── settings_window.py   # Settings panel (tkinter)
├── assets/
│   ├── icon_idle.png
│   ├── icon_recording.png
│   └── icon_processing.png
├── config.json               # User settings (auto-created)
└── requirements.txt
```

---

## Config Schema (`config.json`)

```json
{
  "hotkey": "right alt",
  "model": "base",
  "language": "auto",
  "sound_feedback": true,
  "restore_clipboard": true,
  "launch_at_startup": false
}
```

---

## Whisper Model Reference

| Model | Size | Speed | Best For |
|---|---|---|---|
| `tiny` | 75MB | Very fast | Quick notes, weak hardware |
| `base` | 145MB | Fast | **Recommended default** |
| `small` | 465MB | Moderate | Better accuracy |
| `medium` | 1.5GB | Slower | Near-perfect accuracy |
| `large-v3` | 3GB | Slowest | Maximum accuracy |

---

## Non-Functional Requirements
- App must load in under 3 seconds after model is in memory
- Transcription latency: under 3s for `base` model on mid-range CPU
- Memory footprint: under 500MB RAM for `base` model
- Must work on Windows 10 and Windows 11
- No admin privileges required for normal use

---

## Out of Scope (v1)
- LLM-based text cleanup/polishing
- Multi-language UI
- Push-to-talk via mouse button
- Linux/macOS support
- Custom vocabulary or fine-tuning

---

## Suggested Build Order

| Step | File | Description |
|---|---|---|
| 1 | `recorder.py` | Capture mic while key held, return numpy array |
| 2 | `transcriber.py` | Load Whisper model, transcribe audio array |
| 3 | `injector.py` | Paste text, restore clipboard |
| 4 | `main.py` | Hotkey loop wiring all three (no UI yet) |
| 5 | — | Test end-to-end in terminal |
| 6 | `ui/settings_window.py` | Settings GUI (tkinter) |
| 7 | `main.py` | Add system tray with pystray |
| 8 | `settings.py` | Persist config to JSON |
| 9 | — | Package with PyInstaller into `.exe` |

---

## Starter Prompt for AI Coding Assistant

> "Build a Windows Python app from this PRD. Start with steps 1–4 (core pipeline only, no UI).
> Use `sounddevice` for mic capture, `openai-whisper` for local transcription, `keyboard` for
> hotkey detection, and `pyperclip` + `pyautogui` for text injection. The hotkey is `right alt`
> — hold to record, release to transcribe and paste into the active window."
