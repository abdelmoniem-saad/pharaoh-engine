"""
Main Flet application — navigation, shared state, and app lifecycle.
"""
from __future__ import annotations

import os
import sys
import time
import sqlite3
import threading
import asyncio

# Ensure src is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft
from src.ui import theme

from src.data.models import GameState
from src.utils.config import APP_NAME, APP_VERSION
from src.utils.logging_util import get_logger

log = get_logger("ui")


class AppState:
    """Shared application state accessible from all views."""

    def __init__(self):
        self.db_conn: sqlite3.Connection | None = None
        self.game_state: GameState | None = None
        self.current_save_name: str = "slot1"  # Active slot (multi-save support)
        self._busy: bool = False  # Guards against overlapping heavy operations
        self.pending_event = None  # Interactive random event awaiting player choice
        self._page_ref: ft.Page | None = None
        self._transition_container: ft.Container | None = None
        self._notification_column: ft.Column | None = None
        self._notification_timer: threading.Timer | None = None


# Global state instance
app_state = AppState()


# ── Notification System ─────────────────────────────────────────────────────

_NOTIFY_ICONS = {
    "match":    ft.Icons.SPORTS_SOCCER,
    "transfer": ft.Icons.SWAP_HORIZ,
    "board":    ft.Icons.ACCOUNT_BALANCE,
    "media":    ft.Icons.NEWSPAPER,
    "injury":   ft.Icons.LOCAL_HOSPITAL,
    "trophy":   ft.Icons.EMOJI_EVENTS,
    "general":  ft.Icons.NOTIFICATIONS,
    "success":  ft.Icons.CHECK_CIRCLE,
    "warning":  ft.Icons.WARNING,
    "error":    ft.Icons.ERROR,
}

_NOTIFY_COLORS = {
    "match":    ft.Colors.GREEN_400,
    "transfer": theme.ACCENT,
    "board":    ft.Colors.PURPLE_400,
    "media":    ft.Colors.BLUE_400,
    "injury":   ft.Colors.RED_400,
    "trophy":   theme.GOLD,
    "general":  ft.Colors.GREY_400,
    "success":  ft.Colors.GREEN_400,
    "warning":  ft.Colors.ORANGE_400,
    "error":    ft.Colors.RED_400,
}


def show_notification(page: ft.Page, message: str,
                      category: str = "general",
                      duration: float = 3.5) -> None:
    """Show a themed toast notification that slides in from top-right and auto-dismisses."""
    if not app_state._notification_column:
        return

    icon = _NOTIFY_ICONS.get(category, ft.Icons.NOTIFICATIONS)
    accent = _NOTIFY_COLORS.get(category, ft.Colors.GREY_400)

    card = ft.Container(
        content=ft.Row(
            spacing=10, tight=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(icon, size=18, color=accent),
                ft.Text(message, size=12, color="#EAEAEA",
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=10),
        border_radius=10,
        bgcolor=theme.BG_SURFACE,
        border=ft.border.only(left=ft.BorderSide(3, accent),
                              top=ft.BorderSide(1, ft.Colors.with_opacity(0.15, theme.GOLD)),
                              right=ft.BorderSide(1, ft.Colors.with_opacity(0.15, theme.GOLD)),
                              bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, theme.GOLD))),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=12,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        width=330,
        opacity=0,
        animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        offset=ft.Offset(0.05, 0),
        animate_offset=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
    )
    # Expiry stamp used by purge_expired_notifications() — guarantees the
    # toast disappears on the event thread even if its timer update was dropped.
    card.data = {"expire_at": time.time() + duration}

    col = app_state._notification_column
    col.controls.append(card)
    page.update()

    # Fade in
    card.opacity = 1
    card.offset = ft.Offset(0, 0)
    page.update()

    async def _dismiss():
        await asyncio.sleep(duration)
        try:
            card.opacity = 0
            card.offset = ft.Offset(0.05, 0)
            page.update()
            import time
            await asyncio.sleep(0.3)
            if card in col.controls:
                col.controls.remove(card)
                page.update()
        except Exception:
            pass

    page.run_task(_dismiss)


def show_breaking_news(page: ft.Page, headline: str,
                       body: str = "",
                       category: str = "general") -> None:
    """Show a prominent 'Breaking News' banner that auto-dismisses."""
    accent = _NOTIFY_COLORS.get(category, theme.ACCENT)

    banner = ft.Container(
        content=ft.Column(
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    content=ft.Text("⚡ BREAKING NEWS", size=9,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLACK,
                                    text_align=ft.TextAlign.CENTER),
                    bgcolor=theme.GOLD,
                    padding=ft.padding.symmetric(horizontal=10, vertical=2),
                    border_radius=4,
                ),
                ft.Text(headline, size=13, weight=ft.FontWeight.BOLD,
                        color="#EAEAEA", text_align=ft.TextAlign.CENTER,
                        max_lines=2),
                *([ ft.Text(body, size=11, color="#9E9E9E",
                            text_align=ft.TextAlign.CENTER, max_lines=2) ]
                  if body else []),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=16, vertical=10),
        border_radius=12,
        bgcolor=theme.BG_MID,
        border=ft.border.all(1, ft.Colors.with_opacity(0.35, theme.GOLD)),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=16,
                            color=ft.Colors.with_opacity(0.25, theme.GOLD)),
        width=340,
        opacity=0,
        animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
        scale=ft.Scale(0.95),
        animate_scale=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
    )

    col = app_state._notification_column
    if not col:
        return
    banner.data = {"expire_at": time.time() + 5.5}
    col.controls.insert(0, banner)
    page.update()

    banner.opacity = 1
    banner.scale = ft.Scale(1.0)
    page.update()

    async def _dismiss():
        await asyncio.sleep(5.0)
        try:
            banner.opacity = 0
            banner.scale = ft.Scale(0.95)
            page.update()
            import time
            await asyncio.sleep(0.4)
            if banner in col.controls:
                col.controls.remove(banner)
                page.update()
        except Exception:
            pass

    page.run_task(_dismiss)


def show_snackbar(page: ft.Page, message: str,
                  color: str = ft.Colors.WHITE,
                  bgcolor: str = None) -> None:
    """Show a brief snackbar notification at the bottom of the screen."""
    bgcolor = theme.BG_SURFACE if bgcolor is None else bgcolor
    # Clear any existing snackbars to avoid overlay pile-up
    page.overlay[:] = [ctrl for ctrl in page.overlay if not isinstance(ctrl, ft.SnackBar)]

    sb = ft.SnackBar(
        content=ft.Text(message, color=color, size=14),
        bgcolor=bgcolor,
        duration=2500,
    )
    page.overlay.append(sb)
    sb.open = True
    page.update()


def purge_expired_notifications(page: ft.Page) -> None:
    """
    Remove toast cards whose auto-dismiss window has passed.

    Called from event-thread entry points (navigate, snackbars) because UI
    updates issued by background timers are unreliable in some Flet runtimes.
    This guarantees toasts eventually vanish even when their timer's own
    page.update() was silently dropped.
    """
    col = app_state._notification_column
    if not col or not col.controls:
        return
    now = time.time()
    expired = [c for c in col.controls
               if isinstance(getattr(c, "data", None), dict)
               and c.data.get("expire_at") is not None
               and c.data["expire_at"] <= now]
    if not expired:
        return
    removed = False
    for c in expired:
        if c in col.controls:
            col.controls.remove(c)
            removed = True
    if removed:
        try:
            page.update()
        except Exception as ex:
            log.warning("Notification purge update failed: %s", ex)


# ── Tutorial Overlay ────────────────────────────────────────────────────────

def show_tutorial_overlay(page: ft.Page) -> None:
    """Displays a first-time manager tutorial overlay in the UI hub."""
    from src.utils.prefs import get_pref

    # NOTE: previously used page.client_storage which does not exist in every
    # Flet runtime and crashed right after choosing a new club.
    if get_pref("tutorial_seen"):
        return

    steps = [
        {
            "icon": ft.Icons.SPORTS_SOCCER,
            "title": "Welcome to Pharaoh Engine! ⚽",
            "desc": "You are now in charge. Your decisions on and off the pitch will shape the future of your club."
        },
        {
            "icon": ft.Icons.SPORTS_SOCCER,
            "title": "Match Day & Inbox",
            "desc": "The main hub! Read board emails, answer transfer bids, and press Advance Date to progress to match day."
        },
        {
            "icon": ft.Icons.PEOPLE_ALT,
            "title": "Squad & Tactics",
            "desc": "Evaluate player attributes, choose the best formation, and select your starting XI before every game."
        },
        {
            "icon": ft.Icons.ACCOUNT_BALANCE,
            "title": "Club & Finances",
            "desc": "Keep the fans happy, the board confident, and manage the wage bill to dominate the Egyptian Premier League."
        }
    ]

    current_step = [0]

    title_text = ft.Text(steps[0]["title"], size=22, weight=ft.FontWeight.BOLD, color=theme.GOLD, text_align=ft.TextAlign.CENTER)
    desc_text = ft.Text(steps[0]["desc"], size=16, color="#EAEAEA", text_align=ft.TextAlign.CENTER)
    icon_ctrl = ft.Icon(steps[0]["icon"], size=64, color=theme.GOLD)
    step_indicator = ft.Text(f"Step 1 of {len(steps)}", size=12, color="#9E9E9E")

    def _next_step(e):
        current_step[0] += 1
        if current_step[0] >= len(steps):
            _close_tutorial(e)
        else:
            step = steps[current_step[0]]
            title_text.value = step["title"]
            desc_text.value = step["desc"]
            icon_ctrl.name = step["icon"]
            step_indicator.value = f"Step {current_step[0] + 1} of {len(steps)}"
            btn.text = "Finish" if current_step[0] == len(steps) - 1 else "Next"
            page.update()

    def _close_tutorial(e):
        from src.utils.prefs import set_pref
        set_pref("tutorial_seen", True)
        if overlay_container in page.overlay:
            page.overlay.remove(overlay_container)
            page.update()

    btn = ft.ElevatedButton("Next", on_click=_next_step, style=ft.ButtonStyle(
        bgcolor={"": theme.GOLD}, color={"": theme.BG_DARK}, padding=16
    ), width=200)

    card = ft.Container(
        content=ft.Column(
            [icon_ctrl, title_text, desc_text, ft.Container(height=10), btn, step_indicator],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=15,
        ),
        bgcolor=theme.BG_SURFACE,
        padding=30,
        border_radius=16,
        width=320,
        height=380,
        border=ft.border.all(2, theme.GOLD),
        shadow=ft.BoxShadow(spread_radius=5, blur_radius=25, color=ft.Colors.with_opacity(0.5, "#000000")),
    )

    overlay_container = ft.Container(
        content=card,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.8, "#000000"),
        alignment=ft.Alignment(0, 0),
        on_click=lambda e: None,  # Consume clicks to prevent interacting with background
    )

    page.overlay.append(overlay_container)
    page.update()


# ── Crash-safe Error Screen ──────────────────────────────────────────────────

def build_error_screen(page: ft.Page, route: str = "?") -> ft.Column:
    """Themed fallback screen shown whenever a view fails to build.

    Guarantees the player always sees something usable and their save stays
    intact, instead of a blank screen or a dead app.
    """

    def retry(e):
        navigate(page, route)

    def go_home(e):
        navigate(page, "/" if app_state.game_state is None else "/match_day")

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.ERROR_OUTLINE, size=64, color="#EF5350"),
            ft.Container(height=12),
            ft.Text("Something went wrong", size=20,
                    weight=ft.FontWeight.BOLD, color="#EAEAEA"),
            ft.Container(height=6),
            ft.Text(
                "This section hit an unexpected error.\n"
                "Your save is safe — you can retry or continue playing.",
                size=13, color="#9E9E9E", text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(height=18),
            ft.ElevatedButton("🔄 Try Again", width=220, height=44,
                              style=theme.PRIMARY_BTN_STYLE, on_click=retry),
            ft.Container(height=8),
            ft.OutlinedButton("🏠 Back", width=220, height=40, on_click=go_home),
        ],
    )


# ── Busy Overlay & Heavy Task Runner ────────────────────────────────────────

def show_busy_overlay(page: ft.Page, text: str = "Simulating…"):
    """
    Show a full-screen modal 'working' overlay that blocks interaction.

    Returns a zero-arg *hide()* function that removes the overlay.
    """
    overlay = ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.ProgressRing(width=46, height=46, color=theme.GOLD),
                ft.Container(height=14),
                ft.Text(text, size=14, color="#EAEAEA",
                        text_align=ft.TextAlign.CENTER),
            ],
        ),
        bgcolor=ft.Colors.with_opacity(0.72, "#050810"),
        expand=True,
        alignment=ft.Alignment(0, 0),
        on_click=lambda e: None,  # swallow clicks while working
    )
    page.overlay.append(overlay)
    try:
        page.update()
    except Exception as ex:
        log.warning("Busy overlay initial update failed: %s", ex)

    def hide():
        try:
            if overlay in page.overlay:
                page.overlay.remove(overlay)
                page.update()
        except Exception as ex:
            log.warning("Failed to hide busy overlay: %s", ex)

    return hide


def run_busy_task(page: ft.Page, text: str, fn, on_done=None) -> None:
    """
    Run a potentially slow function behind a modal busy overlay.

    IMPORTANT: this deliberately runs *synchronously* on the calling thread
    after flushing the overlay to the screen. The progress ring keeps
    spinning client-side (Flutter renders animations locally), so users get
    instant feedback, and doing all control mutations on one thread
    guarantees every update is actually delivered.

    Rationale: UI updates from background threads proved unreliable in some
    Flet runtimes — the overlay lingered on screen until the next user
    interaction flushed pending diffs — so worker threads are intentionally
    avoided for UI-affecting work here.

    *on_done(error)* is invoked exactly once afterwards (error is None on
    success) and may safely navigate or update the UI. Re-entrant calls are
    ignored while a task is running, preventing double-click double-sims.
    """
    if getattr(app_state, "_busy", False):
        return
    app_state._busy = True

    try:
        hide = show_busy_overlay(page, text)
    except Exception:
        log.exception("Failed to show busy overlay")
        hide = lambda: None  # noqa: E731 — degrade to overlay-less execution

    error = None
    try:
        fn()
    except Exception as ex:
        log.exception("Busy task failed")
        error = ex

    try:
        hide()
    except Exception:
        log.exception("Failed to hide busy overlay")

    app_state._busy = False

    if callable(on_done):
        try:
            on_done(error)
        except Exception:
            log.exception("on_done callback failed")


# ── Navigation ──────────────────────────────────────────────────────────────

def navigate(page: ft.Page, route: str):
    """
    Navigate to a screen with a smooth fade transition.
    """
    app_state._live_match_token = None
    purge_expired_notifications(page)

    from src.ui.screens.main_menu import build_main_menu
    from src.ui.screens.squad import build_squad_screen
    from src.ui.screens.tactics import build_tactics_screen
    from src.ui.screens.match_day import build_match_day_screen
    from src.ui.screens.table import build_table_screen
    from src.ui.screens.inbox import build_inbox_screen
    from src.ui.screens.club_overview import build_club_overview_screen
    from src.ui.screens.fixtures import build_fixtures_screen
    from src.ui.screens.transfers import build_transfers_screen
    from src.ui.screens.pre_match import build_pre_match_screen
    from src.ui.screens.season_summary import build_season_summary_screen
    from src.ui.screens.settings import build_settings_screen
    from src.ui.screens.post_match import build_post_match_screen
    from src.ui.screens.history import build_history_screen
    from src.ui.screens.live_match import build_live_match_screen

    builders = {
        "/": build_main_menu,
        "/main_menu": build_main_menu,
        "/squad": build_squad_screen,
        "/tactics": build_tactics_screen,
        "/match_day": build_match_day_screen,
        "/table": build_table_screen,
        "/inbox": build_inbox_screen,
        "/club": build_club_overview_screen,
        "/fixtures": build_fixtures_screen,
        "/transfers": build_transfers_screen,
        "/pre_match": build_pre_match_screen,
        "/season_summary": build_season_summary_screen,
        "/settings": build_settings_screen,
        "/post_match": build_post_match_screen,
        "/history": build_history_screen,
        "/live_match": build_live_match_screen,
    }

    builder = builders.get(route, build_main_menu)
    try:
        new_content = builder(page)
    except Exception:
        # Error boundary: a broken screen must never take the whole app down.
        log.exception("Failed to build screen '%s'", route)
        new_content = build_error_screen(page, route)

    # [SOUND DISABLED] Navigation click sound commented out.
    # try:
    #     from src.utils.audio import play_click
    #     play_click()
    # except Exception:
    #     pass

    tc = app_state._transition_container
    if tc is not None:
        # Swap content directly (no fade-out/fade-in race condition).
        # The animate_opacity on the container still provides a smooth feel
        # on initial load, but we avoid the "glimpse then disappear" flicker
        # caused by the background-thread timer fighting Flet's animation.
        frame = ft.Container(width=min(page.width or 390, 800), content=new_content)
        app_state._workspace_frame = frame
        tc.content = ft.Row(expand=True, alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.STRETCH, controls=[frame])
        tc.opacity = 1
        page.update()
    else:
        # Fallback: no animation container yet (first load)
        page.controls.clear()
        page.controls.append(new_content)
        page.update()


def _install_global_error_hooks() -> None:
    """Log uncaught exceptions (main thread & worker threads) before exiting."""

    def _hook(exc_type, exc, tb):
        log.critical("Uncaught exception", exc_info=(exc_type, exc, tb))
        try:
            sys.__excepthook__(exc_type, exc, tb)
        except Exception:
            pass

    sys.excepthook = _hook
    if hasattr(threading, "excepthook"):
        def _thread_hook(args):
            log.critical("Uncaught thread exception",
                         exc_info=(args.exc_type, args.exc_value,
                                   args.exc_traceback))
        threading.excepthook = _thread_hook


def main(page: ft.Page):
    """Flet app entry point — configures the page and sets up routing."""
    _install_global_error_hooks()
    page.title = APP_NAME
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    from src.utils.prefs import get_pref
    theme.configure(get_pref("ui_theme", "classic"))
    theme.apply_to_page(page)
    # Safe area accounts for mobile status bar and home indicator
    page.padding = 0
    page.spacing = 0

    # [SOUND DISABLED] Audio/haptics initialization commented out.
    # try:
    #     from src.utils.audio import init_audio
    #     init_audio(page)
    # except Exception:
    #     pass

    app_state._page_ref = page

    # ── Transition container — wraps every screen for smooth fades ───────
    transition_container = ft.Container(
        expand=True,
        opacity=1,
        animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )
    app_state._transition_container = transition_container

    def resize_workspace(e):
        frame = getattr(app_state, "_workspace_frame", None)
        if frame is not None:
            frame.width = min(page.width or 390, 800)
            page.update()
    page.on_resize = resize_workspace


    # ── Notification overlay — floats above screen content ───────────────
    # IMPORTANT: The overlay must not block pointer events on the content
    # underneath.  We disable hit-testing on the overlay container itself
    # so clicks pass through to buttons, lists, etc. in the game screens.
    notification_col = ft.Column(
        spacing=6,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    app_state._notification_column = notification_col

    notification_overlay = ft.Container(
        content=notification_col,
        alignment=ft.Alignment(0, -1),
    )

    # Stack: transition_container (full screen) + notification overlay on top
    # The overlay is placed inside a transparent GestureDetector-like wrapper
    # that ignores pointer events, letting clicks fall through to the
    # transition_container below.
    root = ft.Stack(
        controls=[
            transition_container,
            ft.TransparentPointer(
                content=notification_overlay,
                top=10,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )

    # Wrap root in SafeArea to handle mobile intrusions (notches, home indicators)
    page.controls.append(ft.SafeArea(content=root, expand=True))
    page.update()

    # App preferences work before a career exists and never create a save.
    from src.utils.localization import set_language, is_rtl
    set_language(get_pref("language", "en"))
    page.rtl = is_rtl()
    theme.apply_to_page(page)

    # Show main menu
    navigate(page, "/")


def run_app():
    """Entry point to launch the Flet application."""
    from pathlib import Path
    ft.run(main, assets_dir=str(Path(__file__).resolve().parents[2] / "assets"))
