"""
Centralized logging for Pharaoh Engine.

Writes rotating logs to ``saves/logs/pharaoh.log`` and mirrors important
messages to stdout. Logging must never crash the game, so every setup step
is defensive: on failure we degrade gracefully to stdout-only (or nothing).
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parents[2] / "saves" / "logs"
_LOG_FILE = _LOG_DIR / "pharaoh.log"
_MAX_BYTES = 1_000_000      # ~1 MB per file
_BACKUP_COUNT = 3           # keep pharaoh.log.1 .. .3

_configured = False


def _configure() -> None:
    """Attach handlers to the root 'pharaoh' logger exactly once."""
    global _configured
    if _configured:
        return

    root = logging.getLogger("pharaoh")
    root.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s [%(name)s] %(message)s")

    # File handler (best effort — storage may be read-only on some devices)
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            str(_LOG_FILE), maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT, encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception:
        pass

    # Console handler (INFO and above so debug noise stays out of stdout)
    try:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(fmt)
        root.addHandler(sh)
    except Exception:
        pass

    _configured = True


def get_logger(name: str = "app") -> logging.Logger:
    """Return a namespaced child of the 'pharaoh' root logger."""
    _configure()
    return logging.getLogger(f"pharaoh.{name}")
