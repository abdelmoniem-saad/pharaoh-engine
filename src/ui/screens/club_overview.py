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
from src.utils.config import expectation_display, expectation_description


def build_club_overview_screen(page: ft.Page) -> ft.Column:
    """Build the club overview / hub screen."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 3)  # table index since accessed from there

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

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

    # Build sections
    sections = [
        ft.Text(f"🏟️ {club.name}", size=22, weight=ft.FontWeight.BOLD),
        ft.Text(f"👤 Manager: {gs.manager_name} | 📅 {gs.current_date.strftime('%d %b %Y')}",
                 size=12, color=ft.Colors.GREY_400),
        ft.Divider(height=1),

        # ── Dashboard: Next Match Card ───────────────
        *_build_next_match_card(conn, gs, club),

        # ── Mini League Table ────────────────────────
        *_build_mini_table(conn, gs),
        ft.Divider(height=1),

        # ── Board & Fans ─────────────────────────
        ft.Text("🏛️ Board & Fans", size=16, weight=ft.FontWeight.W_500),
        _card_row("Board Confidence", f"{confidence.value} ({club.board_confidence}%)", conf_color),
        _card_row("Fan Happiness", f"{fan_level} ({club.fan_happiness}%)", fan_color),
        ft.Text(f"🎤 {atmosphere}", size=11, color=ft.Colors.GREY_400, italic=True),
        ft.Divider(height=1),

        # ── Season Expectation ───────────────────
        ft.Text("🎯 Season Expectation", size=16, weight=ft.FontWeight.W_500),
        ft.Container(
            content=ft.Column(spacing=4, controls=[
                ft.Text(
                    expectation_display(club.season_expectation),
                    size=15, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.AMBER_300,
                ),
                ft.Text(
                    expectation_description(club.season_expectation),
                    size=12, color=ft.Colors.GREY_400, italic=True,
                ),
            ]),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.AMBER),
        ),
        ft.Divider(height=1),

        # ── Finances ─────────────────────────────
        ft.Text("💰 Monthly Finances", size=16, weight=ft.FontWeight.W_500),
        _finance_row("Balance", f"{club.finances.balance:,} EGP"),
        _finance_row("Monthly Income", f"+{income:,} EGP", ft.Colors.GREEN_400),
        _finance_row("Monthly Expenses", f"-{expenses:,} EGP", ft.Colors.RED_400),
        _finance_row("Net Cash Flow", f"{'+' if net >= 0 else ''}{net:,} EGP", net_color),
        _finance_row("Weekly Wage Bill", f"{wage_bill:,} EGP"),
        _finance_row("Transfer Budget", f"{club.finances.transfer_budget:,} EGP"),
        ft.Divider(height=1),

        # ── Stadium ──────────────────────────────
        ft.Text("🏟️ Club Info", size=16, weight=ft.FontWeight.W_500),
        _finance_row("Stadium", f"{club.stadium_name} ({club.stadium_capacity:,} seats)"),
        _finance_row("City", club.city),
        _finance_row("Reputation", f"{'⭐' * (club.reputation // 40 + 1)} {club.reputation}"),
        _finance_row("Facilities", f"{'🟢' * min(club.facilities_level, 10)} Lv.{club.facilities_level}"),
        _finance_row("Youth Rating", f"Lv.{club.youth_rating}"),
        _finance_row("Squad Size", str(len(squad))),
        _finance_row("Avg Age", f"{avg_age:.1f}"),
        _finance_row("🏥 Injured", str(injured_count),
                      ft.Colors.RED_400 if injured_count > 0 else ft.Colors.GREY_500),
        _finance_row("🚫 Suspended", str(suspended_count),
                      ft.Colors.ORANGE_400 if suspended_count > 0 else ft.Colors.GREY_500),
        ft.Divider(height=1),
    ]

    # Injured players list
    injured_players = [p for p in squad if p.injury_days_remaining > 0]
    if injured_players:
        sections.append(ft.Text("🏥 Injured Players", size=16, weight=ft.FontWeight.W_500))
        for p in injured_players:
            sections.append(
                ft.Row(spacing=8, controls=[
                    ft.Text(p.name, size=12, width=140),
                    ft.Text(f"{p.injury_type}", size=11, color=ft.Colors.RED_400),
                    ft.Text(f"({p.injury_days_remaining}d)", size=11, color=ft.Colors.GREY_500),
                ])
            )
        sections.append(ft.Divider(height=1))

    # Suspended players
    suspended_players = [p for p in squad if p.suspension_matches > 0]
    if suspended_players:
        sections.append(ft.Text("🚫 Suspended Players", size=16, weight=ft.FontWeight.W_500))
        for p in suspended_players:
            sections.append(
                ft.Row(spacing=8, controls=[
                    ft.Text(p.name, size=12, width=140),
                    ft.Text(f"{p.suspension_matches} match(es)", size=11, color=ft.Colors.ORANGE_400),
                ])
            )
        sections.append(ft.Divider(height=1))

    # Squad top scorers
    if squad_scorers:
        sections.append(ft.Text("⚽ Your Top Scorers", size=16, weight=ft.FontWeight.W_500))
        for p in squad_scorers:
            sections.append(
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Text(p.name, size=12, width=140),
                        ft.Text(f"⚽ {p.season_stats.goals}", size=12,
                                 weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300),
                        ft.Text(f"🅰️ {p.season_stats.assists}", size=12),
                        ft.Text(f"({p.position.value})", size=11, color=ft.Colors.GREY_500),
                    ],
                )
            )
        sections.append(ft.Divider(height=1))

    # League top scorers
    if league_scorers:
        sections.append(ft.Text("🏆 League Top Scorers", size=16, weight=ft.FontWeight.W_500))
        for i, scorer in enumerate(league_scorers, 1):
            is_user_player = scorer.get("club_short") == club.short_name
            sections.append(
                ft.Row(
                    spacing=6,
                    controls=[
                        ft.Text(f"{i}.", size=11, width=20, color=ft.Colors.GREY_500),
                        ft.Text(scorer["name"], size=12, width=130,
                                 weight=ft.FontWeight.BOLD if is_user_player else ft.FontWeight.NORMAL,
                                 color=ft.Colors.GREEN_300 if is_user_player else None),
                        ft.Text(f"⚽ {scorer['goals']}", size=12, weight=ft.FontWeight.BOLD,
                                 color=ft.Colors.AMBER_300),
                        ft.Text(f"🅰️ {scorer['assists']}", size=11),
                        ft.Text(scorer.get("club_short", ""), size=10, color=ft.Colors.GREY_500),
                    ],
                )
            )

    # Back button
    sections.append(ft.Container(height=10))
    sections.append(
        ft.ElevatedButton("← Back to Table", width=200,
                           on_click=lambda e: navigate(page, "/table")),
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(spacing=6, controls=sections),
            ),
        ],
    )


def _card_row(label: str, value: str, color=None) -> ft.Container:
    """A labeled row with optional color."""
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=13, color=ft.Colors.GREY_400),
                ft.Text(value, size=13, weight=ft.FontWeight.BOLD,
                         color=color or ft.Colors.WHITE),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
    )


def _finance_row(label: str, value: str, color=None) -> ft.Row:
    """A simple label-value row."""
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(label, size=12, color=ft.Colors.GREY_500),
            ft.Text(value, size=12, weight=ft.FontWeight.W_500,
                     color=color or ft.Colors.WHITE),
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
            border_radius=6,
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        ),
    ]


