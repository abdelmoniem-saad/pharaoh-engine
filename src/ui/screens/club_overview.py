"""
Club Overview screen — finances, board confidence, fan happiness, top scorers.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.finance import calculate_monthly_income, calculate_monthly_expenses, monthly_cash_flow
from src.core.board import get_confidence_level
from src.core.fans import get_fan_happiness_level, get_atmosphere_description
from src.core.club import get_squad_average_age, get_squad_average_ability, calculate_wage_bill
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.cards import section_card, info_tile, kv_row, action_card
from src.ui.theme import (
    ACCENT, TEXT_SECONDARY, TEXT_MUTED, TEXT_SUCCESS, TEXT_WARNING, TEXT_DANGER,
    PAGE_PADDING, SECTION_SPACING, TITLE_SIZE, CAPTION_SIZE,
    GOLD_BORDER, header_bar, CARD_GLASS, CARD_GLASS_STRONG,
)
from src.utils.config import expectation_display, expectation_description
from src.utils.localization import t


def build_club_overview_screen(page: ft.Page) -> ft.Column:
    """Build the club overview / hub screen."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 3)  # table index since accessed from there

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text(t("no_game_loaded"))])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    squad = queries.get_players_by_club(conn, club.id)

    # Finance calculations
    income = calculate_monthly_income(club)
    expenses = calculate_monthly_expenses(club)
    net = monthly_cash_flow(club)
    wage_bill = calculate_wage_bill(squad)

    # Board & Fans
    confidence = get_confidence_level(club.board_confidence)
    fan_level = get_fan_happiness_level(club.fan_happiness)
    atmosphere = get_atmosphere_description(club.fan_happiness)

    # Squad stats
    avg_age = get_squad_average_age(squad)
    avg_ability = get_squad_average_ability(squad)
    injured_count = sum(1 for p in squad if p.injury_days_remaining > 0)
    suspended_count = sum(1 for p in squad if p.suspension_matches > 0)

    # Top scorers from user's squad
    squad_scorers = sorted(
        [p for p in squad if p.season_stats.goals > 0],
        key=lambda p: p.season_stats.goals, reverse=True
    )[:5]

    # League top scorers
    league_scorers = queries.get_top_scorers(conn, limit=10)

    # Confidence color
    conf_color = (
        ft.Colors.GREEN_400 if club.board_confidence >= 60
        else ft.Colors.YELLOW_400 if club.board_confidence >= 35
        else ft.Colors.RED_400
    )
    fan_color = (
        ft.Colors.GREEN_400 if club.fan_happiness >= 60
        else ft.Colors.YELLOW_400 if club.fan_happiness >= 35
        else ft.Colors.RED_400
    )

    net_color = ft.Colors.GREEN_400 if net >= 0 else ft.Colors.RED_400

    # ── Tab content containers ─────────────────────────────────────
    # We use manual visibility toggling (like transfers screen) since
    # ft.Tabs in 0.80 uses a content+length API that doesn't directly
    # hold child widgets per tab.

    active_tab = [0]

    # ── Overview tab ─────────────────────────────────────────────────
    overview_controls = [
        # Next match card
        *_build_next_match_card(conn, gs, club),

        # Season Expectation
        section_card("🎯 Season Expectation", [
            ft.Text(
                expectation_display(club.season_expectation),
                size=15, weight=ft.FontWeight.BOLD, color=ACCENT,
            ),
            ft.Text(
                expectation_description(club.season_expectation),
                size=12, color=TEXT_SECONDARY, italic=True,
            ),
        ], title_color=ft.Colors.ORANGE_400),

        # League Position Chart (collapsed)
        *_build_position_chart(conn, gs),

        # Form Trend (collapsed)
        *_build_form_trend(conn, gs),
    ]

    overview_content = ft.Column(spacing=SECTION_SPACING, controls=overview_controls)

    # ── Finances tab ─────────────────────────────────────────────────
    finances_controls = [
        section_card("💰 Monthly Finances", [
            kv_row("Balance", f"{club.finances.balance:,} EGP"),
            kv_row("Monthly Income", f"+{income:,} EGP", TEXT_SUCCESS),
            kv_row("Monthly Expenses", f"-{expenses:,} EGP", TEXT_DANGER),
            kv_row("Net Cash Flow", f"{'+' if net >= 0 else ''}{net:,} EGP", net_color),
            kv_row("Weekly Wage Bill", f"{wage_bill:,} EGP"),
            kv_row("Transfer Budget", f"{club.finances.transfer_budget:,} EGP"),
        ], title_color=TEXT_SUCCESS),

        section_card("🏟️ Club Info", [
            kv_row("Stadium", f"{club.stadium_name} ({club.stadium_capacity:,})"),
            kv_row("City", club.city),
            kv_row("Reputation", f"{'⭐' * (club.reputation // 40 + 1)} {club.reputation}"),
            kv_row("Facilities", f"Lv.{club.facilities_level}"),
            kv_row("Youth Rating", f"Lv.{club.youth_rating}"),
            kv_row("Squad Size", str(len(squad))),
            kv_row("Avg Age", f"{avg_age:.1f}"),
        ], title_color=ft.Colors.BLUE_400),
    ]

    finances_content = ft.Column(spacing=SECTION_SPACING, controls=finances_controls,
                                  visible=False)

    # ── Squad Health tab ─────────────────────────────────────────────
    squad_health_controls = []

    # Injured players
    injured_players = [p for p in squad if p.injury_days_remaining > 0]
    if injured_players:
        injury_rows = [
            kv_row(p.name, f"{p.injury_type} ({p.injury_days_remaining}d)", TEXT_DANGER)
            for p in injured_players
        ]
        squad_health_controls.append(
            section_card("🏥 Injured Players", injury_rows, title_color=TEXT_DANGER))
    else:
        squad_health_controls.append(
            ft.Text("No injuries — squad is fully fit! ✅", size=12, color=TEXT_SUCCESS))

    # Suspended players
    suspended_players = [p for p in squad if p.suspension_matches > 0]
    if suspended_players:
        susp_rows = [
            kv_row(p.name, f"{p.suspension_matches} match(es)", TEXT_WARNING)
            for p in suspended_players
        ]
        squad_health_controls.append(
            section_card("🚫 Suspended", susp_rows, title_color=TEXT_WARNING))

    # Squad top scorers
    if squad_scorers:
        scorer_rows = []
        for p in squad_scorers:
            scorer_rows.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(p.name, size=12, expand=True, max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Row(spacing=8, tight=True, controls=[
                                ft.Text(f"⚽{p.season_stats.goals}", size=12,
                                        weight=ft.FontWeight.BOLD, color=ACCENT),
                                ft.Text(f"🅰️{p.season_stats.assists}", size=12),
                                ft.Text(p.position.value, size=10, color=TEXT_SECONDARY),
                            ]),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                )
            )
        squad_health_controls.append(
            section_card("⚽ Top Scorers", scorer_rows, title_color=ACCENT))

    # League top scorers
    if league_scorers:
        league_rows = []
        for i, scorer in enumerate(league_scorers, 1):
            is_user_player = scorer.get("club_short") == club.short_name
            league_rows.append(
                ft.Container(
                    content=ft.Row(
                        spacing=4,
                        controls=[
                            ft.Text(f"{i}.", size=CAPTION_SIZE, width=18, color=TEXT_MUTED),
                            ft.Text(scorer["name"], size=12, expand=True,
                                    weight=ft.FontWeight.BOLD if is_user_player else ft.FontWeight.NORMAL,
                                    color=TEXT_SUCCESS if is_user_player else None,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"⚽{scorer['goals']}", size=12,
                                    weight=ft.FontWeight.BOLD, color=ACCENT),
                            ft.Text(scorer.get("club_short", ""), size=10, color=TEXT_MUTED,
                                    width=40),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=4, vertical=2),
                )
            )
        squad_health_controls.append(
            section_card("🏆 League Top Scorers", league_rows))

    squad_health_content = ft.Column(spacing=SECTION_SPACING,
                                      controls=squad_health_controls, visible=False)

    # ── Tab switching ────────────────────────────────────────────────
    tab_contents = [overview_content, finances_content, squad_health_content]

    def switch_tab(idx):
        def handler(e):
            active_tab[0] = idx
            for i, tc in enumerate(tab_contents):
                tc.visible = (i == idx)
            # Update tab button styles
            for i, btn in enumerate(tab_buttons):
                if i == idx:
                    btn.style = ft.ButtonStyle(
                        bgcolor=ft.Colors.AMBER_800, color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=10),
                    )
                else:
                    btn.style = ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                        side=ft.BorderSide(1, GOLD_BORDER),
                    )
            page.update()
        return handler

    tab_buttons = [
        ft.ElevatedButton("📋 Overview", on_click=switch_tab(0), height=34,
                           style=ft.ButtonStyle(
                               bgcolor=ft.Colors.AMBER_800, color=ft.Colors.WHITE,
                               shape=ft.RoundedRectangleBorder(radius=10),
                           )),
        ft.OutlinedButton("💰 Finances", on_click=switch_tab(1), height=34,
                           style=ft.ButtonStyle(
                               shape=ft.RoundedRectangleBorder(radius=10),
                               side=ft.BorderSide(1, GOLD_BORDER),
                           )),
        ft.OutlinedButton("🏥 Squad", on_click=switch_tab(2), height=34,
                           style=ft.ButtonStyle(
                               shape=ft.RoundedRectangleBorder(radius=10),
                               side=ft.BorderSide(1, GOLD_BORDER),
                           )),
    ]

    # ── Status strip (always visible) ────────────────────────────────
    status_strip = ft.Row(
        spacing=6, scroll=ft.ScrollMode.AUTO,
        controls=[
            info_tile("Board", f"{club.board_confidence}%", icon=ft.Icons.ACCOUNT_BALANCE,
                      color=conf_color),
            info_tile("Fans", f"{club.fan_happiness}%", icon=ft.Icons.PEOPLE,
                      color=fan_color),
            info_tile("Balance", f"{club.finances.balance // 1000:,}K",
                      icon=ft.Icons.ACCOUNT_BALANCE_WALLET),
        ],
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.all(PAGE_PADDING),
                content=ft.Column(
                    spacing=SECTION_SPACING,
                    controls=[
                        header_bar(
                            title=club.name,
                            subtitle=f"👤 {gs.manager_name}  •  📅 {gs.current_date.strftime('%d %b %Y')}",
                            icon=ft.Icons.STADIUM,
                            page=page,
                            back_route="/squad",
                        ),

                        # Key status at a glance
                        status_strip,

                        # Tab bar
                        ft.Row(spacing=6, controls=tab_buttons),

                        # Tab contents (only one visible at a time)
                        overview_content,
                        finances_content,
                        squad_health_content,

                        # History link (only link kept — not on any tab)
                        action_card("📜 History & Records",
                                     subtitle="Past seasons, all-time stats",
                                     icon=ft.Icons.HISTORY,
                                     on_click=lambda e: navigate(page, "/history")),
                    ],
                ),
            ),
        ],
    )


def _build_next_match_card(conn, gs, club) -> list:
    """Build a dashboard card for the next match."""
    fixture = queries.get_user_next_fixture(conn, gs.user_club_id)
    if not fixture:
        return [ft.Text("No upcoming match", size=13, color=ft.Colors.GREY_500)]

    is_home = fixture.home_club_id == gs.user_club_id
    opp_name = fixture.away_club_name if is_home else fixture.home_club_name
    venue = "🏟️ HOME" if is_home else "✈️ AWAY"
    venue_color = ft.Colors.GREEN_400 if is_home else ft.Colors.ORANGE_400

    days_until = (fixture.date - gs.current_date).days if fixture.date else 0
    when = "TODAY!" if days_until <= 0 else f"in {days_until} day{'s' if days_until != 1 else ''}"

    # Recent form
    recent = queries.get_user_recent_fixtures(conn, gs.user_club_id, limit=5)
    form_chips = []
    for f in recent:
        if not f.result:
            continue
        is_h = f.home_club_id == gs.user_club_id
        ug = f.result.home_goals if is_h else f.result.away_goals
        og = f.result.away_goals if is_h else f.result.home_goals
        if ug > og:
            form_chips.append(("W", ft.Colors.GREEN_400))
        elif ug < og:
            form_chips.append(("L", ft.Colors.RED_400))
        else:
            form_chips.append(("D", ft.Colors.YELLOW_400))

    form_row = ft.Row(spacing=3, controls=[
        ft.Container(
            content=ft.Text(label, size=9, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            width=20, height=20, border_radius=10, bgcolor=color,
            alignment=ft.Alignment(0, 0),
        )
        for label, color in form_chips
    ]) if form_chips else ft.Text("—", size=10, color=ft.Colors.GREY_600)

    return [
        ft.Card(
            content=ft.Container(
                padding=15,
                bgcolor=CARD_GLASS_STRONG,
                border_radius=14,
                border=ft.border.all(1, GOLD_BORDER),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                    controls=[
                        ft.Text("⚽ Next Match", size=14, weight=ft.FontWeight.W_500,
                                color=ft.Colors.AMBER_300),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER, spacing=15,
                            controls=[
                                ft.Text(gs.user_club_name, size=14, weight=ft.FontWeight.BOLD,
                                        width=100, text_align=ft.TextAlign.RIGHT),
                                ft.Text("VS", size=16, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.AMBER_400),
                                ft.Text(opp_name, size=14, weight=ft.FontWeight.BOLD,
                                        width=100, text_align=ft.TextAlign.LEFT),
                            ],
                        ),
                        ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=[
                            ft.Text(venue, size=11, color=venue_color, weight=ft.FontWeight.W_500),
                            ft.Text(f"⏰ {when}", size=11, color=ft.Colors.GREY_400),
                        ]),
                        ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=5, controls=[
                            ft.Text("Form:", size=10, color=ft.Colors.GREY_500),
                            form_row,
                        ]),
                    ],
                ),
            ),
        ),
    ]


def _build_mini_table(conn, gs) -> list:
    """Build a mini league table showing 3 above and 3 below user position."""
    standings = queries.get_standings(conn)
    if not standings:
        return []

    user_idx = -1
    for i, s in enumerate(standings):
        if s.club_id == gs.user_club_id:
            user_idx = i
            break

    if user_idx < 0:
        return []

    # Show 3 above and 3 below
    start = max(0, user_idx - 3)
    end = min(len(standings), user_idx + 4)
    visible = standings[start:end]

    rows = []
    for i, s in enumerate(visible, start + 1):
        is_user = s.club_id == gs.user_club_id
        bg = ft.Colors.with_opacity(0.15, ft.Colors.GREEN) if is_user else None
        rows.append(
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(f"{i}.", size=11, width=22,
                                weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL),
                        ft.Text(s.club_name[:14], size=11, expand=True,
                                weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL,
                                color=ft.Colors.GREEN_300 if is_user else None),
                        ft.Text(f"{s.played}", size=10, width=20, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{s.goal_difference:+d}", size=10, width=25,
                                color=ft.Colors.GREEN_400 if s.goal_difference > 0
                                else ft.Colors.RED_400 if s.goal_difference < 0
                                else ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{s.points}", size=11, width=25,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.AMBER_300 if is_user else None,
                                text_align=ft.TextAlign.CENTER),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                bgcolor=bg,
                border_radius=4,
            )
        )

    return [
        ft.Text("📊 League Position", size=14, weight=ft.FontWeight.W_500),
        ft.Container(
            content=ft.Column(spacing=1, controls=[
                ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text("#", size=9, width=22, color=ft.Colors.GREY_600),
                    ft.Text("Team", size=9, color=ft.Colors.GREY_600, expand=True),
                    ft.Text("P", size=9, width=20, color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("GD", size=9, width=25, color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("Pts", size=9, width=25, color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER),
                ]),
                *rows,
            ]),
            padding=ft.padding.symmetric(horizontal=4, vertical=4),
            border_radius=10,
            bgcolor=CARD_GLASS,
            border=ft.border.all(1, GOLD_BORDER),
        ),
    ]


def _build_position_chart(conn, gs) -> list:
    """Build the league position history chart section."""
    from src.data.chart_queries import get_user_position_history
    from src.ui.widgets.charts import season_position_chart

    try:
        positions = get_user_position_history(conn, gs.user_club_id)
    except Exception:
        positions = []

    if not positions:
        return []

    clubs_count = len(queries.get_all_clubs(conn))
    chart = season_position_chart(positions, total_teams=clubs_count, width=320, height=130)

    return [
        section_card("📈 League Position", [chart], title_color=ft.Colors.BLUE_400),
    ]


def _build_form_trend(conn, gs) -> list:
    """Build the club form trend chart section."""
    from src.data.chart_queries import get_club_form_results
    from src.ui.widgets.charts import club_form_trend_line
    from src.ui.widgets.cards import form_chips

    try:
        results = get_club_form_results(conn, gs.user_club_id, limit=10)
    except Exception:
        results = []

    if not results:
        return []

    chips = form_chips(results)
    trend = club_form_trend_line(results, width=320, height=90)

    return [
        section_card("📊 Recent Form", [chips, trend], title_color=ACCENT),
    ]

