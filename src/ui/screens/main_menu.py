"""
Main Menu screen — New Game, Continue, Settings.
"""
from __future__ import annotations

import flet as ft

from src.data.database import connect, delete_save
from src.data.seed import seed_database
from src.data import queries
from src.core.league import create_league_season
from src.utils import rng


def build_main_menu(page: ft.Page) -> ft.Column:
    """Build the main menu content."""

    def new_game_click(e):
        _show_club_selection(page)

    def continue_click(e):
        _continue_game(page)

    def settings_click(e):
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Settings"),
                content=ft.Text("Settings coming in Phase 2!"),
            )
        )

    # No navigation bar on main menu
    page.navigation_bar = None

    return ft.Column(
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        controls=[
            ft.Container(expand=2),
            ft.Text(
                "⚽ PHARAOH ENGINE ⚽",
                size=32, weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Egyptian Football Manager",
                size=16,
                color=ft.Colors.AMBER_400,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(expand=1),
            ft.Button(
                "New Game",
                width=280, height=55,
                style=ft.ButtonStyle(text_style=ft.TextStyle(size=18)),
                on_click=new_game_click,
            ),
            ft.Button(
                "Continue",
                width=280, height=55,
                style=ft.ButtonStyle(text_style=ft.TextStyle(size=18)),
                on_click=continue_click,
            ),
            ft.OutlinedButton(
                "Settings",
                width=280, height=50,
                on_click=settings_click,
            ),
            ft.Container(expand=2),
            ft.Text(
                "v0.1.0 — MVP",
                size=12, color=ft.Colors.GREY_600,
            ),
        ],
    )


def _show_club_selection(page: ft.Page):
    """Create a new game and show club selection dialog."""
    from src.ui.app import app_state, navigate

    # Seed the database
    delete_save("default")
    conn = connect("default")
    game_state = seed_database(conn, game_seed=rng.randint(1, 999999))

    # Generate league fixtures
    clubs = queries.get_all_clubs(conn)
    create_league_season(conn, clubs, game_state.season_year)

    # Build club list
    club_buttons = []
    for club in clubs:
        def make_handler(c=club):
            def handler(e):
                _select_club(page, conn, game_state, c.id, c.name, dlg)
            return handler

        club_buttons.append(
            ft.ListTile(
                leading=ft.Icon(ft.Icons.SPORTS_SOCCER, color=club.primary_color),
                title=ft.Text(club.name, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(f"{club.city} — Rep: {club.reputation}"),
                on_click=make_handler(),
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text("Choose Your Club"),
        content=ft.Container(
            content=ft.ListView(
                controls=club_buttons,
                spacing=2,
            ),
            width=350,
            height=450,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)


def _select_club(page: ft.Page, conn, game_state, club_id: int,
                  club_name: str, dlg: ft.AlertDialog):
    """Handle club selection."""
    from src.ui.app import app_state, navigate

    game_state.user_club_id = club_id
    game_state.user_club_name = club_name
    queries.save_game_state(conn, game_state)

    # Mark club as user controlled
    club = queries.get_club(conn, club_id)
    if club:
        club.is_user_controlled = True
        queries.update_club(conn, club)

    # Store in shared state
    app_state.db_conn = conn
    app_state.game_state = game_state

    page.pop_dialog()
    navigate(page, "/squad")


def _continue_game(page: ft.Page):
    """Load an existing save game."""
    from src.ui.app import app_state, navigate

    try:
        conn = connect("default")
        game_state = queries.load_game_state(conn)
        if game_state:
            app_state.db_conn = conn
            app_state.game_state = game_state
            navigate(page, "/squad")
        else:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("No Save Found"),
                    content=ft.Text("No save game found. Start a New Game!"),
                )
            )
    except Exception as e:
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text(f"Error loading save: {e}"),
            )
        )
