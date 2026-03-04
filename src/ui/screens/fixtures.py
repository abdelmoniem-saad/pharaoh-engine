"""
Fixtures screen — browse matchday results across the season.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.utils.localization import t, t_format
from src.ui.theme import (
    header_bar, GOLD_BORDER, CARD_GLASS, CARD_GLASS_STRONG, CARD_RADIUS_SM,
    TEXT_SECONDARY, TEXT_MUTED, ACCENT, PAGE_PADDING,
)


def build_fixtures_screen(page: ft.Page) -> ft.Column:
    """Build the fixtures/results browser."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 3)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text(t("no_game_loaded"))])

    conn = app_state.db_conn
    gs = app_state.game_state

    played_matchdays = queries.get_all_matchdays_played(conn)

    if not played_matchdays:
        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.CALENDAR_MONTH, size=48, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                ft.Text(t("no_matches_played"), size=16, color=ft.Colors.GREY_400),
                ft.Container(height=20),
                ft.ElevatedButton(f"← {t('league_table')}", width=200,
                                   on_click=lambda e: navigate(page, "/table"),
                                   style=ft.ButtonStyle(
                                       shape=ft.RoundedRectangleBorder(radius=12),
                                       bgcolor=ft.Colors.AMBER_700,
                                       color=ft.Colors.WHITE,
                                   )),
            ],
        )

    # Default to most recent played matchday
    selected_md = played_matchdays[0]

    # Build matchday selector options
    md_options = [ft.dropdown.Option(str(md)) for md in played_matchdays]

    # Build results for default matchday
    results_column = ft.Column(spacing=4)
    _populate_results(conn, gs, selected_md, results_column)

    def on_matchday_select(e):
        md = int(e.control.value)
        results_column.controls.clear()
        _populate_results(conn, gs, md, results_column)
        page.update()

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        header_bar(
                            title=t("fixture_results"),
                            icon=ft.Icons.CALENDAR_MONTH,
                            page=page,
                            back_route="/table",
                        ),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Dropdown(
                                    label=t("matchday"),
                                    value=str(selected_md),
                                    options=md_options,
                                    on_select=on_matchday_select,
                                    width=160,
                                ),
                                ft.ElevatedButton(
                                    f"← {t('league_table')}",
                                    on_click=lambda e: navigate(page, "/table"),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        side=ft.BorderSide(1, GOLD_BORDER),
                                    ),
                                ),
                            ],
                        ),
                        ft.Divider(height=1),
                        results_column,
                    ],
                ),
            ),
        ],
    )


def _populate_results(conn, gs, matchday: int, column: ft.Column):
    """Fill the column with fixture results for the given matchday."""
    results = queries.get_matchday_results(conn, matchday)
    all_fixtures = queries.get_fixtures_by_matchday(conn, matchday)

    # Played
    if results:
        column.controls.append(
            ft.Text(f"{t('matchday')} {matchday} — {len(results)} / {len(all_fixtures)}",
                     size=13, color=ft.Colors.GREY_500))

        for fixture in results:
            r = fixture.result
            if not r:
                continue

            is_user = (fixture.home_club_id == gs.user_club_id or
                       fixture.away_club_id == gs.user_club_id)
            bg = CARD_GLASS_STRONG if is_user else CARD_GLASS
            border = (ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.GREEN))
                      if is_user else ft.border.all(1, GOLD_BORDER))

            column.controls.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Text(
                                fixture.home_club_name, size=12,
                                text_align=ft.TextAlign.RIGHT, expand=True,
                                weight=ft.FontWeight.BOLD if fixture.home_club_id == gs.user_club_id else ft.FontWeight.NORMAL,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    f"{r.home_goals} - {r.away_goals}",
                                    size=13, weight=ft.FontWeight.BOLD,
                                ),
                                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=6,
                                border=ft.border.all(1, ft.Colors.with_opacity(0.12, "#FFD54F")),
                            ),
                            ft.Text(
                                fixture.away_club_name, size=12,
                                text_align=ft.TextAlign.LEFT, expand=True,
                                weight=ft.FontWeight.BOLD if fixture.away_club_id == gs.user_club_id else ft.FontWeight.NORMAL,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                    ),
                    bgcolor=bg,
                    border=border,
                    border_radius=CARD_RADIUS_SM,
                    padding=ft.padding.symmetric(vertical=6, horizontal=8),
                )
            )

    # Unplayed fixtures on this matchday
    unplayed = [f for f in all_fixtures if not f.played]
    if unplayed:
        column.controls.append(ft.Container(height=8))
        column.controls.append(
            ft.Text(t("upcoming"), size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500))
        for f in unplayed:
            column.controls.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Text(f.home_club_name, size=11,
                                     text_align=ft.TextAlign.RIGHT, expand=True,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text("vs", size=11, color=ft.Colors.GREY_600),
                            ft.Text(f.away_club_name, size=11,
                                     text_align=ft.TextAlign.LEFT, expand=True,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                    ),
                    padding=ft.padding.symmetric(vertical=4, horizontal=8),
                )
            )

    if not results and not unplayed:
        column.controls.append(
            ft.Text(t("no_fixtures_matchday"), size=13, color=ft.Colors.GREY_500))
