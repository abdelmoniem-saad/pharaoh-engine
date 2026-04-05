"""
Pharaoh Engine — Egyptian Football Management Game
Main entry point.
"""
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def apply_windows_asyncio_shutdown_patch() -> None:
    """Silence known benign Windows Proactor pipe teardown errors."""
    if sys.platform != "win32":
        return

    # Allow troubleshooting by disabling the patch at runtime.
    if os.getenv("PHARAOH_DISABLE_WIN_ASYNCIO_PATCH", "").lower() in {"1", "true", "yes"}:
        return

    try:
        import asyncio

        proactor_events = getattr(asyncio, "proactor_events", None)
        transport_cls = getattr(proactor_events, "_ProactorBasePipeTransport", None)
        if transport_cls is None:
            return

        if getattr(transport_cls, "__pharaoh_patch_applied__", False):
            return

        original_call_connection_lost = getattr(transport_cls, "_call_connection_lost", None)
        if original_call_connection_lost is None:
            return

        def _quiet_connection_lost(self, exc=None):
            try:
                original_call_connection_lost(self, exc)
            except ConnectionResetError:
                pass
            except OSError as err:
                # Only suppress common Windows teardown noise.
                if getattr(err, "winerror", None) in {64, 995, 10054}:
                    pass
                else:
                    raise

        transport_cls._call_connection_lost = _quiet_connection_lost
        transport_cls.__pharaoh_patch_applied__ = True
    except Exception:
        # Fallback to default asyncio behavior if internals differ.
        return


apply_windows_asyncio_shutdown_patch()

from src.ui.app import run_app

if __name__ == "__main__":
    run_app()
