"""
Stat bar widget — visual attribute/stat bar for Flet.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme
from src.utils.localization import t


def stat_bar(label: str, value: int, max_value: int = 20) -> ft.Row:
    """Create a labeled progress bar for displaying a stat value."""
    ratio = value / max_value if max_value > 0 else 0

    if ratio >= 0.8:
        bar_color = ft.Colors.GREEN_400
    elif ratio >= 0.6:
        bar_color = ft.Colors.LIGHT_GREEN_400
    elif ratio >= 0.4:
        bar_color = ft.Colors.YELLOW_400
    elif ratio >= 0.2:
        bar_color = ft.Colors.ORANGE_400
    else:
        bar_color = ft.Colors.RED_400

    return ft.Row(
        rtl=theme.rtl(), spacing=8,
        controls=[
            ft.Text(label, rtl=theme.rtl(), size=12, width=90, color=theme.TEXT_SECONDARY),
            ft.ProgressBar(
                rtl=theme.rtl(), value=ratio,
                color=bar_color,
                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                expand=True,
                height=4,
            ),
            ft.Text(str(value), rtl=theme.rtl(), size=11, weight=ft.FontWeight.BOLD, color=bar_color, width=25),
        ],
    )
