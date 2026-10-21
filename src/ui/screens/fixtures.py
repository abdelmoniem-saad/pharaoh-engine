"""
Fixtures screen — browse matchday results across the season.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.utils.localization import t, t_format


def build_fixtures_screen(page: ft.Page) -> ft.Column:
    """Build the fixtures/results browser."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 3)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text(t("no_game_loaded"))])

    conn = app_state.db_conn
    gs = app_state.game_state

    # Competition view state (shared with table screen state if possible)
    active_comp = getattr(page, "_comp_view", "league")
    all_matchdays = queries.get_all_matchdays(conn)

    # ── State Management ──────────────────────────────────────────
    results_column = ft.Column(spacing=4)
    md_dropdown = ft.Dropdown(width=160)

    def update_view():
        comp = page._comp_view
        
        # Filter matchdays
        if comp == "cup":
            filtered_mds = [0] if 0 in all_matchdays else []
            selected_md = 0
        else:
            filtered_mds = [md for md in all_matchdays if md > 0]
            current_md = queries.get_current_matchday(conn)
            selected_md = current_md if current_md in filtered_mds else (filtered_mds[0] if filtered_mds else 1)

        # Update Dropdown
        md_dropdown.options = [
            ft.dropdown.Option(key=str(md), text=t("cup") if md == 0 else f"{t('matchday')} {md}")
            for md in filtered_mds
        ]
        md_dropdown.value = str(selected_md)
        md_dropdown.visible = len(filtered_mds) > 1 or (comp == "league" and len(filtered_mds) > 0)
        
        # Update results
        results_column.controls.clear()
        _populate_results(conn, gs, selected_md, results_column)
        page.update()

    def switch_comp(comp_name: str):
        page._comp_view = comp_name
        update_view()

    # ── UI Components ─────────────────────────────────────────────
    toggle = ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.TextButton(
                    t("league").upper(),
                    style=ft.ButtonStyle(
                        color=theme.ACCENT if active_comp == "league" else theme.TEXT_SECONDARY,
                        bgcolor=ft.Colors.with_opacity(0.1, theme.ACCENT) if active_comp == "league" else ft.Colors.TRANSPARENT,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: switch_comp("league"),
                ),
                ft.Icon(ft.Icons.SWAP_HORIZ, size=16, color=theme.TEXT_MUTED),
                ft.TextButton(
                    t("cup").upper(),
                    style=ft.ButtonStyle(
                        color=theme.ACCENT if active_comp == "cup" else theme.TEXT_SECONDARY,
                        bgcolor=ft.Colors.with_opacity(0.1, theme.ACCENT) if active_comp == "cup" else ft.Colors.TRANSPARENT,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: switch_comp("cup"),
                ),
            ],
        ),
        margin=ft.margin.only(bottom=10),
    )

    md_dropdown.on_change = lambda e: (
        results_column.controls.clear(),
        _populate_results(conn, gs, int(e.control.value), results_column),
        page.update()
    )

    # Initial population
    # Use a small delay/timeout or just set values directly if we're inside build
    filtered_mds = [md for md in all_matchdays if (md == 0 if active_comp == "cup" else md > 0)]
    if active_comp == "cup":
        selected_md = 0
    else:
        current_md = queries.get_current_matchday(conn)
        selected_md = current_md if current_md in filtered_mds else (filtered_mds[0] if filtered_mds else 1)

    md_dropdown.options = [
        ft.dropdown.Option(key=str(md), text=t("cup") if md == 0 else f"{t('matchday')} {md}")
        for md in filtered_mds
    ]
    md_dropdown.value = str(selected_md)
    md_dropdown.visible = (active_comp == "league")
    _populate_results(conn, gs, selected_md, results_column)

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        theme.header_bar(
                            title=t("fixture_results"),
                            icon=ft.Icons.CALENDAR_MONTH,
                            page=page,
                            back_route="/table",
                        ),
                        toggle,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                md_dropdown,
                                ft.OutlinedButton(
                                    f"← {t('competition')}",
                                    on_click=lambda e: navigate(page, "/table"),
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=10),
                                        side=ft.BorderSide(1, theme.GOLD_BORDER),
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
        label = t("cup") if matchday == 0 else f"{t('matchday')} {matchday}"
        column.controls.append(
            ft.Text(f"{label} — {len(results)} / {len(all_fixtures)}",
                     size=13, color=ft.Colors.GREY_500))

        for fixture in results:
            r = fixture.result
            if not r:
                continue

            is_user = (fixture.home_club_id == gs.user_club_id or
                       fixture.away_club_id == gs.user_club_id)
            bg = theme.CARD_GLASS_STRONG if is_user else theme.CARD_GLASS
            border = (ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.GREEN))
                      if is_user else ft.border.all(1, theme.GOLD_BORDER))

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
                                border=ft.border.all(1, ft.Colors.with_opacity(0.12, theme.GOLD)),
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
                    border_radius=theme.CARD_RADIUS_SM,
                    padding=ft.padding.symmetric(vertical=6, horizontal=8),
                )
            )

    # Unplayed fixtures on this matchday
    unplayed = [f for f in all_fixtures if not f.played]
    if unplayed:
        column.controls.append(ft.Container(height=8))
        label = t("cup") if matchday == 0 else f"{t('matchday')} {matchday}"
        if not results:
            column.controls.append(
                ft.Text(f"{label} — 0 / {len(all_fixtures)}",
                         size=13, color=ft.Colors.GREY_500))
        column.controls.append(
            ft.Text(t("upcoming"), size=12, color=ft.Colors.GREY_600, weight=ft.FontWeight.W_500))
        for f in unplayed:
            date_str = f.date.strftime("%d %b %Y") if f.date else ""
            column.controls.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=6,
                        controls=[
                            ft.Text(f.home_club_name, size=11,
                                     text_align=ft.TextAlign.RIGHT, expand=True,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Column(
                                spacing=0,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                controls=[
                                    ft.Text("vs", size=11, color=ft.Colors.GREY_600),
                                    ft.Text(date_str, size=9, color=ft.Colors.GREY_500) if date_str else ft.Container()
                                ]
                            ),
                            ft.Text(f.away_club_name, size=11,
                                     text_align=ft.TextAlign.LEFT, expand=True,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                    ),
                    padding=ft.padding.symmetric(vertical=4, horizontal=8),
                )
            )

    if not results and not unplayed:
        from src.ui.widgets.cards import empty_state
        column.controls.append(empty_state(
            ft.Icons.EVENT_NOTE, t("no_fixtures_matchday")))
