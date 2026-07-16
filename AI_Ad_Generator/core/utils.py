"""Small cross-platform helpers shared across the app."""

import os
import re
import sys
import subprocess


def open_path(path):
    """Open a file or folder with the OS default handler.

    Works on Windows (startfile), macOS (open) and Linux (xdg-open).
    Returns True on success, False otherwise.
    """
    if not path:
        return False
    path = os.path.abspath(path)
    if not os.path.exists(path):
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa: S606 - intentional OS integration
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def human_size(num_bytes):
    """Format a byte count as a human readable string, e.g. '4.2 GB'."""
    try:
        size = float(num_bytes)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def safe_slug(text, max_len=40):
    """Turn arbitrary text into a filesystem-safe slug for filenames."""
    text = re.sub(r"[^\w\s-]", "", str(text), flags=re.UNICODE)
    text = re.sub(r"[\s-]+", "_", text).strip("_").lower()
    return (text or "item")[:max_len]


def ensure_dir(path):
    """Create ``path`` (and parents) if missing; returns the path."""
    os.makedirs(path, exist_ok=True)
    return path
