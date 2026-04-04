"""
Chart widgets for Pharaoh Engine — pharaoh-themed data visualization.

Flet 0.80.x removed the built-in LineChart / BarChart controls.
This module provides lightweight pure-Flet visual replacements using
containers, rows, and gradients — no external chart dependencies.
"""
from __future__ import annotations

import flet as ft
from src.utils.localization import t

# Theme constants (duplicated locally to avoid circular imports)
_GOLD = "#FFD54F"
_GOLD_DIM = ft.Colors.with_opacity(0.18, "#FFD54F")
_GREEN = "#66BB6A"
_RED = "#EF5350"
_BLUE = "#42A5F5"
_AMBER = ft.Colors.AMBER_400
_TEXT_MUTED = "#616161"
_BG_SURFACE = "#141e33"
_GRID = ft.Colors.with_opacity(0.08, ft.Colors.WHITE)


def player_form_line_chart(
    ratings: list[tuple[int, float]],
    width: int = 340,
    height: int = 160,
) -> ft.Container:
    """
    Visual form chart showing a player\'s match-by-match ratings
    as a bar sparkline with color-coded columns.
    """
    if not ratings:
        return ft.Container(
            content=ft.Text("No match data yet", size=11, color=_TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
            width=width, height=60,
            alignment=ft.Alignment(0, 0),
        )

    avg_rating = sum(r for _, r in ratings) / len(ratings)
    min_r = min(r for _, r in ratings)
    max_r = max(r for _, r in ratings)
    r_range = max(max_r - min_r, 1.0)
    bar_height = height - 40

    dots = []
    for i, (md, r) in enumerate(ratings):
        color = _GREEN if r >= 7.5 else _GOLD if r >= 6.5 else _RED
        frac = (r - min_r + 0.5) / (r_range + 1.0)
        dot_bottom = max(8, int(frac * bar_height))

        dots.append(
            ft.Container(
                content=ft.Column(
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.END,
                    controls=[
                        ft.Text(f"{r:.1f}", size=8, color=color,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            width=max(6, (width - 40) // len(ratings) - 4),
                            height=dot_bottom,
                            border_radius=ft.border_radius.only(top_left=3, top_right=3),
                            bgcolor=color,
                            gradient=ft.LinearGradient(
                                colors=[ft.Colors.with_opacity(0.3, color), color],
                                begin=ft.Alignment(0, 1),
                                end=ft.Alignment(0, -1),
                            ),
                        ),
                        ft.Text(f"{md}", size=7, color=_TEXT_MUTED),
                    ],
                ),
                expand=True,
            )
        )

    return ft.Container(
        content=ft.Column(
            spacing=2,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Match Ratings", size=10, color=_TEXT_MUTED),
                        ft.Text(f"Avg: {avg_rating:.1f}", size=10, color=_GOLD,
                                weight=ft.FontWeight.BOLD),
                    ],
                ),
                ft.Container(
                    content=ft.Row(
                        spacing=2,
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                        controls=dots,
                    ),
                    height=bar_height + 18,
                    padding=ft.padding.only(left=4, right=4, bottom=2),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
                    border=ft.border.all(1, _GRID),
                ),
            ],
        ),
        width=width,
        padding=ft.padding.only(top=4),
    )


def player_stats_bar_chart(
    categories: dict[str, float],
    width: int = 340,
    height: int = 140,
) -> ft.Container:
    """Horizontal bar chart for player attribute categories."""
    if not categories:
        return ft.Container()

    max_val = 20.0
    bars = []
    for name, value in categories.items():
        color = _GREEN if value >= 14 else _GOLD if value >= 10 else _AMBER if value >= 7 else _RED
        pct = min(value / max_val, 1.0)

        bars.append(
            ft.Container(
                content=ft.Row(
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(name[:5], size=10, color=_TEXT_MUTED, width=40),
                        ft.Container(
                            content=ft.Container(
                                width=pct * (width - 110),
                                height=14,
                                border_radius=ft.border_radius.only(
                                    top_right=4, bottom_right=4),
                                bgcolor=color,
                                gradient=ft.LinearGradient(
                                    colors=[ft.Colors.with_opacity(0.5, color), color],
                                    begin=ft.Alignment(-1, 0),
                                    end=ft.Alignment(1, 0),
                                ),
                            ),
                            expand=True,
                            height=14,
                            border_radius=7,
                            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                        ),
                        ft.Text(f"{value:.1f}", size=10, color=color,
                                weight=ft.FontWeight.BOLD, width=32,
                                text_align=ft.TextAlign.RIGHT),
                    ],
                ),
                padding=ft.padding.symmetric(vertical=1),
            )
        )

    return ft.Container(
        content=ft.Column(spacing=3, controls=bars),
        width=width,
        padding=ft.padding.only(top=4, right=4),
    )


def season_position_chart(
    positions: list[tuple[int, int]],
    total_teams: int = 18,
    width: int = 340,
    height: int = 140,
) -> ft.Container:
    """Visual position tracker — colored badges per matchday."""
    if not positions:
        return ft.Container(
            content=ft.Text("No position data yet", size=11, color=_TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
            width=width, height=50,
            alignment=ft.Alignment(0, 0),
        )

    badges = []
    for md, pos in positions:
        color = (_GREEN if pos <= 4 else _GOLD if pos <= 8
                 else _AMBER if pos <= 14 else _RED)
        badges.append(
            ft.Container(
                content=ft.Column(
                    spacing=1,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Text(f"{pos}", size=11, color=color,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(f"{md}", size=7, color=_TEXT_MUTED),
                    ],
                ),
                width=max(28, (width - 20) // max(len(positions), 1)),
                height=40,
                alignment=ft.Alignment(0, 0),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.08, color),
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, color)),
            )
        )

    latest_pos = positions[-1][1]
    latest_color = (_GREEN if latest_pos <= 4 else _GOLD if latest_pos <= 8
                    else _AMBER if latest_pos <= 14 else _RED)

    return ft.Container(
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Position History", size=10, color=_TEXT_MUTED),
                        ft.Container(
                            content=ft.Text(
                                f"{latest_pos}{_ordinal(latest_pos)}",
                                size=12, color=latest_color,
                                weight=ft.FontWeight.BOLD),
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=8,
                            bgcolor=ft.Colors.with_opacity(0.12, latest_color),
                        ),
                    ],
                ),
                ft.Row(
                    spacing=2,
                    scroll=ft.ScrollMode.AUTO,
                    controls=badges,
                ),
            ],
        ),
        width=width,
        padding=ft.padding.only(top=4),
    )


def club_form_trend_line(
    results: list[str],
    width: int = 340,
    height: int = 100,
) -> ft.Container:
    """Mini trend visualization for W/D/L as colored blocks."""
    if not results:
        return ft.Container()

    ordered = list(reversed(results))
    color_map = {"W": _GREEN, "D": _AMBER, "L": _RED}
    height_map = {"W": 40, "D": 22, "L": 8}
    label_map = {"W": "Win", "D": "Draw", "L": "Loss"}

    blocks = []
    for r in ordered:
        color = color_map.get(r, _TEXT_MUTED)
        h = height_map.get(r, 15)
        blocks.append(
            ft.Container(
                content=ft.Text(r[0], size=9, color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                width=max(20, (width - 20) // max(len(ordered), 1) - 4),
                height=h,
                border_radius=ft.border_radius.only(top_left=4, top_right=4),
                bgcolor=color,
                alignment=ft.Alignment(0, 0),
                # Flet 0.8x exposes tooltip on controls; Tooltip(content=...) is unsupported.
                tooltip=label_map.get(r, r),
            )
        )

    wins = sum(1 for r in results if r == "W")
    draws = sum(1 for r in results if r == "D")
    losses = sum(1 for r in results if r == "L")

    return ft.Container(
        content=ft.Column(
            spacing=4,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Form Trend", size=10, color=_TEXT_MUTED),
                        ft.Row(spacing=8, tight=True, controls=[
                            ft.Text(f"W{wins}", size=10, color=_GREEN),
                            ft.Text(f"D{draws}", size=10, color=_AMBER),
                            ft.Text(f"L{losses}", size=10, color=_RED),
                        ]),
                    ],
                ),
                ft.Row(
                    spacing=3,
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.END,
                    controls=blocks,
                ),
            ],
        ),
        width=width,
        padding=ft.padding.only(top=4),
    )


def _ordinal(n: int) -> str:
    """Return ordinal suffix for a number (1st, 2nd, 3rd, etc.)."""
    if 11 <= n % 100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
