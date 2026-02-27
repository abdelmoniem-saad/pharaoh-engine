"""
League Table screen — standings display.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar


def build_table_screen(page: ft.Page) -> ft.Column:
    """Build the league standings content."""
    from src.ui.app import app_state

    # Set the navigation bar
    page.navigation_bar = build_nav_bar(page, 3)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    standings = queries.get_standings(conn)

    # Build table rows
    rows = []
    for pos, s in enumerate(standings, 1):
        is_user = s.club_id == gs.user_club_id

        # Position-based color coding
        if is_user:
            row_color = ft.Colors.with_opacity(0.15, ft.Colors.GREEN)
        elif pos <= 2:
            row_color = ft.Colors.with_opacity(0.08, ft.Colors.BLUE)
        elif pos == 3:
            row_color = ft.Colors.with_opacity(0.08, ft.Colors.ORANGE)
        elif pos >= 16:
            row_color = ft.Colors.with_opacity(0.08, ft.Colors.RED)
        else:
            row_color = None

        name_weight = ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL

        rows.append(
            ft.DataRow(
                color=row_color,
                cells=[
                    ft.DataCell(ft.Text(str(pos), size=12)),
                    ft.DataCell(ft.Text(s.club_name[:16], size=12, weight=name_weight)),
                    ft.DataCell(ft.Text(str(s.played), size=12)),
                    ft.DataCell(ft.Text(str(s.won), size=12)),
                    ft.DataCell(ft.Text(str(s.drawn), size=12)),
                    ft.DataCell(ft.Text(str(s.lost), size=12)),
                    ft.DataCell(ft.Text(f"{s.goals_for}:{s.goals_against}", size=11)),
                    ft.DataCell(ft.Text(
                        str(s.points), size=13,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.AMBER_300 if is_user else None,
                    )),
                ],
            )
        )

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("#", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Team", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("P", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("W", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("D", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("L", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(ft.Text("G", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Pts", size=11, weight=ft.FontWeight.BOLD), numeric=True),
        ],
        rows=rows,
        column_spacing=8,
        horizontal_lines=ft.BorderSide(0.3, ft.Colors.WHITE24),
        heading_row_height=35,
        data_row_min_height=32,
        data_row_max_height=36,
    )

    # Legend
    legend = ft.Row(
        spacing=15,
        controls=[
            ft.Row(controls=[ft.Container(width=10, height=10, bgcolor=ft.Colors.BLUE_400, border_radius=2), ft.Text("CAF CL", size=10)]),
            ft.Row(controls=[ft.Container(width=10, height=10, bgcolor=ft.Colors.ORANGE_400, border_radius=2), ft.Text("CAF CC", size=10)]),
            ft.Row(controls=[ft.Container(width=10, height=10, bgcolor=ft.Colors.RED_400, border_radius=2), ft.Text("Relegation", size=10)]),
        ],
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=10,
                content=ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text("📊 Egyptian Premier League", size=20, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=1),
                        data_table,
                        ft.Container(height=5),
                        legend,
                    ],
                ),
            ),
        ],
    )
