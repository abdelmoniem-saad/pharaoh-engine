"""
Player card widget — reusable player info display for Flet.
"""
from __future__ import annotations

import flet as ft

from src.data.models import Player
from src.core.player import calculate_overall_rating


def player_card(player: Player) -> ft.ListTile:
    """Create a compact player info tile with richer detail."""
    ovr = calculate_overall_rating(player)
    fit_color = (
        ft.Colors.GREEN_400 if player.fitness >= 80
        else ft.Colors.YELLOW_400 if player.fitness >= 50
        else ft.Colors.RED_400
    )
    ovr_color = ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE

    # Status badges
    badges = []
    if player.is_captain:
        badges.append("©")
    if player.injury_days_remaining > 0:
        badges.append("🏥")
    if player.suspension_matches > 0:
        badges.append("🚫")
    if player.transfer_listed:
        badges.append("🔴")
    badge_text = " ".join(badges)

    subtitle_parts = [f"Age {player.age}", f"Form {player.form:.1f}"]
    if player.season_stats.goals > 0:
        subtitle_parts.append(f"⚽{player.season_stats.goals}")
    if player.season_stats.assists > 0:
        subtitle_parts.append(f"🅰️{player.season_stats.assists}")

    return ft.ListTile(
        leading=ft.Text(player.position.value, size=12, color=ft.Colors.AMBER_300),
        title=ft.Text(
            f"{player.name} {badge_text}".strip(),
            size=13, weight=ft.FontWeight.W_500,
        ),
        subtitle=ft.Text(
            " | ".join(subtitle_parts),
            size=11, color=ft.Colors.GREY_400,
        ),
        trailing=ft.Row(
            spacing=12,
            tight=True,
            controls=[
                ft.Text(str(ovr), size=14, weight=ft.FontWeight.BOLD, color=ovr_color),
                ft.Text(f"{player.fitness}%", size=12, color=fit_color),
            ],
        ),
    )
