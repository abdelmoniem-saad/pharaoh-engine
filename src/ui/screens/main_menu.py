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
from src.utils.config import APP_VERSION, expectation_display


def build_main_menu(page: ft.Page) -> ft.Column:
    """Build the main menu content."""

    def new_game_click(e):
        _show_manager_name_dialog(page)

    def continue_click(e):
        _continue_game(page)

    def settings_click(e):
        from src.ui.app import navigate
        navigate(page, "/settings")

    # No navigation bar on main menu
    page.navigation_bar = None

    return ft.Column(
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        controls=[
            ft.Container(expand=2),
            ft.Icon(ft.Icons.SPORTS_SOCCER, size=48, color=ft.Colors.AMBER_400),
            ft.Container(height=5),
            ft.Text(
                "PHARAOH ENGINE",
                size=30, weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.AMBER_300,
            ),
            ft.Text(
                "Egyptian Football Manager",
                size=15,
                color=ft.Colors.GREY_400,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(expand=1),
            ft.ElevatedButton(
                "⚽ New Game",
                width=280, height=55,
                style=ft.ButtonStyle(
                    text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
                    bgcolor=ft.Colors.AMBER_700,
                    color=ft.Colors.WHITE,
                ),
                on_click=new_game_click,
            ),
            ft.Container(height=8),
            ft.ElevatedButton(
                "📂 Continue",
                width=280, height=55,
                style=ft.ButtonStyle(text_style=ft.TextStyle(size=18)),
                on_click=continue_click,
            ),
            ft.Container(height=8),
            ft.OutlinedButton(
                "⚙️ Settings",
                width=280, height=50,
                on_click=settings_click,
            ),
            ft.Container(expand=2),
            ft.Text(
                f"v{APP_VERSION} — MVP",
                size=12, color=ft.Colors.GREY_600,
            ),
        ],
    )


def _show_manager_name_dialog(page: ft.Page):
    """Show a dialog to enter the manager name before club selection."""
    name_field = ft.TextField(
        label="Manager Name",
        value="",
        hint_text="Enter your name",
        width=280,
        autofocus=True,
        text_size=16,
    )

    def on_confirm(e):
        manager_name = name_field.value.strip() if name_field.value else "Manager"
        if not manager_name:
            manager_name = "Manager"
        page.pop_dialog()
        _show_club_selection(page, manager_name)

    dlg = ft.AlertDialog(
        title=ft.Text("👤 Your Identity"),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("What should the board call you?",
                            size=13, color=ft.Colors.GREY_400),
                    ft.Container(height=10),
                    name_field,
                ],
                spacing=5,
                tight=True,
            ),
            width=300,
            height=120,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("Continue ➡️", on_click=on_confirm),
        ],
    )
    page.show_dialog(dlg)


def _show_club_selection(page: ft.Page, manager_name: str):
    """Create a new game and show club selection dialog."""
    from src.ui.app import app_state, navigate, show_snackbar

    # Seed the database
    delete_save("default")
    conn = connect("default")
    game_state = seed_database(conn, game_seed=rng.randint(1, 999999))
    game_state.manager_name = manager_name

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

        # Color indicator dot
        club_buttons.append(
            ft.ListTile(
                leading=ft.Container(
                    width=32, height=32,
                    bgcolor=club.primary_color,
                    border_radius=16,
                    content=ft.Icon(ft.Icons.SPORTS_SOCCER, size=16, color=ft.Colors.WHITE),
                ),
                title=ft.Text(club.name, weight=ft.FontWeight.W_500),
                subtitle=ft.Text(
                    f"{club.city} — ⭐ {club.reputation} — 🎯 {expectation_display(club.season_expectation)}",
                    size=12, color=ft.Colors.GREY_400,
                ),
                on_click=make_handler(),
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text("🏟️ Choose Your Club"),
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
    from src.ui.app import app_state, navigate, show_snackbar

    game_state.user_club_id = club_id
    game_state.user_club_name = club_name
    queries.save_game_state(conn, game_state)

    # Mark club as user controlled
    club = queries.get_club(conn, club_id)
    if club:
        club.is_user_controlled = True
        queries.update_club(conn, club)

        # Send initial board objectives message
        from src.core.board import generate_season_objectives
        from src.data.models import InboxMessage
        from datetime import date
        objectives = generate_season_objectives(club)
        exp_name = expectation_display(club.season_expectation)
        obj_text = "\n".join(f"• {o.description} ({o.priority})" for o in objectives)
        queries.insert_message(conn, InboxMessage(
            date=date(2025, 8, 15),
            subject="📋 Board Objectives",
            body=(
                f"Welcome, {game_state.manager_name}!\n\n"
                f"The board expects you to achieve the following this season:\n\n"
                f"🎯 Season Target: {exp_name}\n\n{obj_text}\n\n"
                f"Good luck!"
            ),
            category="board",
        ))

    # Store in shared state
    app_state.db_conn = conn
    app_state.game_state = game_state

    page.pop_dialog()
    navigate(page, "/match_day")
    show_snackbar(page, f"🎉 Welcome to {club_name}, {game_state.manager_name}!")


def _continue_game(page: ft.Page):
    """Load an existing save game."""
    from src.ui.app import app_state, navigate, show_snackbar

    try:
        conn = connect("default")
        game_state = queries.load_game_state(conn)
        if game_state:
            app_state.db_conn = conn
            app_state.game_state = game_state
            navigate(page, "/squad")
            show_snackbar(page, f"📂 Welcome back, {game_state.manager_name}!")
        else:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("No Save Found"),
                    content=ft.Text("No save game found. Start a New Game!"),
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                )
            )
    except Exception as e:
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Error"),
                content=ft.Text(f"Error loading save: {e}"),
                actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
            )
        )
