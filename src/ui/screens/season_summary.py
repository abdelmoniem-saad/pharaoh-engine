"""
Season Summary screen — end-of-season awards, board review, start next season.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.core.season import get_season_awards, start_new_season
from src.core.board import get_confidence_level, generate_season_objectives, evaluate_objectives
from src.core.fans import get_fan_happiness_level
from src.utils.config import expectation_display, expectation_description
from src.utils.localization import t, display_name


def build_season_summary_screen(page: ft.Page) -> ft.Column:
    """Build the end-of-season summary."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = None  # No nav bar on this special screen

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text("No game loaded", rtl=theme.rtl())])

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
        trophy_icon = ft.Icon(ft.Icons.EMOJI_EVENTS, rtl=theme.rtl(), size=80, color=theme.ACCENT)
        trophy_text = t("champions")
        trophy_color = theme.GOLD
    else:
        trophy_icon = ft.Icon(ft.Icons.EMOJI_EVENTS, rtl=theme.rtl(), size=60, color=ft.Colors.GREY_500)
        trophy_text = t("season_complete")
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
                ft.Text(msg, rtl=theme.rtl(), size=12,
                         color=ft.Colors.GREEN_400 if is_achieved else ft.Colors.RED_400)
            )

    # Top scorers section
    scorer_rows = []
    for i, s in enumerate(top_scorers[:5], 1):
        is_mine = s.get("club_short") == (club.short_name if club else "")
        scorer_rows.append(
            ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                ft.Text(f"{i}.", rtl=theme.rtl(), size=12, width=20, color=ft.Colors.GREY_500),
                ft.Text(s["name"], rtl=theme.rtl(), size=12, expand=True,
                         weight=ft.FontWeight.BOLD if is_mine else ft.FontWeight.NORMAL,
                         color=ft.Colors.GREEN_300 if is_mine else None,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"⚽ {s['goals']}", rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD,
                         color=theme.GOLD),
                ft.Text(s.get("club_short", ""), rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
            ])
        )

    # Top 5 standings
    table_rows = []
    for i, s in enumerate(standings[:5], 1):
        is_user = s.club_id == gs.user_club_id
        table_rows.append(
            ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                ft.Text(f"{i}.", rtl=theme.rtl(), size=12, width=20,
                         weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL),
                ft.Text(s.club_name, rtl=theme.rtl(), size=12, expand=True,
                         weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL,
                         color=ft.Colors.GREEN_300 if is_user else None,
                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{s.points} pts", rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD,
                         color=theme.GOLD if is_user else None),
            ])
        )

    def _begin_next_season():
        from src.ui.app import run_busy_task

        def done(error):
            if error is not None:
                show_snackbar(page,
                              f"⚠️ Could not start the new season: {error}",
                              bgcolor=ft.Colors.RED_800)
                return
            show_snackbar(page, f"🏟️ Season {gs.season_year}/{gs.season_year+1} started!")
            navigate(page, "/match_day")

        run_busy_task(page, "🏟️ Preparing new season…", lambda: start_new_season(conn, gs),
                      on_done=done)

    def start_next(e):
        # Irreversible progression — always confirm before rolling over.
        def _confirm(e2):
            page.pop_dialog()
            _begin_next_season()

        page.show_dialog(ft.AlertDialog(
            rtl=theme.rtl(), title=ft.Text("🔄 Start Next Season?", rtl=theme.rtl()),
            content=ft.Text(
                "This closes the current campaign for good: players age, "
                "retirements are processed, youth prospects join and next "
                "season's fixtures are drawn.\n\nReady when you are, Boss."
            , rtl=theme.rtl()),
            actions=[
                ft.TextButton(t("cancel"), rtl=theme.rtl(), on_click=lambda e2: page.pop_dialog()),
                ft.ElevatedButton("🔄 Let's Go", rtl=theme.rtl(), on_click=_confirm),
            ],
        ))

    from src.ui.widgets.cards import section_card, kv_row
    from src.ui.widgets.dossier import metric, section_tabs
    review = ft.Column(rtl=theme.rtl(), spacing=20, controls=[
        section_card(t("board_objectives"), [
            kv_row(t("board_confidence"), f"{club.board_confidence}%"),
            kv_row(t("fan_happiness"), f"{club.fan_happiness}%"),
            *board_eval_rows,
        ]) if club else ft.Container(rtl=theme.rtl()),
        section_card(t("final_standings"), table_rows),
    ])
    award_cards = []
    for winner, label, stat in [
        (golden_boot, t("golden_boot"), "goals"),
        (golden_glove, t("golden_glove"), "clean_sheets"),
        (young_player, t("young_player"), "rating"),
        (most_assists, t("most_assists"), "assists"),
    ]:
        if winner:
            award_cards.append(_award_card(label, winner["name"],
                f"{t(stat)}: {winner.get(stat, '—')}", winner.get("club_name", winner.get("club_short", ""))))
    honours = ft.Column(rtl=theme.rtl(), spacing=16, controls=[
        *award_cards, section_card(t("top_scorers"), scorer_rows),
    ])
    return ft.Column(rtl=theme.rtl(), expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(rtl=theme.rtl(), padding=theme.PAGE_PADDING, content=ft.Column(rtl=theme.rtl(), spacing=24, controls=[
            theme.header_bar(trophy_text, subtitle=f"{gs.season_year} / {gs.season_year+1}", page=page, show_notification_bell=False),
            ft.Container(rtl=theme.rtl(), padding=24, border_radius=16, bgcolor=theme.CARD_GLASS_STRONG,
                border=ft.border.all(1, theme.GOLD_BORDER), content=ft.Column(rtl=theme.rtl(), spacing=20, controls=[
                    ft.Icon(ft.Icons.EMOJI_EVENTS_OUTLINED, rtl=theme.rtl(), size=36, color=theme.ACCENT),
                    ft.Text(display_name(club) if club else gs.user_club_name, rtl=theme.rtl(), size=28, font_family=theme.display_font()),
                    ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                        metric(t("position"), str(user_pos)),
                        metric(t("points"), str(user_standing.points if user_standing else 0)),
                        metric(t("goals"), str(user_standing.goals_for if user_standing else 0)),
                    ]),
                ])),
            ft.FilledButton(t("next_season"), rtl=theme.rtl(), height=52, style=theme.PRIMARY_BTN_STYLE, on_click=start_next),
            section_tabs(page, [t("overview_tab"), t("season_awards")], [review, honours]),
            review, honours,
            ft.Row(rtl=theme.rtl(), wrap=True, controls=[
                ft.OutlinedButton(t("view_full_table"), rtl=theme.rtl(), on_click=lambda e: navigate(page, "/table")),
                ft.TextButton(t("main_menu"), rtl=theme.rtl(), on_click=lambda e: navigate(page, "/")),
            ]),
        ]))])



def _award_card(award_name: str, player_name: str, detail: str, club: str) -> ft.Container:
    """Build a small award card widget."""
    return ft.Container(rtl=theme.rtl(), padding=20, border_radius=12,
        bgcolor=theme.CARD_GLASS_STRONG, border=ft.border.all(1, theme.GOLD_BORDER),
        content=ft.Column(rtl=theme.rtl(), spacing=10, controls=[
            ft.Text(award_name, rtl=theme.rtl(), size=12, color=theme.ACCENT),
            ft.Text(player_name, rtl=theme.rtl(), size=24, font_family=theme.display_font()),
            ft.Text(detail, rtl=theme.rtl(), size=13, color=theme.TEXT_SECONDARY),
            ft.Text(club, rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
        ]))
