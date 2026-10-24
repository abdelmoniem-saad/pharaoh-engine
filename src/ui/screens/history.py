"""
History screen — browse past seasons, all-time records, and player/club archives.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.utils.localization import t


def build_history_screen(page: ft.Page) -> ft.Column:
    """Build the History / Records screen."""
    from src.ui.app import app_state

    page.navigation_bar = build_nav_bar(page, 3)  # same slot as table

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("no_game_loaded"), rtl=theme.rtl())])

    conn = app_state.db_conn
    gs = app_state.game_state

    # ── Build tab contents ────────────────────────────────────────────
    seasons_tab = _build_seasons_tab(conn, gs)
    records_tab = _build_records_tab(conn)
    club_tab = _build_club_history_tab(conn, gs)

    content_area = ft.Container(rtl=theme.rtl(), content=seasons_tab, expand=True)

    def switch_tab(idx):
        views = [seasons_tab, records_tab, club_tab]
        content_area.content = views[idx]
        # Update button styles
        for i, btn in enumerate(tab_buttons):
            if i == idx:
                btn.style = ft.ButtonStyle(
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER),
                    color=theme.GOLD,
                )
            else:
                btn.style = ft.ButtonStyle(
                    bgcolor=ft.Colors.TRANSPARENT,
                    color=theme.TEXT_MUTED,
                )
        page.update()

    tab_buttons = [
        ft.TextButton(t("seasons"), rtl=theme.rtl(), height=44, expand=True, on_click=lambda e: switch_tab(0),
                       style=ft.ButtonStyle(
                           bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER),
                           color=theme.GOLD)),
        ft.TextButton(t("records"), rtl=theme.rtl(), height=44, expand=True, on_click=lambda e: switch_tab(1),
                       style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT,
                                            color=theme.TEXT_MUTED)),
        ft.TextButton(t("my_club"), rtl=theme.rtl(), height=44, expand=True, on_click=lambda e: switch_tab(2),
                       style=ft.ButtonStyle(bgcolor=ft.Colors.TRANSPARENT,
                                            color=theme.TEXT_MUTED)),
    ]

    tab_bar = ft.Container(
        rtl=theme.rtl(), content=ft.Row(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER,
            spacing=4,
            controls=tab_buttons,
        ),
        padding=ft.padding.symmetric(horizontal=theme.PAGE_PADDING, vertical=4),
    )

    return ft.Column(
        rtl=theme.rtl(), expand=True,
        spacing=0,
        controls=[
            theme.screen_container(
                ft.Column(
                    rtl=theme.rtl(), expand=True,
                    spacing=0,
                    controls=[
                        theme.header_bar(
                            title=t("history"),
                            subtitle=t("past_seasons_stats"),
                            back_route="/club",
                            page=page,
                        ),
                        tab_bar,
                        ft.Container(
                            rtl=theme.rtl(), content=content_area,
                            expand=True,
                            padding=ft.padding.only(left=theme.PAGE_PADDING, right=theme.PAGE_PADDING,
                                                     top=4, bottom=10),
                        ),
                    ],
                ),
                page=page,
            ),
        ],
    )


# ── Seasons Tab ──────────────────────────────────────────────────────────────

def _build_seasons_tab(conn, gs) -> ft.Container:
    """List of all completed seasons with key stats."""
    seasons = queries.get_season_history(conn)

    if not seasons:
        return ft.Container(
            rtl=theme.rtl(), content=ft.Column(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.HISTORY, rtl=theme.rtl(), size=48, color=theme.TEXT_MUTED),
                    ft.Container(rtl=theme.rtl(), height=12),
                    ft.Text(t("no_seasons"), rtl=theme.rtl(), size=theme.BODY_SIZE,
                            color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.Text(t("history_hint"),
                            rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
                ],
            ),
            expand=True,
        )

    rows = []
    for s in seasons:
        is_champ = s.user_position == 1
        pos_color = (theme.TEXT_SUCCESS if s.user_position <= 4
                     else theme.TEXT_WARNING if s.user_position <= 10
                     else theme.TEXT_DANGER)

        rows.append(ft.Container(
            rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=4, controls=[
                # Season header
                ft.Row(
                    rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"🏟️ {s.season_display}", rtl=theme.rtl(), size=theme.BODY_SIZE,
                                weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                        ft.Container(
                            rtl=theme.rtl(), content=ft.Text(
                                f"{'🏆 ' if is_champ else ''}#{s.user_position}",
                                rtl=theme.rtl(), size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                                color=pos_color,
                            ),
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.1, pos_color),
                        ),
                    ],
                ),
                # Champion & stats
                ft.Row(rtl=theme.rtl(), spacing=4, controls=[
                    ft.Text("🏆", rtl=theme.rtl(), size=theme.TINY_SIZE),
                    ft.Text(s.champion_club_name or "—", rtl=theme.rtl(), size=theme.CAPTION_SIZE,
                            color=theme.GOLD, weight=ft.FontWeight.W_500),
                    ft.Container(rtl=theme.rtl(), expand=True),
                    ft.Text(f"⚽ {s.total_goals}", rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
                    ft.Text(f"📋 {s.total_matches}", rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
                ]),
                # Awards row
                ft.Row(rtl=theme.rtl(), spacing=0, wrap=True, controls=[
                    _award_chip("👟", s.golden_boot_player, f"{s.golden_boot_goals}g")
                    if s.golden_boot_player else ft.Container(rtl=theme.rtl()),
                    _award_chip("🧤", s.golden_glove_player, f"{s.golden_glove_clean_sheets}cs")
                    if s.golden_glove_player else ft.Container(rtl=theme.rtl()),
                    _award_chip("🅰️", s.most_assists_player, f"{s.most_assists_count}a")
                    if s.most_assists_player else ft.Container(rtl=theme.rtl()),
                ]),
            ]),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=10,
            bgcolor=theme.CARD_GLASS_STRONG if is_champ else theme.CARD_GLASS,
            border=ft.border.all(1, theme.GOLD_BORDER_STRONG if is_champ else theme.GOLD_BORDER),
            margin=ft.margin.only(bottom=6),
        ))

    return ft.Container(
        rtl=theme.rtl(), content=ft.ListView(
            rtl=theme.rtl(), spacing=0,
            controls=rows,
            expand=True,
        ),
        expand=True,
        padding=ft.padding.only(top=8),
    )


def _award_chip(emoji: str, name: str, stat: str) -> ft.Container:
    """Small chip showing an award winner."""
    return ft.Container(
        rtl=theme.rtl(), content=ft.Row(rtl=theme.rtl(), spacing=3, controls=[
            ft.Text(emoji, rtl=theme.rtl(), size=10),
            ft.Text(name, rtl=theme.rtl(), size=11, color=theme.TEXT_SECONDARY),
            ft.Text(stat, rtl=theme.rtl(), size=11, color=theme.GOLD,
                    weight=ft.FontWeight.BOLD),
        ]),
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.AMBER),
        margin=ft.margin.only(right=4, bottom=2),
    )


# ── Records Tab ──────────────────────────────────────────────────────────────

def _build_records_tab(conn) -> ft.Container:
    """All-time top scorers, assisters, and best rated players."""
    top_scorers = queries.get_all_time_top_scorers(conn, limit=15)
    top_assists = queries.get_all_time_top_assists(conn, limit=15)
    top_rated = queries.get_all_time_top_rated(conn, limit=15, min_appearances=5)

    if not top_scorers and not top_assists and not top_rated:
        return ft.Container(
            rtl=theme.rtl(), content=ft.Column(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.STAR_BORDER, rtl=theme.rtl(), size=48, color=theme.TEXT_MUTED),
                    ft.Container(rtl=theme.rtl(), height=12),
                    ft.Text(t("no_records"), rtl=theme.rtl(), size=theme.BODY_SIZE,
                            color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.Text(t("records_hint"),
                            rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
                ],
            ),
            expand=True,
        )

    sections = []

    # Top Scorers
    if top_scorers:
        sections.append(_record_section(t("all_time_scorers"), top_scorers,
                                         stat_key="total_goals", stat_label=t("goals")))

    # Top Assists
    if top_assists:
        sections.append(_record_section(t("all_time_assists"), top_assists,
                                         stat_key="total_assists", stat_label=t("assists")))

    # Top Rated
    if top_rated:
        sections.append(_record_section(t("all_time_rated"), top_rated,
                                         stat_key="avg_rating", stat_label=t("rating"),
                                         is_float=True))

    return ft.Container(
        rtl=theme.rtl(), content=ft.ListView(
            rtl=theme.rtl(), spacing=theme.SECTION_SPACING,
            controls=sections,
            expand=True,
        ),
        expand=True,
        padding=ft.padding.only(top=8),
    )


def _record_section(title: str, records: list[dict], stat_key: str,
                     stat_label: str, is_float: bool = False) -> ft.Container:
    """A titled section showing a ranked list of player records."""
    rows = []
    for i, r in enumerate(records, 1):
        rank_color = (theme.GOLD if i == 1
                      else ft.Colors.GREY_300 if i == 2
                      else ft.Colors.ORANGE_300 if i == 3
                      else theme.TEXT_MUTED)
        stat_val = r[stat_key]
        stat_display = f"{stat_val:.1f}" if is_float else str(stat_val)

        rows.append(ft.Container(
            rtl=theme.rtl(), content=ft.Row(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                        ft.Text(f"{i}.", rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=rank_color,
                                weight=ft.FontWeight.BOLD, width=22),
                        ft.Column(rtl=theme.rtl(), spacing=0, expand=True, controls=[
                            ft.Text(r["player_name"], rtl=theme.rtl(), size=theme.CAPTION_SIZE,
                                    weight=ft.FontWeight.W_500, color=theme.TEXT_PRIMARY),
                            ft.Text(
                                f"{r.get('last_club', '')} · {r.get('seasons_played', 0)} seasons · "
                                f"{r.get('total_appearances', 0)} apps",
                                rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED,
                            ),
                        ]),
                    ], expand=True),
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Text(stat_display, rtl=theme.rtl(), size=theme.BODY_SIZE,
                                        weight=ft.FontWeight.BOLD,
                                        color=theme.GOLD),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=6,
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER),
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=12),
        ))

    return ft.Container(
        rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=2, controls=[
            ft.Text(title, rtl=theme.rtl(), size=theme.BODY_SIZE, weight=ft.FontWeight.BOLD,
                    color=theme.GOLD),
            ft.Container(rtl=theme.rtl(), height=2),
            *rows,
        ]),
        padding=ft.padding.symmetric(horizontal=8, vertical=8),
        border_radius=10,
        bgcolor=theme.CARD_GLASS,
        border=ft.border.all(1, theme.GOLD_BORDER),
    )


# ── Club History Tab ─────────────────────────────────────────────────────────

def _build_club_history_tab(conn, gs) -> ft.Container:
    """Show the user's club season-by-season performance."""
    club_history = queries.get_club_history(conn, gs.user_club_id)

    if not club_history:
        return ft.Container(
            rtl=theme.rtl(), content=ft.Column(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Icon(ft.Icons.SHIELD_OUTLINED, rtl=theme.rtl(), size=48, color=theme.TEXT_MUTED),
                    ft.Container(rtl=theme.rtl(), height=12),
                    ft.Text(t("no_seasons"), rtl=theme.rtl(), size=theme.BODY_SIZE,
                            color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.Text(t("history_hint"),
                            rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED,
                            text_align=ft.TextAlign.CENTER),
                ],
            ),
            expand=True,
        )

    # Summary stats
    total_seasons = len(club_history)
    titles_won = sum(1 for c in club_history if c.position_finish == 1)
    top_4_finishes = sum(1 for c in club_history if c.position_finish <= 4)
    total_wins = sum(c.won for c in club_history)
    total_goals = sum(c.goals_for for c in club_history)
    best_finish = min(c.position_finish for c in club_history) if club_history else 0

    summary = ft.Container(
        rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=4, controls=[
            ft.Text(f"{gs.user_club_name} · {t('career_summary')}", rtl=theme.rtl(), size=theme.BODY_SIZE,
                    weight=ft.FontWeight.BOLD, color=theme.GOLD),
            ft.Row(rtl=theme.rtl(), wrap=True, spacing=0, controls=[
                _stat_chip("🏆", t("titles"), str(titles_won)),
                _stat_chip("🥇", "Top 4", str(top_4_finishes)),
                _stat_chip("📋", t("seasons"), str(total_seasons)),
                _stat_chip("✅", t("wins"), str(total_wins)),
                _stat_chip("⚽", t("goals"), str(total_goals)),
                _stat_chip("🔝", "Best", f"#{best_finish}"),
            ]),
        ]),
        padding=ft.padding.symmetric(horizontal=10, vertical=8),
        border_radius=10,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.all(1, theme.GOLD_BORDER_STRONG),
        margin=ft.margin.only(bottom=8),
    )

    # Season-by-season rows
    season_rows = []
    for c in club_history:
        is_champ = c.position_finish == 1
        pos_color = (theme.TEXT_SUCCESS if c.position_finish <= 4
                     else theme.TEXT_WARNING if c.position_finish <= 10
                     else theme.TEXT_DANGER)

        season_rows.append(ft.Container(
            rtl=theme.rtl(), content=ft.Row(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(rtl=theme.rtl(), spacing=0, controls=[
                        ft.Text(
                            f"{'🏆 ' if is_champ else ''}{c.season_year}/{c.season_year + 1}",
                            rtl=theme.rtl(), size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                            color=theme.GOLD if is_champ else theme.TEXT_PRIMARY,
                        ),
                        ft.Text(
                            f"W{c.won} D{c.drawn} L{c.lost} · "
                            f"GF {c.goals_for} GA {c.goals_against} "
                            f"({c.goal_difference:+d})",
                            rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED,
                        ),
                    ]),
                    ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                        ft.Text(f"{c.points}pts", rtl=theme.rtl(), size=theme.CAPTION_SIZE,
                                color=theme.TEXT_SECONDARY),
                        ft.Container(
                            rtl=theme.rtl(), content=ft.Text(f"#{c.position_finish}", rtl=theme.rtl(), size=theme.CAPTION_SIZE,
                                            weight=ft.FontWeight.BOLD, color=pos_color),
                            padding=ft.padding.symmetric(horizontal=6, vertical=2),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.1, pos_color),
                        ),
                    ]),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=10, vertical=12),
            border_radius=8,
            bgcolor=theme.CARD_GLASS_STRONG if is_champ else theme.CARD_GLASS,
            border=ft.border.all(1, theme.GOLD_BORDER_STRONG if is_champ else theme.GOLD_BORDER),
            margin=ft.margin.only(bottom=4),
        ))

    return ft.Container(
        rtl=theme.rtl(), content=ft.ListView(
            rtl=theme.rtl(), spacing=0,
            controls=[summary, *season_rows],
            expand=True,
        ),
        expand=True,
        padding=ft.padding.only(top=8),
    )


def _stat_chip(emoji: str, label: str, value: str) -> ft.Container:
    """Small stat chip for the summary section."""
    return ft.Container(
        rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                          controls=[
            ft.Text(f"{emoji} {value}", rtl=theme.rtl(), size=theme.CAPTION_SIZE,
                    weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
            ft.Text(label, rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
        ]),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        margin=ft.margin.only(right=4, bottom=2),
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.AMBER),
    )


