"""
Tactics screen — formation and mentality selection.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.tactics import get_available_formations, PRESETS
from src.utils.config import Mentality
from src.ui.widgets.nav_bar import build_nav_bar


def build_tactics_screen(page: ft.Page) -> ft.Column:
    """Build the tactical setup content."""
    from src.ui.app import app_state, navigate

    # Set the navigation bar
    page.navigation_bar = build_nav_bar(page, 1)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    formations = get_available_formations()
    mentality_options = [
        ft.dropdown.Option(m.name.replace("_", " ").title()) for m in Mentality
    ]

    def on_formation_change(e):
        club_obj = queries.get_club(conn, gs.user_club_id)
        if club_obj:
            club_obj.formation = e.control.value
            queries.update_club(conn, club_obj)
            navigate(page, "/tactics")

    def on_mentality_change(e):
        club_obj = queries.get_club(conn, gs.user_club_id)
        if club_obj:
            key = e.control.value.upper().replace(" ", "_")
            try:
                club_obj.mentality = Mentality[key]
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")
            except KeyError:
                pass

    def make_preset_handler(preset_key):
        def handler(e):
            preset = PRESETS[preset_key]
            club_obj = queries.get_club(conn, gs.user_club_id)
            if club_obj:
                club_obj.formation = preset.formation
                club_obj.mentality = preset.mentality
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")  # Refresh
        return handler

    # Preset cards
    preset_cards = []
    for key, preset in PRESETS.items():
        preset_cards.append(
            ft.Card(
                content=ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.Icons.PLAY_ARROW),
                        title=ft.Text(preset.name, weight=ft.FontWeight.W_500),
                        subtitle=ft.Text(
                            f"{preset.formation} | {preset.description[:60]}",
                            size=11, color=ft.Colors.GREY_400,
                        ),
                        on_click=make_preset_handler(key),
                    ),
                    padding=ft.padding.symmetric(vertical=2),
                ),
            )
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=15,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("⚙️ Tactics", size=22, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=1),
                        ft.Dropdown(
                            label="Formation",
                            value=club.formation,
                            options=[ft.dropdown.Option(f) for f in formations],
                            on_select=on_formation_change,
                            width=300,
                        ),
                        ft.Dropdown(
                            label="Mentality",
                            value=club.mentality.name.replace("_", " ").title(),
                            options=mentality_options,
                            on_select=on_mentality_change,
                            width=300,
                        ),
                        ft.Container(height=10),
                        ft.Text("Quick Presets", size=16, weight=ft.FontWeight.W_500),
                        *preset_cards,
                    ],
                ),
            ),
        ],
    )
