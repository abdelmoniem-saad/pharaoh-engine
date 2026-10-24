"""
Match result widget — compact result display for Flet.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data.models import MatchResult
from src.utils.localization import t, display_home_name, display_away_name


def match_result_row(result: MatchResult, user_club_id: int = 0) -> ft.Container:
    """Create a compact match result display row with contextual styling."""
    # Determine result from user perspective
    if user_club_id > 0:
        if result.home_club_id == user_club_id:
            is_win = result.home_goals > result.away_goals
            is_loss = result.home_goals < result.away_goals
        elif result.away_club_id == user_club_id:
            is_win = result.away_goals > result.home_goals
            is_loss = result.away_goals < result.home_goals
        else:
            is_win = False
            is_loss = False
    else:
        is_win = False
        is_loss = False

    score_color = (
        ft.Colors.GREEN_400 if is_win
        else ft.Colors.RED_400 if is_loss
        else ft.Colors.GREY_300
    )

    return ft.Container(
        rtl=theme.rtl(), content=ft.Row(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text(
                    display_home_name(result),
                    rtl=theme.rtl(), size=13, text_align=ft.TextAlign.LEFT if theme.rtl() else ft.TextAlign.RIGHT,
                    expand=True, max_lines=2,
                    weight=ft.FontWeight.BOLD if result.home_club_id == user_club_id else ft.FontWeight.NORMAL,
                ),
                ft.Container(
                    rtl=theme.rtl(), content=ft.Text(
                        theme.scoreline(result.home_goals, result.away_goals),
                        rtl=False, size=15, weight=ft.FontWeight.BOLD,
                        color=score_color,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=6,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.15, theme.GOLD)),
                ),
                ft.Text(
                    display_away_name(result),
                    rtl=theme.rtl(), size=13, text_align=ft.TextAlign.RIGHT if theme.rtl() else ft.TextAlign.LEFT,
                    expand=True, max_lines=2,
                    weight=ft.FontWeight.BOLD if result.away_club_id == user_club_id else ft.FontWeight.NORMAL,
                ),
            ],
        ),
        padding=ft.padding.symmetric(vertical=2),
    )
