"""
Player card widget — reusable player info display for Flet.
"""
from __future__ import annotations

import flet as ft

from src.data.models import Player
from src.core.player import calculate_overall_rating


def player_card(player: Player) -> ft.ListTile:
    """Create a compact player info tile."""
    ovr = calculate_overall_rating(player)
    fit_color = (
        ft.Colors.GREEN_400 if player.fitness >= 80
        else ft.Colors.YELLOW_400 if player.fitness >= 50
        else ft.Colors.RED_400
    )
    ovr_color = ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE

    return ft.ListTile(
        leading=ft.Text(player.position.value, size=12, color=ft.Colors.AMBER_300),
        title=ft.Text(player.name, size=13, weight=ft.FontWeight.W_500),
        subtitle=ft.Text(f"Age {player.age} | Form {player.form:.1f}", size=11, color=ft.Colors.GREY_400),
        trailing=ft.Row(
            spacing=12,
            tight=True,
            controls=[
                ft.Text(str(ovr), size=14, weight=ft.FontWeight.BOLD, color=ovr_color),
                ft.Text(f"{player.fitness}%", size=12, color=fit_color),
            ],
        ),
    )
