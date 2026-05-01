# WisprWin

<!-- banner -->

**Offline voice dictation for Windows — hold a hotkey, speak, release, and your words appear wherever your cursor is.**

No cloud. No account. No subscription. Just fast, private, local speech-to-text powered by OpenAI Whisper.

---

## ✨ Features

- 🎤 **Hold-to-dictate** — Hold your hotkey, speak, release. Text appears instantly.
- 🧠 **Multiple Whisper models** — From tiny (75 MB) to large-v3-turbo (800 MB). Pick your speed/accuracy sweet spot.
- 🌐 **99 languages** — Auto-detect or lock to a specific language.
- 🔒 **100% offline** — All processing happens locally on your machine. No data leaves your PC.
- ⚡ **GPU accelerated** — CUDA support for NVIDIA GPUs. Also works on CPU.
- 🎨 **Modern dark UI** — Beautiful CustomTkinter settings panel and Model Manager.
- 📦 **One-click model downloads** — Browse, download, and switch models from the GUI.
- 🖥️ **System tray** — Lives quietly in your tray. Right-click for settings, double-click to open.
- 🚀 **Launch at startup** — Optional Windows startup integration.
- 🔔 **Audio feedback** — Beep on start/stop recording (toggleable).
- 📋 **Clipboard restore** — Automatically restores your clipboard after pasting.

---

## 📸 Screenshots

<!-- screenshot: Model Manager -->

---

## 🧠 Supported Models

| Model | Size | Speed | Accuracy | Languages | Best For |
|---|---|---|---|---|---|
| `tiny` | 75 MB | ★★★★★ | ★★☆☆☆ | 99 | Quick notes, weak hardware |
| `base` | 145 MB | ★★★★☆ | ★★★☆☆ | 99 | Good default for most users |
| `small` | 465 MB | ★★★★☆ | ★★★★☆ | 99 | Best speed/accuracy balance |
| `medium` | 1.5 GB | ★★★☆☆ | ★★★★☆ | 99 | Higher accuracy, moderate speed |
| `large-v3` | 3 GB | ★★☆☆☆ | ★★★★★ | 99 | Maximum accuracy, slow on CPU |
| **`large-v3-turbo`** | **800 MB** | **★★★★☆** | **★★★★★** | **99** | **Best overall — recommended** |
| `distil-large-v2` | 750 MB | ★★★★★ | ★★★★☆ | English only | Fast + accurate for English |
| `distil-large-v3` | 750 MB | ★★★★★ | ★★★★★ | English only | Best English-only model |

---

## 🚀 Installation

### Option 1: Download the .exe (easiest)

1. Go to [Releases](../../releases) and download `WisprWin.exe`
2. Run it — no installation needed
3. Pick a model from the Model Manager and start dictating

### Option 2: Run from source

```bash
# Clone the repo
git clone https://github.com/yourname/WisprWin.git
cd WisprWin

# Run setup (creates venv, installs PyTorch + deps)
setup.bat

# Start the app
start_wispr.bat
```

**Requirements:**
- Windows 10 or 11
- Python 3.12+
- NVIDIA GPU (optional, for CUDA acceleration)

---

## 🎯 How to Use

### 1. Install & pick a model
Run the app → right-click tray icon → Settings → Manage Models → Download a model

### 2. Set your hotkey
Default: `Right Alt + .` — change it in Settings

### 3. Dictate!
Hold your hotkey → speak → release → text appears at your cursor ✨

---

## 🏗️ Building from Source

To create a standalone `.exe`:

```bash
# Make sure you've run setup.bat first
build.bat
```

This produces `dist/WisprWin.exe` — a single portable executable.

---

## 📁 Project Structure

```
WisprWin/
├── wisprwin/
│   ├── main.py              # Entry point — tray, hotkeys, orchestration
│   ├── recorder.py          # Microphone capture (sounddevice)
│   ├── transcriber.py       # Whisper transcription (faster-whisper)
│   ├── injector.py          # Clipboard paste into active window
│   ├── settings.py          # Config load/save, Windows registry
│   ├── make_icons.py        # Tray icon generation (Pillow)
│   ├── requirements.txt     # Python dependencies
│   ├── assets/              # Generated tray icons
│   └── ui/
│       ├── settings_window.py   # CustomTkinter settings panel
│       └── model_manager.py     # Model download/manage UI
├── setup.bat                # First-time setup script
├── start_wispr.bat          # Silent launcher
├── build.bat                # PyInstaller build script
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines

- Don't modify `recorder.py`, `transcriber.py`, or `injector.py` unless fixing bugs
- Keep the app fully offline — no cloud APIs or telemetry
- Test on both Windows 10 and Windows 11
- Follow the existing code style

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for people who think faster than they type.
</p>
