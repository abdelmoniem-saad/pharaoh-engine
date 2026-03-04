"""
Main Flet application — navigation, shared state, and app lifecycle.
"""
from __future__ import annotations

import os
import sys
import sqlite3
import threading

# Ensure src is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import flet as ft

from src.data.models import GameState
from src.utils.config import APP_NAME, APP_VERSION


class AppState:
    """Shared application state accessible from all views."""

    def __init__(self):
        self.db_conn: sqlite3.Connection | None = None
        self.game_state: GameState | None = None
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
    "transfer": ft.Colors.AMBER_400,
    "board":    ft.Colors.PURPLE_400,
    "media":    ft.Colors.BLUE_400,
    "injury":   ft.Colors.RED_400,
    "trophy":   ft.Colors.AMBER_300,
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
        bgcolor="#141e33",
        border=ft.border.only(left=ft.BorderSide(3, accent),
                              top=ft.BorderSide(1, ft.Colors.with_opacity(0.15, "#FFD54F")),
                              right=ft.BorderSide(1, ft.Colors.with_opacity(0.15, "#FFD54F")),
                              bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, "#FFD54F"))),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=12,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.BLACK)),
        width=330,
        opacity=0,
        animate_opacity=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
        offset=ft.Offset(0.05, 0),
        animate_offset=ft.Animation(250, ft.AnimationCurve.EASE_OUT),
    )

    col = app_state._notification_column
    col.controls.append(card)
    page.update()

    # Fade in
    card.opacity = 1
    card.offset = ft.Offset(0, 0)
    page.update()

    def _dismiss():
        try:
            card.opacity = 0
            card.offset = ft.Offset(0.05, 0)
            page.update()
            import time
            time.sleep(0.3)
            if card in col.controls:
                col.controls.remove(card)
                page.update()
        except Exception:
            pass

    t = threading.Timer(duration, _dismiss)
    t.daemon = True
    t.start()


def show_breaking_news(page: ft.Page, headline: str,
                       body: str = "",
                       category: str = "general") -> None:
    """Show a prominent 'Breaking News' banner that auto-dismisses."""
    accent = _NOTIFY_COLORS.get(category, ft.Colors.AMBER_400)

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
                    bgcolor="#FFD54F",
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
        bgcolor="#0f1729",
        border=ft.border.all(1, ft.Colors.with_opacity(0.35, "#FFD54F")),
        shadow=ft.BoxShadow(spread_radius=0, blur_radius=16,
                            color=ft.Colors.with_opacity(0.25, "#FFD54F")),
        width=340,
        opacity=0,
        animate_opacity=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
        scale=ft.Scale(0.95),
        animate_scale=ft.Animation(350, ft.AnimationCurve.EASE_OUT),
    )

    col = app_state._notification_column
    if not col:
        return
    col.controls.insert(0, banner)
    page.update()

    banner.opacity = 1
    banner.scale = ft.Scale(1.0)
    page.update()

    def _dismiss():
        try:
            banner.opacity = 0
            banner.scale = ft.Scale(0.95)
            page.update()
            import time
            time.sleep(0.4)
            if banner in col.controls:
                col.controls.remove(banner)
                page.update()
        except Exception:
            pass

    t = threading.Timer(5.0, _dismiss)
    t.daemon = True
    t.start()


def show_snackbar(page: ft.Page, message: str,
                  color: str = ft.Colors.WHITE,
                  bgcolor: str = "#141e33") -> None:
    """Show a brief snackbar notification at the bottom of the screen."""
    sb = ft.SnackBar(
        content=ft.Text(message, color=color, size=14),
        bgcolor=bgcolor,
        duration=2500,
    )
    page.overlay.append(sb)
    sb.open = True
    page.update()


# ── Navigation ──────────────────────────────────────────────────────────────

def navigate(page: ft.Page, route: str):
    """
    Navigate to a screen with a smooth fade transition.
    """
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
    }

    builder = builders.get(route, build_main_menu)
    new_content = builder(page)

    tc = app_state._transition_container
    if tc is not None:
        # Swap content directly (no fade-out/fade-in race condition).
        # The animate_opacity on the container still provides a smooth feel
        # on initial load, but we avoid the "glimpse then disappear" flicker
        # caused by the background-thread timer fighting Flet's animation.
        tc.content = new_content
        tc.opacity = 1
        page.update()
    else:
        # Fallback: no animation container yet (first load)
        page.controls.clear()
        page.controls.append(new_content)
        page.update()


def main(page: ft.Page):
    """Flet app entry point — configures the page and sets up routing."""
    page.title = APP_NAME
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0a0e1a"
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.AMBER,
        font_family="Roboto",
    )
    # Top padding accounts for the mobile status/notification bar
    page.padding = ft.Padding(top=40, bottom=0, left=0, right=0)
    page.spacing = 0

    app_state._page_ref = page

    # ── Transition container — wraps every screen for smooth fades ───────
    transition_container = ft.Container(
        expand=True,
        opacity=1,
        animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
    )
    app_state._transition_container = transition_container

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
        alignment=ft.Alignment(0, -0.85),  # top center
        expand=True,
    )

    # Stack: transition_container (full screen) + notification overlay on top
    # The overlay is placed inside a transparent GestureDetector-like wrapper
    # that ignores pointer events, letting clicks fall through to the
    # transition_container below.
    root = ft.Stack(
        controls=[
            transition_container,
            ft.TransparentPointer(content=notification_overlay),
        ],
        expand=True,
    )

    page.controls.append(root)
    page.update()

    # ── Load language preference (once, at startup) ────────────────────
    try:
        from src.utils.localization import set_language, get_language, is_rtl
        _lang_conn = app_state.db_conn
        if _lang_conn is None:
            try:
                from src.data.database import connect as _connect
                _lang_conn = _connect()
            except Exception:
                _lang_conn = None
        if _lang_conn:
            try:
                # Ensure the settings row + language column exist
                _lang_conn.execute(
                    "INSERT OR IGNORE INTO game_settings (id) VALUES (1)"
                )
                _lang_conn.commit()
                row = _lang_conn.execute(
                    "SELECT language FROM game_settings WHERE id=1"
                ).fetchone()
                if row and row["language"] and row["language"] != "en":
                    set_language(row["language"])
                    page.rtl = is_rtl()
                    page.update()
                    print(f"DEBUG: Startup language loaded from DB: '{row['language']}'")
            except Exception as ex:
                print(f"DEBUG: Startup language load skipped: {ex}")
    except Exception:
        pass

    # Show main menu
    navigate(page, "/")


def run_app():
    """Entry point to launch the Flet application."""
    ft.run(main)
