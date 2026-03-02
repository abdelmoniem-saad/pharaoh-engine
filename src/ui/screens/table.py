"""
League Table screen — standings display with card-based mobile layout.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.cards import section_card, info_tile, action_card
from src.ui.theme import (
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    TEXT_SUCCESS, TEXT_WARNING, TEXT_DANGER,
    CARD_BG, CARD_GLASS, CARD_GLASS_STRONG, CARD_BG_HIGHLIGHT, CARD_RADIUS_SM,
    PAGE_PADDING, SECTION_SPACING,
    TITLE_SIZE, BODY_SIZE, CAPTION_SIZE, TINY_SIZE,
    GOLD_BORDER, header_bar,
)


def build_table_screen(page: ft.Page) -> ft.Column:
    """Build the league standings content."""
    from src.ui.app import app_state, navigate

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

    # ── Table Header Row ────────────────────────────────────────────
    header_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("#", size=TINY_SIZE, color=TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("Team", size=TINY_SIZE, color=TEXT_MUTED, expand=True),
                ft.Text("P", size=TINY_SIZE, color=TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("W", size=TINY_SIZE, color=TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("D", size=TINY_SIZE, color=TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("L", size=TINY_SIZE, color=TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("GD", size=TINY_SIZE, color=TEXT_MUTED, width=28,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("Pts", size=TINY_SIZE, color=TEXT_MUTED, width=28,
                        text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        bgcolor=CARD_GLASS,
        border_radius=CARD_RADIUS_SM,
    )

    # ── Table Rows ──────────────────────────────────────────────────
    table_rows = []
    for pos, s in enumerate(standings, 1):
        is_user = s.club_id == gs.user_club_id

        # Zone coloring
        if is_user:
            bg = CARD_BG_HIGHLIGHT
            left_border = ft.border.only(
                left=ft.BorderSide(3, TEXT_SUCCESS),
                top=ft.BorderSide(1, ft.Colors.with_opacity(0.2, ft.Colors.GREEN)),
                right=ft.BorderSide(1, ft.Colors.with_opacity(0.2, ft.Colors.GREEN)),
                bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.2, ft.Colors.GREEN)),
            )
        elif pos <= 2:
            bg = ft.Colors.with_opacity(0.08, ft.Colors.BLUE)
            left_border = ft.border.only(left=ft.BorderSide(3, ft.Colors.BLUE_400))
        elif pos == 3:
            bg = ft.Colors.with_opacity(0.08, ft.Colors.ORANGE)
            left_border = ft.border.only(left=ft.BorderSide(3, ft.Colors.ORANGE_400))
        elif pos >= len(standings) - 2:
            bg = ft.Colors.with_opacity(0.08, ft.Colors.RED)
            left_border = ft.border.only(left=ft.BorderSide(3, ft.Colors.RED_400))
        else:
            bg = CARD_GLASS
            left_border = ft.border.all(1, GOLD_BORDER)

        name_weight = ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL
        pts_color = ACCENT if is_user else TEXT_PRIMARY

        gd_val = s.goal_difference
        gd_color = TEXT_SUCCESS if gd_val > 0 else TEXT_DANGER if gd_val < 0 else TEXT_MUTED

        table_rows.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(str(pos), size=CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL,
                                color=ACCENT if is_user else TEXT_SECONDARY),
                        ft.Text(s.club_name[:16], size=12, expand=True,
                                weight=name_weight,
                                color=TEXT_SUCCESS if is_user else TEXT_PRIMARY,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(str(s.played), size=CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=TEXT_SECONDARY),
                        ft.Text(str(s.won), size=CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=TEXT_SUCCESS),
                        ft.Text(str(s.drawn), size=CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=TEXT_WARNING),
                        ft.Text(str(s.lost), size=CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=TEXT_DANGER),
                        ft.Text(f"{gd_val:+d}", size=CAPTION_SIZE, width=28,
                                text_align=ft.TextAlign.CENTER, color=gd_color),
                        ft.Text(str(s.points), size=BODY_SIZE, width=28,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD, color=pts_color),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                border_radius=CARD_RADIUS_SM,
                bgcolor=bg,
                border=left_border,
            )
        )

    # ── User Position Callout ───────────────────────────────────────
    pos_suffix = {1: "st", 2: "nd", 3: "rd"}.get(user_pos, "th")
    user_pts_text = ""
    if user_standing:
        user_pts_text = (
            f"{user_standing.points} pts  •  W{user_standing.won} D{user_standing.drawn} L{user_standing.lost}  •  "
            f"GD {user_standing.goal_difference:+d}"
        )

    # ── Legend ──────────────────────────────────────────────────────
    legend = ft.Row(
        spacing=12,
        controls=[
            ft.Row(spacing=4, tight=True, controls=[
                ft.Container(width=10, height=10, bgcolor=ft.Colors.BLUE_400, border_radius=2),
                ft.Text("CAF CL", size=TINY_SIZE, color=TEXT_MUTED),
            ]),
            ft.Row(spacing=4, tight=True, controls=[
                ft.Container(width=10, height=10, bgcolor=ft.Colors.ORANGE_400, border_radius=2),
                ft.Text("CAF CC", size=TINY_SIZE, color=TEXT_MUTED),
            ]),
            ft.Row(spacing=4, tight=True, controls=[
                ft.Container(width=10, height=10, bgcolor=ft.Colors.RED_400, border_radius=2),
                ft.Text("Relegation", size=TINY_SIZE, color=TEXT_MUTED),
            ]),
        ],
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.all(PAGE_PADDING),
                content=ft.Column(
                    spacing=SECTION_SPACING,
                    controls=[
                        # Header
                        header_bar(
                            title="Egyptian Premier League",
                            subtitle=f"Season {gs.season_year}/{gs.season_year + 1}  •  Matchday {current_md}",
                            icon=ft.Icons.LEADERBOARD,
                            page=page,
                        ),

                        # User position callout
                        *([ ft.Container(
                            content=ft.Column(spacing=2, controls=[
                                ft.Text(f"📍 You are {user_pos}{pos_suffix}", size=BODY_SIZE,
                                        weight=ft.FontWeight.W_600, color=TEXT_SUCCESS),
                                ft.Text(user_pts_text, size=CAPTION_SIZE, color=TEXT_SECONDARY),
                            ]),
                            padding=ft.padding.symmetric(horizontal=12, vertical=8),
                            bgcolor=CARD_GLASS_STRONG,
                            border_radius=CARD_RADIUS_SM,
                            border=ft.border.only(
                                left=ft.BorderSide(3, TEXT_SUCCESS),
                                top=ft.BorderSide(1, GOLD_BORDER),
                                right=ft.BorderSide(1, GOLD_BORDER),
                                bottom=ft.BorderSide(1, GOLD_BORDER),
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=0, blur_radius=6,
                                color=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
                            ),
                        )] if user_pos else []),

                        # Quick nav
                        ft.Row(spacing=6, controls=[
                            ft.OutlinedButton("📅 Fixtures", height=32,
                                              on_click=lambda e: navigate(page, "/fixtures"),
                                              style=ft.ButtonStyle(
                                                  padding=ft.padding.symmetric(horizontal=12),
                                                  shape=ft.RoundedRectangleBorder(radius=10),
                                                  side=ft.BorderSide(1, GOLD_BORDER),
                                              )),
                            ft.OutlinedButton("🏟️ My Club", height=32,
                                              on_click=lambda e: navigate(page, "/club"),
                                              style=ft.ButtonStyle(
                                                  padding=ft.padding.symmetric(horizontal=12),
                                                  shape=ft.RoundedRectangleBorder(radius=10),
                                                  side=ft.BorderSide(1, GOLD_BORDER),
                                              )),
                        ]),

                        # Table
                        header_row,
                        ft.Column(spacing=2, controls=table_rows),
                        ft.Container(height=4),
                        legend,
                    ],
                ),
            ),
        ],
    )
