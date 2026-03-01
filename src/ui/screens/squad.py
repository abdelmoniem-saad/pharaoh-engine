"""
Squad management screen — view players, tap for detailed stats.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.player import calculate_overall_rating
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.stat_bar import stat_bar


def build_squad_screen(page: ft.Page) -> ft.Column:
    """Build the squad management content."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 0)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    players = queries.get_players_by_club(conn, club.id)

    # Build player rows for the DataTable
    rows = []
    for player in players:
        ovr = calculate_overall_rating(player)
        fit_color = (
            ft.Colors.GREEN_400 if player.fitness >= 80
            else ft.Colors.YELLOW_400 if player.fitness >= 50
            else ft.Colors.RED_400
        )
        ovr_color = ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE
        morale_icon = "😊" if player.morale >= 70 else "😐" if player.morale >= 40 else "😞"

        def make_click_handler(p=player, o=ovr):
            def handler(e):
                _show_player_detail(page, p, o)
            return handler

        rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(player.name, size=12)),
                    ft.DataCell(ft.Text(player.position.value, size=11,
                                        color=ft.Colors.AMBER_300)),
                    ft.DataCell(ft.Text(str(player.age), size=11)),
                    ft.DataCell(ft.Text(str(ovr), size=12,
                                        weight=ft.FontWeight.BOLD, color=ovr_color)),
                    ft.DataCell(ft.Text(f"{player.fitness}%", size=11, color=fit_color)),
                    ft.DataCell(ft.Text(f"{player.form:.1f}", size=11)),
                ],
                on_select_change=make_click_handler(),
            )
        )

    # Squad summary
    avg_ovr = sum(calculate_overall_rating(p) for p in players) / max(len(players), 1)
    avg_age = sum(p.age for p in players) / max(len(players), 1)

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(label=ft.Text("Name", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Pos", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Age", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("OVR", size=11, weight=ft.FontWeight.BOLD), numeric=True),
            ft.DataColumn(label=ft.Text("Fit", size=11, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(label=ft.Text("Form", size=11, weight=ft.FontWeight.BOLD), numeric=True),
        ],
        rows=rows,
        column_spacing=10,
        horizontal_lines=ft.BorderSide(0.3, ft.Colors.WHITE24),
        heading_row_height=35,
        data_row_min_height=34,
        data_row_max_height=38,
    )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=10, right=10, top=10),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text(
                            f"📋 {gs.user_club_name}",
                            size=22, weight=ft.FontWeight.BOLD,
                        ),
                        ft.Row(
                            spacing=15,
                            controls=[
                                ft.Text(
                                    f"👤 {gs.manager_name}",
                                    size=13, color=ft.Colors.GREY_400,
                                ),
                                ft.Text(
                                    f"📅 {gs.current_date.strftime('%d %b %Y')}",
                                    size=13, color=ft.Colors.GREY_500,
                                ),
                            ],
                        ),
                        # Squad summary chips
                        ft.Row(
                            spacing=8,
                            controls=[
                                _summary_chip("Squad", str(len(players)), ft.Icons.PEOPLE),
                                _summary_chip("Avg OVR", f"{avg_ovr:.0f}", ft.Icons.STAR),
                                _summary_chip("Avg Age", f"{avg_age:.1f}", ft.Icons.CAKE),
                            ],
                        ),
                        ft.Divider(height=1),
                        ft.Text("Tap a player for details",
                                size=11, color=ft.Colors.GREY_600, italic=True),
                        data_table,
                    ],
                ),
            ),
        ],
    )


def _summary_chip(label: str, value: str, icon) -> ft.Container:
    """Small summary chip widget."""
    return ft.Container(
        content=ft.Row(
            spacing=4, tight=True,
            controls=[
                ft.Icon(icon, size=13, color=ft.Colors.AMBER_300),
                ft.Text(f"{label}: ", size=10, color=ft.Colors.GREY_500),
                ft.Text(value, size=11, weight=ft.FontWeight.BOLD),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=6,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
    )


def _show_player_detail(page: ft.Page, player, ovr: int):
    """Show a detailed player profile dialog with all stats."""
    a = player.attributes
    s = player.season_stats

    fit_color = (
        ft.Colors.GREEN_400 if player.fitness >= 80
        else ft.Colors.YELLOW_400 if player.fitness >= 50
        else ft.Colors.RED_400
    )
    morale_text = (
        "😊 Happy" if player.morale >= 70
        else "😐 Content" if player.morale >= 40
        else "😞 Unhappy"
    )

    # Technical stats
    tech_stats = [
        stat_bar("Finishing", a.finishing),
        stat_bar("Passing", a.passing),
        stat_bar("Dribbling", a.dribbling),
        stat_bar("First Touch", a.first_touch),
        stat_bar("Crossing", a.crossing),
        stat_bar("Heading", a.heading),
        stat_bar("Long Shots", a.long_shots),
    ]

    # Physical stats
    phys_stats = [
        stat_bar("Pace", a.pace),
        stat_bar("Stamina", a.stamina),
        stat_bar("Strength", a.strength),
        stat_bar("Agility", a.agility),
        stat_bar("Jumping", a.jumping),
    ]

    # Mental stats
    mental_stats = [
        stat_bar("Composure", a.composure),
        stat_bar("Vision", a.vision),
        stat_bar("Work Rate", a.work_rate),
        stat_bar("Positioning", a.positioning),
        stat_bar("Decisions", a.decisions),
    ]

    # Defensive stats
    def_stats = [
        stat_bar("Tackling", a.tackling),
        stat_bar("Marking", a.marking),
    ]

    # GK stats (only for goalkeepers)
    gk_section = []
    if player.position.value == "GK":
        gk_section = [
            ft.Text("🧤 Goalkeeping", size=13, weight=ft.FontWeight.W_500,
                     color=ft.Colors.AMBER_300),
            stat_bar("Reflexes", a.gk_reflexes),
            stat_bar("Handling", a.gk_handling),
            stat_bar("GK Pos.", a.gk_positioning),
            stat_bar("1v1", a.gk_one_on_ones),
            stat_bar("Kicking", a.gk_kicking),
            ft.Divider(height=1),
        ]

    # Season stats row
    season_info = ft.Row(
        wrap=True, spacing=12,
        controls=[
            ft.Text(f"⚽ {s.goals}G", size=12),
            ft.Text(f"🅰️ {s.assists}A", size=12),
            ft.Text(f"📋 {s.appearances} Apps", size=12),
            ft.Text(f"🟡 {s.yellow_cards}", size=12),
            ft.Text(f"🟥 {s.red_cards}", size=12),
        ],
    )

    # Contract info
    expiry_str = player.contract.contract_expiry.strftime("%b %Y") if player.contract.contract_expiry else "N/A"
    wage_str = f"{player.contract.wage_weekly:,} EGP/wk"

    dlg = ft.AlertDialog(
        title=ft.Row(
            controls=[
                ft.Text(player.name, size=18, weight=ft.FontWeight.BOLD, expand=True),
                ft.Container(
                    content=ft.Text(str(ovr), size=18, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE),
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=8,
                ),
            ],
        ),
        content=ft.Container(
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO,
                spacing=6,
                controls=[
                    # Player info bar
                    ft.Row(
                        spacing=10, wrap=True,
                        controls=[
                            ft.Text(f"📍 {player.position.value}", size=12,
                                    color=ft.Colors.AMBER_300, weight=ft.FontWeight.BOLD),
                            ft.Text(f"Age {player.age}", size=12),
                            ft.Text(f"🦶 {player.preferred_foot.value}", size=12),
                            ft.Text(f"#{player.shirt_number or '–'}", size=12,
                                    color=ft.Colors.GREY_400),
                        ],
                    ),
                    ft.Row(
                        spacing=10,
                        controls=[
                            ft.Text(f"💪 {player.fitness}%", size=12, color=fit_color),
                            ft.Text(f"📊 Form {player.form:.1f}", size=12),
                            ft.Text(morale_text, size=12),
                        ],
                    ),
                    ft.Divider(height=1),
                    # Season stats
                    ft.Text("📈 Season Stats", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    season_info,
                    ft.Divider(height=1),
                    # GK section (if applicable)
                    *gk_section,
                    # Technical
                    ft.Text("⚽ Technical", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *tech_stats,
                    ft.Divider(height=1),
                    # Defensive
                    ft.Text("🛡️ Defensive", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *def_stats,
                    ft.Divider(height=1),
                    # Physical
                    ft.Text("🏃 Physical", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *phys_stats,
                    ft.Divider(height=1),
                    # Mental
                    ft.Text("🧠 Mental", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    *mental_stats,
                    ft.Divider(height=1),
                    # Contract
                    ft.Text("📝 Contract", size=13, weight=ft.FontWeight.W_500,
                             color=ft.Colors.AMBER_300),
                    ft.Row(
                        spacing=15,
                        controls=[
                            ft.Text(f"💰 {wage_str}", size=12),
                            ft.Text(f"📅 Expires: {expiry_str}", size=12),
                        ],
                    ),
                ],
            ),
            width=340,
            height=420,
        ),
        actions=[
            ft.TextButton("Close", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)

