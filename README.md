# 🚀 All-in-One AI Ad Generator (Windows 11)

A complete desktop application that combines multiple open-source AI models to
generate product advertisements from **text** and **images**. Built with
Python + CustomTkinter and the Hugging Face `diffusers` ecosystem.

```
AI_Ad_Generator/
├── main.py              # App entry point (startup checks + launches UI)
├── app.py               # Alternative launcher (same as main.py)
├── config.py            # App config, model registry, ad templates
├── requirements.txt     # Python dependencies
├── install.bat          # One-click installer (venv + deps + torch CUDA)
├── setup.bat            # Setup wrapper (delegates to install.bat)
├── start.bat            # Launch the application
├── build.bat            # Build a standalone .exe via PyInstaller
├── core/                # Generation + processing engine
│   ├── model_manager.py     # Download / load / unload models
│   ├── prompt_generator.py  # Optimized ad-prompt builder
│   ├── background_remover.py# U2Net background removal
│   ├── image_editor.py      # Resize / text overlay / enhance
│   ├── text_to_video.py     # ZeroScope / CogVideoX
│   ├── image_to_video.py    # Stable Video Diffusion / AnimateDiff
│   └── video_editor.py      # Cut, text, music, combine, loop, speed
├── ui/                  # CustomTkinter front-end
│   ├── main_window.py       # Window, header, tabview, status bar
│   ├── text_to_video_tab.py # Text → Video generation tab
│   ├── image_to_video_tab.py# Image → Video generation tab
│   ├── prompt_tab.py        # Prompt generator tab
│   ├── editor_tab.py        # Video editor tab
│   ├── settings_tab.py      # System info + model manager tab
│   └── styles.py            # Colors & fonts theme
├── models/              # Downloaded model weights (created at runtime)
├── outputs/             # Generated videos (created at runtime)
├── temp/                # Intermediate files (created at runtime)
└── assets/              # icon.ico, logo.png
```

## ✨ Features

| Area | Highlights |
|------|-----------|
| 📝 **Text to Video** | ZeroScope V2, CogVideoX, 5 ad templates, custom prompts, adjustable steps/guidance/frames/resolution/seed |
| 🖼 **Image to Video** | Stable Video Diffusion, AnimateDiff, auto background removal, image enhancement, motion control |
| 💡 **Prompt Generator** | 8 styles (cinematic/luxury/tech/…), batch variations, quick templates, auto negative prompts |
| ✂️ **Video Editor** | Text overlay, background music, combine videos, loop, speed adjustment |
| ⚙️ **Settings** | One-click model download, GPU/CPU auto-detect, system info, FP16 & CPU offloading |

## 🛠 Requirements

- **Windows 11** (the `.bat` launchers are Windows-only)
- **Python 3.10+** with "Add Python to PATH" checked during install
- **NVIDIA GPU with 8 GB+ VRAM** recommended (works on CPU too, just slower)

## 🚀 How to Install & Run

1. Install **Python 3.10+** from <https://www.python.org/downloads/> and make
   sure **"Add Python to PATH"** is checked.
2. Copy/clone all files into a folder named `AI_Ad_Generator`.
3. **Double-click `install.bat`** — this will:
   - Create a virtual environment (`venv`)
   - Upgrade pip
   - Install PyTorch with CUDA 12.1
   - Install all dependencies from `requirements.txt`
   - Create the `models/`, `outputs/`, `temp/`, `assets/` folders
4. **Double-click `start.bat`** to launch the app.
5. Open the **⚙️ Settings & Models** tab and **download the models** you want.
6. Start creating ads! 🎬

## ▶️ Usage

```bat
start.bat          # run the GUI
```

Or manually inside the virtual environment:

```bat
venv\Scripts\activate.bat
python main.py
```

## 📦 Build a Standalone Executable

```bat
build.bat
```

This uses PyInstaller to produce `dist/AI_Ad_Generator/AI_Ad_Generator.exe`.

## ⚠️ Notes & Tips

- The first generation for each model downloads weights (you can also use the
  in-app **Model Manager**) — ensure a good internet connection and enough disk
  space.
- `CogVideoX` needs ~16 GB VRAM; `ZeroScope` / `SVD` / `AnimateDiff` work with
  ~8 GB. On systems with less VRAM, keep **FP16** and **CPU Offloading**
  enabled in Settings.
- Generated videos are saved to `AI_Ad_Generator/outputs/` as `.mp4`.
- `os.startfile(...)` calls are Windows-specific; on other OSes the
  "Open Folder / Play" buttons won't work (the generation pipeline itself is
  cross-platform).

## 📄 License

Provided as-is for educational and personal use. Respect the licenses of the
individual models (Stable Video Diffusion, AnimateDiff, ZeroScope, CogVideoX,
etc.) before any commercial use.
