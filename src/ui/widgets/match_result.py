"""
Match result widget — compact result display for Flet.
"""
from __future__ import annotations

import flet as ft

from src.data.models import MatchResult


def match_result_row(result: MatchResult) -> ft.Row:
    """Create a compact match result display row."""
    return ft.Row(
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10,
        controls=[
            ft.Text(
                result.home_club_name,
                size=13, text_align=ft.TextAlign.RIGHT,
                width=120,
            ),
            ft.Container(
                content=ft.Text(
                    f"{result.home_goals} - {result.away_goals}",
                    size=15, weight=ft.FontWeight.BOLD,
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=5,
            ),
            ft.Text(
                result.away_club_name,
                size=13, text_align=ft.TextAlign.LEFT,
                width=120,
            ),
        ],
    )
