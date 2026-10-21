"""
News ticker and notification banner widgets for the match day screen.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme
from src.utils.localization import t

_GOLD = theme.GOLD
_GOLD_BORDER = ft.Colors.with_opacity(0.18, theme.GOLD)
_TEXT_PRIMARY = "#EAEAEA"
_TEXT_MUTED = "#616161"
_BG_SURFACE = theme.BG_SURFACE

_CAT_ICONS = {
    "match": "⚽", "media": "📰", "board": "🏛️",
    "transfer": "💰", "general": "📬", "injury": "🏥",
}


def news_ticker(headlines: list[dict]) -> ft.Container:
    """
    Horizontal scrolling news ticker for the match day screen.

    Args:
        headlines: list of dicts with keys: subject, category
    """
    if not headlines:
        return ft.Container(height=0)

    items = []
    for h in headlines[:8]:
        icon = _CAT_ICONS.get(h.get("category", "general"), "📬")
        items.append(
            ft.Container(
                content=ft.Row(
                    spacing=4, tight=True,
                    controls=[
                        ft.Text(icon, size=11),
                        ft.Text(
                            h.get("subject", ""),
                            size=10, color=_TEXT_PRIMARY,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
            )
        )
        # Separator
        items.append(
            ft.Container(
                content=ft.Text("•", size=10, color=_GOLD),
                padding=ft.padding.symmetric(horizontal=4),
            )
        )

    return ft.Container(
        content=ft.Row(
            controls=items,
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
        ),
        height=28,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.AMBER),
        border=ft.border.only(
            bottom=ft.BorderSide(1, _GOLD_BORDER),
        ),
        padding=ft.padding.symmetric(horizontal=8),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )


def quick_headline_bar(
    text: str,
    icon: str = "⚡",
    bgcolor: str = "",
) -> ft.Container:
    """
    Single-line highlight bar for important news (e.g. transfer completed).
    """
    return ft.Container(
        content=ft.Row(
            spacing=6, tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Text(icon, size=12),
                ft.Text(text, size=11, color=_TEXT_PRIMARY,
                        weight=ft.FontWeight.W_500,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        bgcolor=bgcolor or ft.Colors.with_opacity(0.08, ft.Colors.AMBER),
        border_radius=8,
        border=ft.border.all(1, _GOLD_BORDER),
    )

