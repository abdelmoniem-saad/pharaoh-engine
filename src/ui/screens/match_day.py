"""
Match Day screen — pre-match info, simulate, and show results.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.calendar import simulate_user_match, advance_to_next_match, advance_day
from src.core.league import is_season_complete, get_champion
from src.utils.config import MatchEventType
from src.ui.widgets.nav_bar import build_nav_bar


def build_match_day_screen(page: ft.Page) -> ft.Column:
    """Build the match day content."""
    from src.ui.app import app_state, navigate

    # Set the navigation bar
    page.navigation_bar = build_nav_bar(page, 2)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    controls: list[ft.Control] = []

    # Header
    controls.append(ft.Text("⚽ Match Day", size=22, weight=ft.FontWeight.BOLD))
    controls.append(ft.Text(
        f"Date: {gs.current_date.strftime('%d %b %Y')}",
        size=13, color=ft.Colors.GREY_500,
    ))
    controls.append(ft.Divider(height=1))

    # Season complete?
    if is_season_complete(conn):
        champ = get_champion(conn)
        if champ:
            controls.append(ft.Container(height=30))
            controls.append(ft.Icon(ft.Icons.EMOJI_EVENTS, size=60, color=ft.Colors.AMBER_400))
            controls.append(ft.Text(
                "Season Complete!",
                size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300,
                text_align=ft.TextAlign.CENTER,
            ))
            controls.append(ft.Text(
                f"{champ.club_name} are CHAMPIONS!",
                size=18, weight=ft.FontWeight.W_500,
                text_align=ft.TextAlign.CENTER,
            ))
            controls.append(ft.Text(
                f"{champ.points} points",
                size=16, color=ft.Colors.GREY_400,
                text_align=ft.TextAlign.CENTER,
            ))
        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controls,
        )

    # Next fixture for user
    fixture = queries.get_user_next_fixture(conn, gs.user_club_id)

    if fixture:
        is_home = fixture.home_club_id == gs.user_club_id
        venue = "HOME" if is_home else "AWAY"
        venue_color = ft.Colors.GREEN_400 if is_home else ft.Colors.ORANGE_400

        # Match card
        match_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Text(
                            f"Matchday {fixture.matchday}",
                            size=14, color=ft.Colors.AMBER_300,
                            weight=ft.FontWeight.W_500,
                        ),
                        ft.Chip(
                            label=ft.Text(venue, size=11),
                            bgcolor=venue_color,
                        ),
                        ft.Container(height=5),
                        ft.Text(fixture.home_club_name, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text("vs", size=14, color=ft.Colors.GREY_500),
                        ft.Text(fixture.away_club_name, size=20, weight=ft.FontWeight.BOLD),
                    ],
                ),
                padding=20,
                alignment="center",
            ),
        )
        controls.append(match_card)

        if fixture.date and fixture.date > gs.current_date:
            days_until = (fixture.date - gs.current_date).days
            controls.append(ft.Text(
                f"Match in {days_until} day(s)",
                size=14, color=ft.Colors.GREY_400,
                text_align=ft.TextAlign.CENTER,
            ))

            def advance_click(e):
                advance_to_next_match(conn, gs)
                navigate(page, "/match_day")

            controls.append(ft.Button(
                "⏩ Advance to Match Day",
                width=280, height=50,
                on_click=advance_click,
            ))
        else:
            # Match is today
            def simulate_click(e):
                result = simulate_user_match(conn, gs)
                if result:
                    _show_result_dialog(page, result)
                advance_day(conn, gs)
                navigate(page, "/match_day")

            controls.append(ft.Container(height=10))
            controls.append(ft.FilledButton(
                "▶  SIMULATE MATCH",
                width=280, height=55,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_700,
                    text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
                ),
                on_click=simulate_click,
            ))
    else:
        controls.append(ft.Container(height=20))
        controls.append(ft.Text(
            "No upcoming match found.",
            size=16, color=ft.Colors.GREY_400,
            text_align=ft.TextAlign.CENTER,
        ))

        def advance_one(e):
            advance_day(conn, gs)
            navigate(page, "/match_day")

        controls.append(ft.Button(
            "⏩ Advance Day", width=250, height=45,
            on_click=advance_one,
        ))

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=15,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=controls,
                ),
            ),
        ],
    )


def _show_result_dialog(page: ft.Page, result):
    """Show match result in a dialog."""
    # Goal events
    goal_widgets = []
    goals = [e for e in result.events if e.event_type == MatchEventType.GOAL]
    for g in goals:
        text = f"⚽ {g.minute}' {g.player_name}"
        if g.second_player_name:
            text += f" (assist: {g.second_player_name})"
        goal_widgets.append(ft.Text(text, size=13))

    if not goal_widgets:
        goal_widgets.append(ft.Text("No goals", size=13, italic=True, color=ft.Colors.GREY_500))

    # Stats table
    stats_rows = [
        ("Possession", f"{result.home_stats.possession:.0f}%", f"{result.away_stats.possession:.0f}%"),
        ("Shots", str(result.home_stats.shots), str(result.away_stats.shots)),
        ("On Target", str(result.home_stats.shots_on_target), str(result.away_stats.shots_on_target)),
        ("Corners", str(result.home_stats.corners), str(result.away_stats.corners)),
        ("Fouls", str(result.home_stats.fouls), str(result.away_stats.fouls)),
        ("Yellow Cards", str(result.home_stats.yellow_cards), str(result.away_stats.yellow_cards)),
    ]
    stat_widgets = []
    for label, home_val, away_val in stats_rows:
        stat_widgets.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(home_val, size=12, width=40, text_align=ft.TextAlign.CENTER),
                    ft.Text(label, size=11, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
                    ft.Text(away_val, size=12, width=40, text_align=ft.TextAlign.CENTER),
                ],
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text(
            result.score_display,
            size=22, weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Divider(),
                    ft.Text("Goals", size=14, weight=ft.FontWeight.W_500),
                    *goal_widgets,
                    ft.Divider(),
                    ft.Text("Match Stats", size=14, weight=ft.FontWeight.W_500),
                    *stat_widgets,
                ],
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=320,
            height=350,
        ),
        actions=[
            ft.TextButton("OK", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)
