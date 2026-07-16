"""Central logging for the app.

Every subsystem logs to ``temp/app.log`` (rotating, 1 MB x 2 backups) so
problems can be diagnosed after the fact instead of vanishing with the
console window. Usage::

    from .logger import get_logger
    log = get_logger("sound")
    log.info("muxed audio into %s", out)
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import TEMP_DIR

_LOGGERS = {}
_LOG_FILE = os.path.join(TEMP_DIR, "app.log")


def get_logger(name="app"):
    """Return a named logger wired to the shared rotating app log."""
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(f"aiadgen.{name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        try:
            handler = RotatingFileHandler(
                _LOG_FILE, maxBytes=1_000_000, backupCount=2, encoding="utf-8")
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
            logger.addHandler(handler)
        except Exception:
            # Disk problems must never crash the app; fall back to console.
            logger.addHandler(logging.StreamHandler())

    _LOGGERS[name] = logger
    return logger
