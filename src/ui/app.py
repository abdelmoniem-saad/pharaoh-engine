"""
Main Flet application — navigation, shared state, and app lifecycle.
"""
from __future__ import annotations

import os
import sys
import sqlite3

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


# Global state instance
app_state = AppState()


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


def navigate(page: ft.Page, route: str):
    """
    Navigate to a screen by replacing page controls.

    This is the central navigation function used by all screens.
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
    content = builder(page)

    page.controls.clear()
    page.controls.append(content)
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

    # Show main menu
    navigate(page, "/")


def run_app():
    """Entry point to launch the Flet application."""
    ft.run(main)
