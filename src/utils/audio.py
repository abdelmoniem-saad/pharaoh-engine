"""
Audio and feedback helper.

[SOUND DISABLED]
All sound / haptic feedback has been intentionally commented out for this
release. The public functions below are kept as no-op stubs so that any
existing or future call site keeps working without producing audio.
To re-enable sound later, restore the commented implementation block and
uncomment the call sites marked with "[SOUND DISABLED]".
"""
from __future__ import annotations


# ── Original implementation (commented out — sound disabled) ────────────────
# Playback order was:
# 1) Flet Audio controls (when available in runtime) -> best for mobile/desktop.
# 2) Native Windows WAV playback (winsound) for desktop fallback.
# 3) Haptic feedback service for mobile tactile fallback.
#
# import sys
# import threading
# from pathlib import Path
# from typing import Any
#
# _AUDIO_ENABLED = True
# _HAPTIC_SERVICE: Any | None = None
# _PAGE_REF: Any | None = None
# _AUDIO_PLAYERS: dict[str, Any] = {}
#
# _ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "sfx"
# _SFX_FILES = {
#     "click": "ui_click.wav",
#     "goal": "goal_cheer.wav",
#     "full": "full_time_whistle.wav",
# }
#
#
# def _asset_path(name: str) -> Path:
#     return _ASSET_DIR / name
#
#
# def init_audio(page: Any) -> None:
#     """Initialize optional feedback services and best-available players."""
#     global _HAPTIC_SERVICE, _PAGE_REF, _AUDIO_PLAYERS
#     _PAGE_REF = page
#
#     try:
#         import flet as ft
#     except Exception:
#         return
#
#     # Optional haptics service
#     try:
#         h = ft.HapticFeedback()
#         if hasattr(page, "services") and isinstance(page.services, list):
#             page.services.append(h)
#             _HAPTIC_SERVICE = h
#     except Exception:
#         _HAPTIC_SERVICE = None
#
#     # Optional Flet Audio controls (not available in all runtime versions)
#     _AUDIO_PLAYERS = {}
#     audio_cls = getattr(ft, "Audio", None)
#     if audio_cls is None:
#         return
#
#     try:
#         for key, filename in _SFX_FILES.items():
#             p = _asset_path(filename)
#             if not p.exists():
#                 continue
#             player = audio_cls(src=str(p), volume=0.45, autoplay=False)
#             if hasattr(page, "overlay") and isinstance(page.overlay, list):
#                 page.overlay.append(player)
#             _AUDIO_PLAYERS[key] = player
#         if _AUDIO_PLAYERS and hasattr(page, "update"):
#             page.update()
#     except Exception:
#         _AUDIO_PLAYERS = {}
#
#
# def set_audio_enabled(enabled: bool) -> None:
#     global _AUDIO_ENABLED
#     _AUDIO_ENABLED = bool(enabled)
#
#
# def is_audio_enabled() -> bool:
#     return _AUDIO_ENABLED
#
#
# def _haptic(kind: str = "light") -> None:
#     if not _AUDIO_ENABLED or _HAPTIC_SERVICE is None:
#         return
#
#     method_candidates = {
#         "light": ["light_impact", "medium_impact", "vibrate"],
#         "goal": ["medium_impact", "heavy_impact", "vibrate"],
#         "full": ["heavy_impact", "medium_impact", "vibrate"],
#     }.get(kind, ["light_impact", "vibrate"])
#
#     for method_name in method_candidates:
#         try:
#             fn = getattr(_HAPTIC_SERVICE, method_name, None)
#             if callable(fn):
#                 fn()
#                 return
#         except Exception:
#             continue
#
#
# def _play_with_flet_player(key: str) -> bool:
#     player = _AUDIO_PLAYERS.get(key)
#     if not player:
#         return False
#     try:
#         # Restart from beginning when supported
#         seek_fn = getattr(player, "seek", None)
#         if callable(seek_fn):
#             seek_fn(0)
#         play_fn = getattr(player, "play", None)
#         if callable(play_fn):
#             play_fn()
#             return True
#     except Exception:
#         return False
#     return False
#
#
# def _play_windows_wav(filename: str) -> bool:
#     if sys.platform != "win32":
#         return False
#
#     wav_path = _asset_path(filename)
#     if not wav_path.exists():
#         return False
#
#     try:
#         import winsound
#     except Exception:
#         return False
#
#     def _run() -> None:
#         try:
#             winsound.PlaySound(str(wav_path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
#         except Exception:
#             pass
#
#     threading.Thread(target=_run, daemon=True).start()
#     return True
#
#
# def _play(key: str, haptic_kind: str) -> None:
#     if not _AUDIO_ENABLED:
#         return
#
#     if _play_with_flet_player(key):
#         return
#
#     filename = _SFX_FILES.get(key)
#     if filename and _play_windows_wav(filename):
#         return
#
#     _haptic(haptic_kind)


# ── No-op stubs (safe replacements so existing call sites keep working) ─────

def init_audio(page=None) -> None:
    """[SOUND DISABLED] No-op — kept for API compatibility."""


def set_audio_enabled(enabled: bool) -> None:
    """[SOUND DISABLED] No-op — kept for API compatibility."""


def is_audio_enabled() -> bool:
    """[SOUND DISABLED] Audio is always off."""
    return False


def play_click() -> None:
    """[SOUND DISABLED] No-op."""


def play_goal() -> None:
    """[SOUND DISABLED] No-op."""


def play_full_time() -> None:
    """[SOUND DISABLED] No-op."""
