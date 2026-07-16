"""Ensure moviepy / pydub can find an ffmpeg binary.

The base app already depends on `imageio-ffmpeg`, which bundles a static
ffmpeg. moviepy and pydub normally expect `ffmpeg` on PATH, so we point them
at the bundled binary when present. This keeps audio muxing / synthesis
working with no extra system install.
"""

import os


def configure_ffmpeg():
    """Locate the bundled ffmpeg and configure moviepy + pydub to use it."""
    exe = None
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        exe = None

    if not exe or not os.path.exists(exe):
        return None

    os.environ.setdefault("IMAGEIO_FFMPEG_EXE", exe)
    os.environ.setdefault("FFMPEG_BINARY", exe)

    # Configure moviepy if/when it is imported later.
    try:
        from moviepy.config import change_settings
        change_settings({"FFMPEG_BINARY": exe})
    except Exception:
        os.environ["FFMPEG_BINARY"] = exe

    # pydub reads this attribute at export time.
    try:
        from pydub import AudioSegment
        AudioSegment.converter = exe
        AudioSegment.ffmpeg = exe
        AudioSegment.ffprobe = exe.replace("ffmpeg", "ffprobe") \
            if "ffmpeg" in exe else exe
    except Exception:
        pass

    return exe
