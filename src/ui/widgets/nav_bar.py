"""
Shared navigation bar used across all game screens.
"""
from __future__ import annotations

import flet as ft


def _get_unread() -> int:
    """Get the unread inbox count from app state, returns 0 if unavailable."""
    try:
        from src.ui.app import app_state
        from src.data.queries import get_unread_count
        if app_state.db_conn:
            return get_unread_count(app_state.db_conn)
    except Exception:
        pass
    return 0


def build_nav_bar(page: ft.Page, selected_index: int = 0) -> ft.NavigationBar:
    """
    Build the shared bottom navigation bar.

    Args:
        page: Flet page reference for navigation.
        selected_index: Index of the currently active tab (0-4).
    """
    unread_count = _get_unread()
    route_map = {
        0: "/squad",
        1: "/tactics",
        2: "/match_day",
        3: "/table",
        4: "/inbox",
    }

    def on_nav(e):
        from src.ui.app import navigate

        target = route_map.get(e.control.selected_index, "/squad")
        navigate(page, target)

    # Inbox destination — add badge if unread messages
    if unread_count > 0:
        inbox_dest = ft.NavigationBarDestination(
            icon=ft.Icons.MAIL,
            label="Inbox",
            badge=ft.Badge(label=str(unread_count)),
        )
    else:
        inbox_dest = ft.NavigationBarDestination(
            icon=ft.Icons.MAIL, label="Inbox",
        )

    return ft.NavigationBar(
        selected_index=selected_index,
        on_change=on_nav,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Squad"),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Tactics"),
            ft.NavigationBarDestination(icon=ft.Icons.SPORTS_SOCCER, label="Match"),
            ft.NavigationBarDestination(icon=ft.Icons.TABLE_CHART, label="Table"),
            inbox_dest,
        ],
    )
