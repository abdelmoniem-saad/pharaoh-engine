"""
App-level preferences that must survive restarts (tutorial flags, hints, …).

Replaces direct ``page.client_storage`` usage, which is unavailable in some
Flet runtimes and crashed the app on startup. Preferences are stored in a
small atomic JSON file under ``saves/`` so they work identically on desktop,
mobile, and restricted environments.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from src.utils.storage import save_directory

_FILE = save_directory() / "app_prefs.json"

_lock = threading.Lock()
_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    if _cache is None:
        try:
            if _FILE.exists():
                _cache = json.loads(_FILE.read_text(encoding="utf-8"))
                if not isinstance(_cache, dict):
                    _cache = {}
            else:
                _cache = {}
        except Exception:
            _cache = {}
    return _cache


def _flush(data: dict[str, Any]) -> None:
    """Atomically persist prefs (write temp file, then replace)."""
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        tmp.replace(_FILE)
    except Exception:
        # Read-only storage etc. — prefs simply won't persist this session.
        pass


def get_pref(key: str, default: Any = None) -> Any:
    """Return a stored preference value, or *default* when unset."""
    with _lock:
        data = _load()
        return data.get(key, default)


def set_pref(key: str, value: Any) -> None:
    """Store a preference value and persist it immediately."""
    global _cache
    with _lock:
        data = _load()
        data[key] = value
        _cache = data
        _flush(data)
