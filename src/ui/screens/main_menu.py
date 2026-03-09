"""
Main Menu screen — New Game, Continue, Settings.
"""
from __future__ import annotations

import flet as ft

from src.data.models import Club
from src.data.database import connect, delete_save
from src.data.seed import seed_database
from src.data import queries
from src.core.league import create_league_season
from src.utils import rng
from src.utils.config import APP_VERSION, expectation_display
from src.utils.localization import t, display_name


def build_main_menu(page: ft.Page) -> ft.Column:
    """Build the main menu content."""
    from src.ui.theme import (
        gradient_bg, BG_DARK, BG_MID, BG_TEAL, BG_SURFACE,
        GOLD, GOLD_GLOW, GOLD_BORDER, GOLD_BORDER_STRONG,
        TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
        PRIMARY_BTN_STYLE, SECONDARY_BTN_STYLE,
    )

    def new_game_click(e):
        _show_manager_name_dialog(page)

    def continue_click(e):
        _continue_game(page)

    def settings_click(e):
        from src.ui.app import navigate
        navigate(page, "/settings")

    # No navigation bar on main menu
    page.navigation_bar = None

    # Title block
    title_block = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
        controls=[
            ft.Container(
                content=ft.Icon(ft.Icons.SHIELD, size=56, color=GOLD),
                width=80, height=80, border_radius=40,
                bgcolor=ft.Colors.with_opacity(0.10, GOLD),
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(
                    spread_radius=2, blur_radius=20,
                    color=ft.Colors.with_opacity(0.15, GOLD),
                ),
            ),
            ft.Container(height=8),
            ft.Text(
                t("app_title").upper(),
                size=34, weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                color=GOLD,
            ),
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Container(width=30, height=1, bgcolor=GOLD_BORDER_STRONG),
                        ft.Text("⚽", size=12),
                        ft.Container(width=30, height=1, bgcolor=GOLD_BORDER_STRONG),
                    ],
                ),
            ),
            ft.Text(
                t("egyptian_football_manager"),
                size=15,
                color=TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
                italic=True,
            ),
        ],
    )

    # Buttons
    button_block = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        controls=[
            ft.ElevatedButton(
                "⚽  " + t("new_game"),
                width=280, height=56,
                style=PRIMARY_BTN_STYLE,
                on_click=new_game_click,
            ),
            ft.ElevatedButton(
                "📂  " + t("continue_game"),
                width=280, height=52,
                style=SECONDARY_BTN_STYLE,
                on_click=continue_click,
            ),
            ft.OutlinedButton(
                "⚙️  " + t("settings"),
                width=280, height=48,
                style=ft.ButtonStyle(
                    color=TEXT_SECONDARY,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    side=ft.BorderSide(1, GOLD_BORDER),
                ),
                on_click=settings_click,
            ),
        ],
    )

    return ft.Column(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                gradient=gradient_bg(
                    colors=[BG_DARK, BG_MID, "#0b1a2d", BG_TEAL],
                ),
                padding=0,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    controls=[
                        ft.Container(expand=2),
                        title_block,
                        ft.Container(expand=1),
                        button_block,
                        ft.Container(expand=2),
                        ft.Text(
                            f"v{APP_VERSION}",
                            size=11, color=TEXT_MUTED,
                        ),
                        ft.Container(height=16),
                    ],
                ),
            ),
        ],
    )


def _show_manager_name_dialog(page: ft.Page):
    """Show a dialog to enter the manager name before club selection."""
    from src.ui.theme import GOLD, GOLD_BORDER, TEXT_SECONDARY

    name_field = ft.TextField(
        label=t("manager_name"),
        value="",
        hint_text=t("enter_your_name"),
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
        title=ft.Text("👤 " + t("your_identity"), color=GOLD),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(t("what_should_board_call_you"),
                            size=13, color=TEXT_SECONDARY),
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
            ft.TextButton(t("cancel"), on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton(t("confirm") + " ➡️", on_click=on_confirm,
                              style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700,
                                                    color=ft.Colors.WHITE,
                                                    shape=ft.RoundedRectangleBorder(radius=10))),
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
                _select_club(page, conn, game_state, c, dlg)
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
                title=ft.Text(display_name(club), weight=ft.FontWeight.W_500),
                subtitle=ft.Text(
                    f"{club.city} — ⭐ {club.reputation} — 🎯 {expectation_display(club.season_expectation)}",
                    size=12, color=ft.Colors.GREY_400,
                ),
                on_click=make_handler(),
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text("🏟️ " + t("choose_your_club"),
                       color="#FFD54F", weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.ListView(
                controls=club_buttons,
                spacing=2,
            ),
            width=300,
            height=450,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)


def _select_club(page: ft.Page, conn, game_state, club: Club, dlg: ft.AlertDialog):
    """Handle club selection."""
    from src.ui.app import app_state, navigate, show_snackbar

    game_state.user_club_id = club.id
    game_state.user_club_name = club.name
    game_state.user_club_name_ar = club.name_ar
    queries.save_game_state(conn, game_state)

    # Mark club as user controlled
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
            subject="📋 " + t("board_objectives"),
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

    # Ensure Cup is initialized (it might have failed in seed_database due to FKs)
    from src.core.competition import ensure_cup_initialized
    ensure_cup_initialized(conn, game_state)

    page.pop_dialog()
    navigate(page, "/match_day")
    show_snackbar(page, f"🎉 Welcome to {display_name(club)}, {game_state.manager_name}!")


def _continue_game(page: ft.Page):
    """Load an existing save game."""
    from src.ui.app import app_state, navigate, show_snackbar

    try:
        conn = connect("default")
        game_state = queries.load_game_state(conn)
        if game_state:
            app_state.db_conn = conn
            app_state.game_state = game_state

            # Repair/Ensure Cup (for existing saves after schema update)
            from src.core.competition import ensure_cup_initialized
            if ensure_cup_initialized(conn, game_state):
                print("DEBUG: Egypt Cup repaired/initialized successfully.")

            navigate(page, "/squad")
            show_snackbar(page, f"📂 Welcome back, {game_state.manager_name}!")
        else:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text(t("no_save_found")),
                    content=ft.Text(t("no_save_found_msg")),
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
