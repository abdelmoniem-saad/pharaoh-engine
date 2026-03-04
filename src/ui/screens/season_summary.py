"""
Season Summary screen — end-of-season awards, board review, start next season.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.season import get_season_awards, start_new_season
from src.core.board import get_confidence_level, generate_season_objectives, evaluate_objectives
from src.core.fans import get_fan_happiness_level
from src.utils.config import expectation_display, expectation_description
from src.utils.localization import t


def build_season_summary_screen(page: ft.Page) -> ft.Column:
    """Build the end-of-season summary."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = None  # No nav bar on this special screen

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)

    awards = get_season_awards(conn, gs)
    champion = awards["champion"]
    standings = awards["standings"]
    top_scorers = awards["top_scorers"]
    user_pos = awards["user_position"]
    user_standing = awards["user_standing"]
    is_champ = awards["is_user_champion"]
    golden_boot = awards.get("golden_boot")
    golden_glove = awards.get("golden_glove")
    young_player = awards.get("young_player")
    most_assists = awards.get("most_assists")

    # Trophy section
    if is_champ:
        trophy_icon = ft.Icon(ft.Icons.EMOJI_EVENTS, size=80, color=ft.Colors.AMBER_400)
        trophy_text = "🎉 CHAMPIONS! 🎉"
        trophy_color = ft.Colors.AMBER_300
    else:
        trophy_icon = ft.Icon(ft.Icons.EMOJI_EVENTS, size=60, color=ft.Colors.GREY_500)
        trophy_text = f"{champion.club_name} are Champions" if champion else "Season Complete"
        trophy_color = ft.Colors.GREY_400

    # User summary
    pos_suffix = {1: "st", 2: "nd", 3: "rd"}.get(user_pos, "th")
    user_summary = f"You finished {user_pos}{pos_suffix}"
    if user_standing:
        user_summary += (f" — {user_standing.points} pts | "
                          f"W{user_standing.won} D{user_standing.drawn} L{user_standing.lost} | "
                          f"GD {user_standing.goal_difference:+d}")

    # Board evaluation
    confidence_text = ""
    fan_text = ""
    board_eval_rows = []
    expectation_text = ""
    if club:
        conf = get_confidence_level(club.board_confidence)
        fan_lvl = get_fan_happiness_level(club.fan_happiness)
        confidence_text = f"Board Confidence: {conf.value} ({club.board_confidence}%)"
        fan_text = f"Fan Happiness: {fan_lvl} ({club.fan_happiness}%)"
        expectation_text = f"🎯 Expectation: {expectation_display(club.season_expectation)}"

        # Evaluate objectives for display
        objectives = generate_season_objectives(club)
        club.board_objectives = objectives
        user_gf = user_standing.goals_for if user_standing else 0
        user_gd = user_standing.goal_difference if user_standing else 0
        eval_msgs = evaluate_objectives(club, user_pos,
                                         goals_for=user_gf,
                                         goal_difference=user_gd)
        for msg in eval_msgs:
            is_achieved = msg.startswith("✅")
            board_eval_rows.append(
                ft.Text(msg, size=12,
                         color=ft.Colors.GREEN_400 if is_achieved else ft.Colors.RED_400)
            )

    # Top scorers section
    scorer_rows = []
    for i, s in enumerate(top_scorers[:5], 1):
        is_mine = s.get("club_short") == (club.short_name if club else "")
        scorer_rows.append(
            ft.Row(spacing=6, controls=[
                ft.Text(f"{i}.", size=12, width=20, color=ft.Colors.GREY_500),
                ft.Text(s["name"], size=12, expand=True,
                         weight=ft.FontWeight.BOLD if is_mine else ft.FontWeight.NORMAL,
                         color=ft.Colors.GREEN_300 if is_mine else None,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"⚽ {s['goals']}", size=12, weight=ft.FontWeight.BOLD,
                         color=ft.Colors.AMBER_300),
                ft.Text(s.get("club_short", ""), size=10, color=ft.Colors.GREY_500),
            ])
        )

    # Top 5 standings
    table_rows = []
    for i, s in enumerate(standings[:5], 1):
        is_user = s.club_id == gs.user_club_id
        table_rows.append(
            ft.Row(spacing=6, controls=[
                ft.Text(f"{i}.", size=12, width=20,
                         weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL),
                ft.Text(s.club_name, size=12, expand=True,
                         weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL,
                         color=ft.Colors.GREEN_300 if is_user else None,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{s.points} pts", size=12, weight=ft.FontWeight.BOLD,
                         color=ft.Colors.AMBER_300 if is_user else None),
            ])
        )

    def start_next(e):
        msgs = start_new_season(conn, gs)
        show_snackbar(page, f"🏟️ Season {gs.season_year}/{gs.season_year+1} started!")
        navigate(page, "/match_day")

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=16, right=16, top=20, bottom=20),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        trophy_icon,
                        ft.Text(trophy_text, size=24, weight=ft.FontWeight.BOLD,
                                 color=trophy_color, text_align=ft.TextAlign.CENTER),
                        ft.Text(
                            f"Season {gs.season_year}/{gs.season_year + 1}",
                            size=14, color=ft.Colors.GREY_500,
                        ),
                        ft.Divider(height=1),

                        # User result
                        ft.Container(
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                controls=[
                                    ft.Text(f"📍 {gs.user_club_name}", size=18,
                                             weight=ft.FontWeight.BOLD),
                                    ft.Text(user_summary, size=13, color=ft.Colors.GREY_400,
                                             text_align=ft.TextAlign.CENTER),
                                ],
                            ),
                            padding=12,
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.GREEN if is_champ else ft.Colors.WHITE),
                            border_radius=10,
                            border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.AMBER)),
                        ),

                        # Board & Fans
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER, spacing=20,
                            controls=[
                                ft.Text(confidence_text, size=12, color=ft.Colors.GREY_400),
                                ft.Text(fan_text, size=12, color=ft.Colors.GREY_400),
                            ],
                        ),

                        # Season expectation callout
                        ft.Container(
                            content=ft.Text(
                                expectation_text, size=14, weight=ft.FontWeight.W_500,
                                color=ft.Colors.AMBER_300, text_align=ft.TextAlign.CENTER,
                            ),
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=6,
                            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.AMBER),
                        ) if expectation_text else ft.Container(),

                        # Board Objectives Evaluation
                        *(
                            [ft.Text("📋 Board Objectives", size=16, weight=ft.FontWeight.W_500)]
                            + board_eval_rows
                            if board_eval_rows else []
                        ),
                        ft.Divider(height=1),

                        # Final Table (Top 5)
                        ft.Text("🏆 Final Standings (Top 5)", size=16,
                                 weight=ft.FontWeight.W_500),
                        *table_rows,
                        ft.Divider(height=1),

                        # Top Scorers
                        ft.Text("⚽ Top Scorers", size=16, weight=ft.FontWeight.W_500),
                        *(scorer_rows if scorer_rows else [
                            ft.Text("No goals scored!", size=12, color=ft.Colors.GREY_500)
                        ]),
                        ft.Divider(height=1),

                        # Season Awards
                        ft.Text("🏅 Season Awards", size=16, weight=ft.FontWeight.W_500),
                        *(
                            [_award_card("🥇 Golden Boot", golden_boot["name"],
                                         f"⚽ {golden_boot['goals']} goals",
                                         golden_boot.get("club_short", ""))]
                            if golden_boot else []
                        ),
                        *(
                            [_award_card("🧤 Golden Glove", golden_glove["name"],
                                         f"🧤 {golden_glove['clean_sheets']} clean sheets",
                                         golden_glove.get("club_name", ""))]
                            if golden_glove else []
                        ),
                        *(
                            [_award_card("⭐ Young Player", young_player["name"],
                                         f"📊 {young_player['rating']:.1f} avg rating (Age {young_player['age']})",
                                         young_player.get("club_name", ""))]
                            if young_player else []
                        ),
                        *(
                            [_award_card("🅰️ Most Assists", most_assists["name"],
                                         f"🅰️ {most_assists['assists']} assists",
                                         most_assists.get("club_name", ""))]
                            if most_assists else []
                        ),
                        ft.Divider(height=1),

                        # Actions
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "🔄 Start Next Season",
                            width=280, height=55,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE,
                                text_style=ft.TextStyle(size=18, weight=ft.FontWeight.BOLD),
                                shape=ft.RoundedRectangleBorder(radius=12),
                                elevation=4,
                                shadow_color=ft.Colors.with_opacity(0.25, "#FFD54F"),
                            ),
                            on_click=start_next,
                        ),
                        ft.Container(height=5),
                        ft.OutlinedButton(
                            "📊 View Full Table",
                            width=280, height=45,
                            on_click=lambda e: navigate(page, "/table"),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                side=ft.BorderSide(1, ft.Colors.with_opacity(0.18, "#FFD54F")),
                            ),
                        ),
                        ft.OutlinedButton(
                            "🏠 Main Menu",
                            width=280, height=45,
                            on_click=lambda e: navigate(page, "/"),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=12),
                                side=ft.BorderSide(1, ft.Colors.with_opacity(0.18, "#FFD54F")),
                            ),
                        ),
                    ],
                ),
            ),
        ],
    )


def _award_card(award_name: str, player_name: str, detail: str, club: str) -> ft.Container:
    """Build a small award card widget."""
    return ft.Container(
        content=ft.Row(
            spacing=10,
            controls=[
                ft.Text(award_name.split()[0], size=22),  # emoji
                ft.Column(spacing=0, expand=True, controls=[
                    ft.Text(" ".join(award_name.split()[1:]), size=12,
                            color=ft.Colors.AMBER_300, weight=ft.FontWeight.W_500),
                    ft.Text(player_name, size=14, weight=ft.FontWeight.BOLD),
                    ft.Row(spacing=6, controls=[
                        ft.Text(detail, size=11, color=ft.Colors.GREY_400),
                        ft.Text(f"({club})", size=10, color=ft.Colors.GREY_600) if club else ft.Container(),
                    ]),
                ]),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.AMBER),
        border_radius=10,
        border=ft.border.all(1, ft.Colors.with_opacity(0.18, ft.Colors.AMBER)),
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=6,
            color=ft.Colors.with_opacity(0.06, ft.Colors.AMBER),
        ),
    )
