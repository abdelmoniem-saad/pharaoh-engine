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

        # ── Board & Fans ─────────────────────────
        ft.Text("🏛️ Board & Fans", size=16, weight=ft.FontWeight.W_500),
        _card_row("Board Confidence", f"{confidence.value} ({club.board_confidence}%)", conf_color),
        _card_row("Fan Happiness", f"{fan_level} ({club.fan_happiness}%)", fan_color),
        ft.Text(f"🎤 {atmosphere}", size=11, color=ft.Colors.GREY_400, italic=True),
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
        ft.Divider(height=1),
    ]

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


