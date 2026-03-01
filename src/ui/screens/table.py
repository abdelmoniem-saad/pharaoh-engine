"""
League Table screen — standings display with season info.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar


def build_table_screen(page: ft.Page) -> ft.Column:
    """Build the league standings content."""
    from src.ui.app import app_state

    page.navigation_bar = build_nav_bar(page, 3)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    standings = queries.get_standings(conn)
    current_md = queries.get_current_matchday(conn)

    # Find user position
    user_pos = 0
    user_standing = None
    for i, s in enumerate(standings, 1):
        if s.club_id == gs.user_club_id:
            user_pos = i
            user_standing = s
            break

    # Build table rows
    rows = []
    for pos, s in enumerate(standings, 1):
        is_user = s.club_id == gs.user_club_id

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
                    ft.DataCell(ft.Text(
                        s.club_name[:16],
                        size=12, weight=name_weight,
                    )),
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
            ft.DataColumn(label=ft.Text("#", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Team", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("P", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("W", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("D", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("L", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("G", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Pts", size=11, weight=ft.FontWeight.BOLD), numeric=True),
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
        spacing=12,
        controls=[
            ft.Row(controls=[
                ft.Container(width=10, height=10, bgcolor=ft.Colors.BLUE_400, border_radius=2),
                ft.Text("CAF CL", size=10),
            ]),
            ft.Row(controls=[
                ft.Container(width=10, height=10, bgcolor=ft.Colors.ORANGE_400, border_radius=2),
                ft.Text("CAF CC", size=10),
            ]),
            ft.Row(controls=[
                ft.Container(width=10, height=10, bgcolor=ft.Colors.RED_400, border_radius=2),
                ft.Text("Relegation", size=10),
            ]),
        ],
    )

    # User position callout
    pos_suffix = {1: "st", 2: "nd", 3: "rd"}.get(user_pos, "th")
    user_callout_text = f"📍 You are {user_pos}{pos_suffix}" if user_pos else ""
    user_pts_text = ""
    if user_standing:
        user_pts_text = (
            f" — {user_standing.points} pts | "
            f"W{user_standing.won} D{user_standing.drawn} L{user_standing.lost} | "
            f"GD {user_standing.goal_difference:+d}"
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
                        ft.Text("📊 Egyptian Premier League", size=20,
                                weight=ft.FontWeight.BOLD),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Text(
                                    f"Season {gs.season_year}/{gs.season_year + 1}",
                                    size=12, color=ft.Colors.GREY_500,
                                ),
                                ft.Text(
                                    f"Matchday {current_md}",
                                    size=12, color=ft.Colors.AMBER_400,
                                    weight=ft.FontWeight.W_500,
                                ),
                            ],
                        ),
                        # User position callout
                        ft.Container(
                            content=ft.Text(
                                f"{user_callout_text}{user_pts_text}",
                                size=13, weight=ft.FontWeight.W_500,
                                color=ft.Colors.GREEN_300,
                            ),
                            padding=ft.padding.symmetric(horizontal=10, vertical=6),
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN),
                            border_radius=6,
                        ) if user_pos else ft.Container(),
                        ft.Divider(height=1),
                        data_table,
                        ft.Container(height=5),
                        legend,
                    ],
                ),
            ),
        ],
    )
