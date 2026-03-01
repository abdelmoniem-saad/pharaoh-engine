"""
Squad management screen — view players, set starting XI.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.player import calculate_overall_rating
from src.ui.widgets.nav_bar import build_nav_bar


def build_squad_screen(page: ft.Page) -> ft.Column:
    """Build the squad management content."""
    from src.ui.app import app_state, navigate

    # Set the navigation bar
    page.navigation_bar = build_nav_bar(page, 0)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    players = queries.get_players_by_club(conn, club.id)
    # Remove unresolved player_card reference, just show a simple list for now
    player_tiles = [ft.ListTile(title=ft.Text(p.name), subtitle=ft.Text(p.position.value)) for p in players]

    # Build player rows for the DataTable
    rows = []
    for player in players:
        ovr = calculate_overall_rating(player)
        fit_color = (
            ft.Colors.GREEN_400 if player.fitness >= 80
            else ft.Colors.YELLOW_400 if player.fitness >= 50
            else ft.Colors.RED_400
        )
        ovr_color = ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE

        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(player.name, size=13)),
                    ft.DataCell(ft.Text(player.position.value, size=12)),
                    ft.DataCell(ft.Text(str(player.age), size=12)),
                    ft.DataCell(ft.Text(str(ovr), size=13, weight=ft.FontWeight.BOLD, color=ovr_color)),
                    ft.DataCell(ft.Text(f"{player.fitness}%", size=12, color=fit_color)),
                    ft.DataCell(ft.Text(f"{player.form:.1f}", size=12)),
                ],
            )
        )

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Name", size=12, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Pos", size=12, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Age", size=12, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("OVR", size=12, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("Fit", size=12, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Form", size=12, weight=ft.FontWeight.BOLD), numeric=True),
        ],
        rows=rows,
        column_spacing=12,
        horizontal_lines=ft.BorderSide(0.3, ft.Colors.WHITE24),
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=10, right=10, top=10),
                content=ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text(
                            f"📋 {gs.user_club_name} — Squad",
                            size=22, weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(
                            f"Date: {gs.current_date.strftime('%d %b %Y')}",
                            size=13, color=ft.Colors.GREY_500,
                        ),
                        ft.Divider(height=1),
                        data_table,
                    ],
                ),
            ),
        ],
    )
