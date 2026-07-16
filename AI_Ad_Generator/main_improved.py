#!/usr/bin/env python3
"""
AI Ad Generator - All-in-One Product Advertisement Creator
Combines open source AI models for text-to-video and image-to-video generation.

Features:
- Text to Video (ZeroScope, CogVideoX, ModelScope, Mochi, HunyuanVideo, LTX-Video)
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
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.logger import get_logger

log = get_logger("main")


def check_python_version() -> bool:
    """Check if Python version meets requirements.
    
    Returns:
        True if version is sufficient, False otherwise
    """
    py_version = sys.version_info
    print(f"[CHECK] Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")
    
    if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 10):
        print("[ERROR] Python 3.10+ required!")
        return False
    return True


def check_gpu() -> Optional[str]:
    """Check GPU availability and return status message.
    
    Returns:
        Status message about GPU, or None if error
    """
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            msg = f"[CHECK] GPU: {gpu_name} | VRAM: {vram:.1f} GB"
            print(msg)
            return msg
        else:
            msg = "[WARNING] No CUDA GPU detected - running on CPU (slower)"
            print(msg)
            return msg
    except ImportError:
        print("[WARNING] PyTorch not installed - run install.bat first")
        return None
    except Exception as e:
        print(f"[WARNING] Could not detect GPU: {e}")
        return None


def check_dependencies() -> bool:
    """Check critical dependencies.
    
    Returns:
        True if all dependencies are available, False otherwise
    """
    deps_ok = True
    
    # Check PyTorch
    try:
        import torch
        print("[CHECK] PyTorch: OK")
    except ImportError:
        print("[ERROR] PyTorch not installed - run install.bat")
        return False
    
    # Check CustomTkinter
    try:
        import customtkinter
        print("[CHECK] CustomTkinter: OK")
    except ImportError:
        print("[ERROR] CustomTkinter not installed - run install.bat")
        return False
    
    # Check optional but important
    optional = ["diffusers", "transformers", "PIL", "numpy"]
    for pkg in optional:
        try:
            __import__(pkg)
            print(f"[CHECK] {pkg}: OK")
        except ImportError:
            print(f"[WARNING] {pkg} not found - some features may not work")
            deps_ok = False
    
    return deps_ok


def check_requirements() -> bool:
    """Check if all basic requirements are met.
    
    Returns:
        True if all checks passed, False otherwise
    """
    print("=" * 50)
    print("  AI Ad Generator - Startup Check")
    print("=" * 50)
    print()

    # Check Python version
    if not check_python_version():
        return False

    print()

    # Check GPU
    gpu_status = check_gpu()
    if gpu_status is None:
        return False

    print()

    # Check dependencies
    if not check_dependencies():
        log.warning("Some optional dependencies missing")

    print()
    print("[OK] All critical checks passed!")
    print("=" * 50)
    return True


def main() -> None:
    """Main entry point."""
    if not check_requirements():
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass  # no console (e.g. windowed PyInstaller build)
        sys.exit(1)

    try:
        print("\nStarting AI Ad Generator...\n")
        from ui.main_window import MainWindow

        app = MainWindow()
        app.run()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}", file=sys.stderr)
        log.error("Fatal error: %s", e)
        try:
            input("Press Enter to exit...")
        except EOFError:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
