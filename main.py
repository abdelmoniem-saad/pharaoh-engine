"""
Pharaoh Engine — Egyptian Football Management Game
Main entry point.
"""
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Suppress harmless Windows asyncio shutdown noise ─────────────────────────
# On Windows the ProactorEventLoop sometimes raises ConnectionResetError when
# the Flet subprocess pipe is torn down.  This is cosmetic — the game has
# already saved and closed — so we silence it.
if sys.platform == "win32":
    import asyncio

    _original_er = asyncio.proactor_events._ProactorBasePipeTransport  # type: ignore[attr-defined]

    _orig_call_connection_lost = _original_er._call_connection_lost

    def _quiet_connection_lost(self, exc=None):
        try:
            _orig_call_connection_lost(self, exc)
        except (ConnectionResetError, OSError):
            pass

    _original_er._call_connection_lost = _quiet_connection_lost

from src.ui.app import run_app

if __name__ == "__main__":
    run_app()
