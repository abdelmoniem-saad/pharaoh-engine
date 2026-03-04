"""
Chart widgets for Pharaoh Engine — pharaoh-themed data visualization.

Uses Flet's built-in LineChart and BarChart for player form,
club position history, attribute breakdowns, and form trend lines.
"""
from __future__ import annotations

import flet as ft

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
    Line chart showing a player's match-by-match ratings.

    Args:
        ratings: list of (matchday, rating) tuples, oldest first.
    """
    if not ratings:
        return ft.Container(
            content=ft.Text("No match data yet", size=11, color=_TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
            width=width, height=60,
            alignment=ft.Alignment(0, 0),
        )

    data_points = [
        ft.LineChartDataPoint(
            x=i,
            y=r,
            tooltip=f"MD {md}: {r:.1f}",
        )
        for i, (md, r) in enumerate(ratings)
    ]

    avg_rating = sum(r for _, r in ratings) / len(ratings)
    min_y = max(4.0, min(r for _, r in ratings) - 0.5)
    max_y = min(10.0, max(r for _, r in ratings) + 0.5)

    line = ft.LineChartData(
        data_points=data_points,
        stroke_width=2.5,
        color=_GOLD,
        curved=True,
        stroke_cap_round=True,
        below_line_gradient=ft.LinearGradient(
            colors=[ft.Colors.with_opacity(0.25, _GOLD),
                    ft.Colors.with_opacity(0.0, _GOLD)],
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
        ),
    )

    # Average line
    avg_line = ft.LineChartData(
        data_points=[
            ft.LineChartDataPoint(x=0, y=avg_rating),
            ft.LineChartDataPoint(x=len(ratings) - 1, y=avg_rating),
        ],
        stroke_width=1,
        color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE),
        dash_pattern=[4, 4],
    )

    chart = ft.LineChart(
        data_series=[line, avg_line],
        width=width,
        height=height,
        min_x=0,
        max_x=max(len(ratings) - 1, 1),
        min_y=min_y,
        max_y=max_y,
        bgcolor="transparent",
        border=ft.border.all(1, _GRID),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=1, color=_GRID, width=0.5,
        ),
        left_axis=ft.ChartAxis(
            labels_size=28,
            labels=[
                ft.ChartAxisLabel(
                    value=v,
                    label=ft.Text(str(int(v)), size=9, color=_TEXT_MUTED),
                )
                for v in range(int(min_y), int(max_y) + 1)
            ],
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=22,
            labels=[
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(f"MD{md}", size=8, color=_TEXT_MUTED),
                )
                for i, (md, _) in enumerate(ratings)
                if i % max(1, len(ratings) // 5) == 0 or i == len(ratings) - 1
            ],
        ),
        tooltip_bgcolor=_BG_SURFACE,
    )

    return ft.Container(
        content=chart,
        padding=ft.padding.only(right=8, top=4),
    )


def player_stats_bar_chart(
    categories: dict[str, float],
    width: int = 340,
    height: int = 140,
) -> ft.Container:
    """
    Grouped bar chart for player attribute categories.

    Args:
        categories: dict like {"Technical": 14.2, "Physical": 12.5, ...}
    """
    if not categories:
        return ft.Container()

    bar_groups = []
    for i, (name, value) in enumerate(categories.items()):
        color = _GOLD if value >= 14 else _GREEN if value >= 10 else _AMBER if value >= 7 else _RED
        bar_groups.append(
            ft.BarChartGroup(
                x=i,
                bar_rods=[
                    ft.BarChartRod(
                        from_y=0,
                        to_y=value,
                        width=28,
                        color=color,
                        tooltip=f"{name}: {value:.1f}",
                        border_radius=ft.border_radius.only(
                            top_left=4, top_right=4,
                        ),
                        gradient=ft.LinearGradient(
                            colors=[ft.Colors.with_opacity(0.7, color), color],
                            begin=ft.Alignment(0, 1),
                            end=ft.Alignment(0, -1),
                        ),
                    ),
                ],
            )
        )

    chart = ft.BarChart(
        bar_groups=bar_groups,
        width=width,
        height=height,
        bgcolor="transparent",
        border=ft.border.all(1, _GRID),
        max_y=20,
        horizontal_grid_lines=ft.ChartGridLines(
            interval=5, color=_GRID, width=0.5,
        ),
        left_axis=ft.ChartAxis(
            labels_size=24,
            labels=[
                ft.ChartAxisLabel(value=v, label=ft.Text(str(v), size=9, color=_TEXT_MUTED))
                for v in [0, 5, 10, 15, 20]
            ],
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=30,
            labels=[
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(
                        name[:4], size=9, color=_TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                )
                for i, name in enumerate(categories.keys())
            ],
        ),
        tooltip_bgcolor=_BG_SURFACE,
    )

    return ft.Container(content=chart, padding=ft.padding.only(right=8, top=4))


def season_position_chart(
    positions: list[tuple[int, int]],
    total_teams: int = 18,
    width: int = 340,
    height: int = 140,
) -> ft.Container:
    """
    Line chart showing league position over matchdays (1 at top).

    Args:
        positions: list of (matchday, position) tuples.
        total_teams: number of teams in the league.
    """
    if not positions:
        return ft.Container(
            content=ft.Text("No position data yet", size=11, color=_TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
            width=width, height=50,
            alignment=ft.Alignment(0, 0),
        )

    data_points = [
        ft.LineChartDataPoint(
            x=i,
            y=total_teams + 1 - pos,  # invert: 1st place = highest y
            tooltip=f"MD {md}: {pos}{_ordinal(pos)}",
        )
        for i, (md, pos) in enumerate(positions)
    ]

    # Color based on latest position
    latest_pos = positions[-1][1]
    line_color = _GREEN if latest_pos <= 4 else _GOLD if latest_pos <= 8 else _AMBER if latest_pos <= 14 else _RED

    line = ft.LineChartData(
        data_points=data_points,
        stroke_width=2.5,
        color=line_color,
        curved=True,
        stroke_cap_round=True,
        below_line_gradient=ft.LinearGradient(
            colors=[ft.Colors.with_opacity(0.15, line_color),
                    ft.Colors.with_opacity(0.0, line_color)],
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
        ),
    )

    chart = ft.LineChart(
        data_series=[line],
        width=width,
        height=height,
        min_x=0,
        max_x=max(len(positions) - 1, 1),
        min_y=0,
        max_y=total_teams + 1,
        bgcolor="transparent",
        border=ft.border.all(1, _GRID),
        horizontal_grid_lines=ft.ChartGridLines(
            interval=total_teams // 3, color=_GRID, width=0.5,
        ),
        left_axis=ft.ChartAxis(
            labels_size=28,
            labels=[
                ft.ChartAxisLabel(
                    value=total_teams + 1 - v,
                    label=ft.Text(f"{v}", size=9, color=_TEXT_MUTED),
                )
                for v in [1, total_teams // 3, 2 * total_teams // 3, total_teams]
            ],
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=22,
            labels=[
                ft.ChartAxisLabel(
                    value=i,
                    label=ft.Text(f"{md}", size=8, color=_TEXT_MUTED),
                )
                for i, (md, _) in enumerate(positions)
                if i % max(1, len(positions) // 5) == 0 or i == len(positions) - 1
            ],
        ),
        tooltip_bgcolor=_BG_SURFACE,
    )

    return ft.Container(content=chart, padding=ft.padding.only(right=8, top=4))


def club_form_trend_line(
    results: list[str],
    width: int = 340,
    height: int = 100,
) -> ft.Container:
    """
    Mini trend line mapping W=3, D=1, L=0 over recent matches.

    Args:
        results: list of "W", "D", "L" strings, most recent first.
    """
    if not results:
        return ft.Container()

    # Reverse so oldest is first (left side of chart)
    ordered = list(reversed(results))

    points_map = {"W": 3, "D": 1, "L": 0}
    data_points = [
        ft.LineChartDataPoint(
            x=i,
            y=points_map.get(r, 0),
            tooltip=f"{'Win' if r == 'W' else 'Draw' if r == 'D' else 'Loss'}",
        )
        for i, r in enumerate(ordered)
    ]

    line = ft.LineChartData(
        data_points=data_points,
        stroke_width=2,
        color=_GOLD,
        curved=True,
        stroke_cap_round=True,
    )

    chart = ft.LineChart(
        data_series=[line],
        width=width,
        height=height,
        min_x=0,
        max_x=max(len(ordered) - 1, 1),
        min_y=-0.5,
        max_y=3.5,
        bgcolor="transparent",
        border=ft.border.all(1, _GRID),
        left_axis=ft.ChartAxis(
            labels_size=22,
            labels=[
                ft.ChartAxisLabel(value=0, label=ft.Text("L", size=9, color=_RED)),
                ft.ChartAxisLabel(value=1, label=ft.Text("D", size=9, color=_AMBER)),
                ft.ChartAxisLabel(value=3, label=ft.Text("W", size=9, color=_GREEN)),
            ],
        ),
        bottom_axis=ft.ChartAxis(labels_size=0),
        tooltip_bgcolor=_BG_SURFACE,
    )

    return ft.Container(content=chart)


def _ordinal(n: int) -> str:
    """Return ordinal suffix for a number (1st, 2nd, 3rd, etc.)."""
    if 11 <= n % 100 <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

