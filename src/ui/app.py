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


class AppState:
    """Shared application state accessible from all views."""

    def __init__(self):
        self.db_conn: sqlite3.Connection | None = None
        self.game_state: GameState | None = None


# Global state instance
app_state = AppState()


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

    builders = {
        "/": build_main_menu,
        "/main_menu": build_main_menu,
        "/squad": build_squad_screen,
        "/tactics": build_tactics_screen,
        "/match_day": build_match_day_screen,
        "/table": build_table_screen,
        "/inbox": build_inbox_screen,
    }

    builder = builders.get(route, build_main_menu)
    content = builder(page)

    page.controls.clear()
    page.controls.append(content)
    page.update()


def main(page: ft.Page):
    """Flet app entry point — configures the page and sets up routing."""
    page.title = "Pharaoh Engine"
    page.window.width = 420
    page.window.height = 780
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.AMBER,
        font_family="Roboto",
    )
    page.padding = 0

    # Show main menu
    navigate(page, "/")


def run_app():
    """Entry point to launch the Flet application."""
    ft.run(main)
