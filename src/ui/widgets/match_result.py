"""
Match result widget — compact result display for Flet.
"""
from __future__ import annotations

import flet as ft

from src.data.models import MatchResult


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
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.Text(
                    result.home_club_name,
                    size=13, text_align=ft.TextAlign.RIGHT,
                    width=120,
                    weight=ft.FontWeight.BOLD if result.home_club_id == user_club_id else ft.FontWeight.NORMAL,
                ),
                ft.Container(
                    content=ft.Text(
                        f"{result.home_goals} - {result.away_goals}",
                        size=15, weight=ft.FontWeight.BOLD,
                        color=score_color,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=5,
                ),
                ft.Text(
                    result.away_club_name,
                    size=13, text_align=ft.TextAlign.LEFT,
                    width=120,
                    weight=ft.FontWeight.BOLD if result.away_club_id == user_club_id else ft.FontWeight.NORMAL,
                ),
            ],
        ),
        padding=ft.padding.symmetric(vertical=2),
    )
