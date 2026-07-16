#!/usr/bin/env python3
"""
AI Ad Generator - All-in-One Product Advertisement Creator
Combines open source AI models for text-to-video and image-to-video generation.

Features:
- Text to Video (ZeroScope, CogVideoX)
- Image to Video (Stable Video Diffusion, AnimateDiff)
- AI Prompt Generator optimized for product ads
- Background Removal
- Video Editor (text overlay, music, combine, loop, speed)
- Model Manager with one-click download

Requirements:
- Windows 11
- Python 3.10+
- NVIDIA GPU with 8GB+ VRAM (recommended)
- Works on CPU too (slower)
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_requirements():
    """Check if basic requirements are met"""
    print("=" * 50)
    print("  AI Ad Generator - Startup Check")
    print("=" * 50)

    # Check Python version
    py_version = sys.version_info
    print(f"\n[CHECK] Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version.major < 3 or py_version.minor < 10:
        print("[WARNING] Python 3.10+ recommended!")

    # Check GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"[CHECK] GPU: {gpu_name}")
            print(f"[CHECK] VRAM: {vram:.1f} GB")
        else:
            print("[WARNING] No CUDA GPU detected - running on CPU (slower)")
    except ImportError:
        print("[WARNING] PyTorch not installed - run install.bat first")
        return False

    # Check customtkinter
    try:
        import customtkinter
        print("[CHECK] CustomTkinter: OK")
    except ImportError:
        print("[ERROR] CustomTkinter not installed - run install.bat")
        return False

    print("\n[OK] All checks passed!")
    print("=" * 50)
    return True


def main():
    """Main entry point"""
    if not check_requirements():
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass  # no console (e.g. windowed PyInstaller build)
        sys.exit(1)

    print("\nStarting AI Ad Generator...")

    from ui.main_window import MainWindow

    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
