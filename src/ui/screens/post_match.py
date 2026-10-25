"""
Post-Match screen — detailed summary, MOTM, press conference, ratings.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme
from src.utils.inbox_localization import display_news

from src.data import queries
from src.data.models import MatchResult, MatchdayOutcome, InboxMessage
from src.core.player import calculate_overall_rating
from src.utils.config import MatchEventType
from src.utils import rng
from src.utils.localization import t, display_name, display_home_name, display_away_name


def build_post_match_screen(page: ft.Page) -> ft.Column:
    """Build the post-match summary screen."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = None  # Full-screen experience

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("no_game_loaded"), rtl=theme.rtl())])

    conn = app_state.db_conn
    gs = app_state.game_state

    # Reset transient nav guard when this screen mounts.
    app_state._post_match_nav_in_progress = False

    # Get the last match outcome stored on app_state
    outcome: MatchdayOutcome | None = getattr(app_state, '_last_outcome', None)
    if not outcome:
        return ft.Column(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Text(t("no_data"), rtl=theme.rtl(), size=16, color=ft.Colors.GREY_400),
                ft.ElevatedButton(t("back"), rtl=theme.rtl(), on_click=lambda e: navigate(page, "/match_day")),
            ],
        )

    result = outcome.user_result
    is_home = result.home_club_id == gs.user_club_id
    user_goals = result.home_goals if is_home else result.away_goals
    opp_goals = result.away_goals if is_home else result.home_goals
    user_club_name = result.home_club_name if is_home else result.away_club_name
    opp_club_name = result.away_club_name if is_home else result.home_club_name

    # Result type
    if user_goals > opp_goals:
        result_text = t("victory").upper()
        result_color = ft.Colors.GREEN_400
        result_icon = ft.Icons.CELEBRATION
    elif user_goals < opp_goals:
        result_text = t("defeat").upper()
        result_color = ft.Colors.RED_400
        result_icon = ft.Icons.SENTIMENT_DISSATISFIED
    else:
        result_text = t("draw").upper()
        result_color = ft.Colors.YELLOW_400
        result_icon = ft.Icons.HANDSHAKE

    # Show match result notification
    try:
        from src.ui.app import show_notification
        show_notification(
            page,
            f"{result_text} — {user_club_name} {user_goals}-{opp_goals} {opp_club_name}",
            category="match",
            duration=4.0,
        )
    except Exception:
        pass

    # ── MOTM calculation ────────────────────────────────────────────
    user_players = queries.get_players_by_club(conn, gs.user_club_id)
    name_map = {p.id: p for p in user_players}
    user_ratings = {pid: r for pid, r in result.player_ratings.items()
                    if pid in name_map}
    motm_id = max(user_ratings, key=user_ratings.get) if user_ratings else None
    motm_player = name_map.get(motm_id) if motm_id else None
    motm_rating = user_ratings.get(motm_id, 0.0) if motm_id else 0.0

    # ── Goals list ──────────────────────────────────────────────────
    goals = [e for e in result.events if e.event_type in (MatchEventType.GOAL, MatchEventType.PENALTY)]
    goal_widgets = []
    for g in goals:
        side_icon = "🏠" if g.club_id == result.home_club_id else "✈️"
        is_user_goal = g.club_id == gs.user_club_id
        goal_color = ft.Colors.GREEN_300 if is_user_goal else ft.Colors.RED_300
        assist_text = f" ({t('assist')}: {g.second_player_name})" if g.second_player_name and g.event_type == MatchEventType.GOAL else ""
        goal_widgets.append(
            ft.Container(
                rtl=theme.rtl(), content=ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                    ft.Text(f"{g.minute}'", rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD,
                            color=theme.GOLD, width=35),
                    ft.Text("⚽", rtl=theme.rtl(), size=14),
                    ft.Text(f"{g.player_name}{assist_text}", rtl=theme.rtl(), size=12, color=goal_color,
                            expand=True),
                ]),
                padding=ft.padding.symmetric(vertical=2),
            )
        )
    if not goal_widgets:
        goal_widgets.append(ft.Text(t("no_goals_scored"), rtl=theme.rtl(), size=12, color=ft.Colors.GREY_500))

    # ── Cards & injuries ────────────────────────────────────────────
    cards = [e for e in result.events
             if e.event_type in (MatchEventType.YELLOW_CARD, MatchEventType.RED_CARD)]
    injuries = [e for e in result.events if e.event_type == MatchEventType.INJURY]
    incident_widgets = []
    for c in cards:
        icon = "🟡" if c.event_type == MatchEventType.YELLOW_CARD else "🟥"
        incident_widgets.append(ft.Text(f"{c.minute}' {icon} {c.player_name}", rtl=theme.rtl(), size=11))
    for inj in injuries:
        incident_widgets.append(
            ft.Text(f"{inj.minute}' 🏥 {inj.description}", rtl=theme.rtl(), size=11, color=ft.Colors.RED_400))

    # ── Stats comparison ────────────────────────────────────────────
    stats_data = [
        (t("possession"), f"{result.home_stats.possession:.0f}%", f"{result.away_stats.possession:.0f}%"),
        (t("shots"), str(result.home_stats.shots), str(result.away_stats.shots)),
        (t("on_target"), str(result.home_stats.shots_on_target), str(result.away_stats.shots_on_target)),
        (t("corners"), str(result.home_stats.corners), str(result.away_stats.corners)),
        (t("fouls"), str(result.home_stats.fouls), str(result.away_stats.fouls)),
        (t("yellow_cards"), str(result.home_stats.yellow_cards), str(result.away_stats.yellow_cards)),
        (t("saves"), str(result.home_stats.saves), str(result.away_stats.saves)),
    ]

    def _stat_bar(home_val_str, away_val_str, label):
        """Create a visual stat comparison bar — responsive width."""
        try:
            hv = float(home_val_str.replace('%', ''))
            av = float(away_val_str.replace('%', ''))
        except ValueError:
            hv = av = 0
        total = hv + av if (hv + av) > 0 else 1
        home_flex = max(1, int(hv / total * 100))
        away_flex = max(1, int((1 - hv / total) * 100))
        return ft.Container(
            rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=2, controls=[
                ft.Row(rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                    ft.Text(home_val_str, rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
                    ft.Text(label, rtl=theme.rtl(), size=10, color=ft.Colors.GREY_400),
                    ft.Text(away_val_str, rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
                ]),
                ft.Row(rtl=theme.rtl(), spacing=2, controls=[
                    ft.Container(
                        rtl=theme.rtl(), expand=home_flex, height=4,
                        bgcolor=ft.Colors.GREEN_400 if is_home else ft.Colors.BLUE_400,
                        border_radius=2,
                    ),
                    ft.Container(
                        rtl=theme.rtl(), expand=away_flex, height=4,
                        bgcolor=ft.Colors.BLUE_400 if is_home else ft.Colors.GREEN_400,
                        border_radius=2,
                    ),
                ]),
            ]),
            padding=ft.padding.symmetric(vertical=2),
        )

    stat_widgets = [_stat_bar(h, a, label) for label, h, a in stats_data]

    # ── Top player ratings (sorted) ─────────────────────────────────
    all_players_db = user_players + queries.get_players_by_club(conn,
        result.away_club_id if is_home else result.home_club_id)
    all_name_map = {p.id: p for p in all_players_db}

    sorted_ratings = sorted(result.player_ratings.items(), key=lambda x: -x[1])[:10]
    rating_widgets = []
    for pid, rating in sorted_ratings:
        p = all_name_map.get(pid)
        if not p:
            continue
        is_mine = p.club_id == gs.user_club_id
        r_color = (ft.Colors.GREEN_400 if rating >= 7.5
                   else ft.Colors.YELLOW_400 if rating >= 6.5
                   else ft.Colors.RED_400)
        rating_widgets.append(
            ft.Container(
                rtl=theme.rtl(), content=ft.Row(
                    rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(rtl=theme.rtl(), spacing=6, tight=True, controls=[
                            ft.Container(
                                rtl=theme.rtl(), content=ft.Text(p.position.value, rtl=theme.rtl(), size=9,
                                                color=ft.Colors.WHITE),
                                width=28, height=18, border_radius=4,
                                bgcolor=theme.ACCENT_DARK if is_mine else ft.Colors.GREY_700,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Text(p.name, rtl=theme.rtl(), size=12,
                                    weight=ft.FontWeight.BOLD if is_mine else ft.FontWeight.NORMAL,
                                    color=ft.Colors.GREEN_200 if is_mine else None),
                        ]),
                        ft.Container(
                            rtl=theme.rtl(), content=ft.Text(f"{rating:.1f}", rtl=theme.rtl(), size=13,
                                            weight=ft.FontWeight.BOLD, color=r_color),
                            width=40, alignment=ft.Alignment(1, 0),
                        ),
                    ],
                ),
                padding=ft.padding.symmetric(vertical=3, horizontal=6),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                border=ft.border.only(
                    left=ft.BorderSide(2,
                        theme.ACCENT if is_mine else ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                ),
            )
        )

    # ── Other matchday results ──────────────────────────────────────
    other_widgets = []
    if outcome.other_results:
        for r in outcome.other_results:
            other_widgets.append(
                ft.Container(
                    rtl=theme.rtl(), content=ft.Row(
                        rtl=theme.rtl(), alignment=ft.MainAxisAlignment.CENTER, spacing=8,
                        controls=[
                            ft.Text(r.home_club_name, rtl=theme.rtl(), size=11,
                                    text_align=ft.TextAlign.LEFT if theme.rtl() else ft.TextAlign.RIGHT, expand=True,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(
                                rtl=theme.rtl(), content=ft.Text(theme.scoreline(r.home_goals, r.away_goals),
                                                rtl=False, size=12, weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=4,
                            ),
                            ft.Text(r.away_club_name, rtl=theme.rtl(), size=11,
                                    text_align=ft.TextAlign.RIGHT if theme.rtl() else ft.TextAlign.LEFT, expand=True,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                    ),
                    padding=ft.padding.symmetric(vertical=2),
                )
            )

    # ── Position change ─────────────────────────────────────────────
    pos_widget = ft.Container(rtl=theme.rtl())
    if outcome.position_before > 0 and outcome.position_after > 0:
        delta = outcome.position_before - outcome.position_after
        if delta > 0:
            pos_text = f"▲ {outcome.position_after}th (up {delta})"
            pos_color = ft.Colors.GREEN_400
        elif delta < 0:
            pos_text = f"▼ {outcome.position_after}th (down {abs(delta)})"
            pos_color = ft.Colors.RED_400
        else:
            pos_text = f"— {outcome.position_after}th (unchanged)"
            pos_color = ft.Colors.GREY_400
        pos_widget = ft.Text(pos_text, rtl=theme.rtl(), size=13, color=pos_color,
                             weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER)

    # ── Press conference state ──────────────────────────────────────
    press_done = [False]

    def _press_conference(e):
        if press_done[0]:
            show_snackbar(page, f"{t('press_conference')} ✅")
            return
        _show_press_conference(page, conn, gs, result, is_home)
        press_done[0] = True

    # ── Navigation ──────────────────────────────────────────────────
    def go_match_day(e):
        if getattr(app_state, "_post_match_nav_in_progress", False):
            return
        app_state._post_match_nav_in_progress = True
        e.control.disabled = True
        page.update()
        app_state._last_outcome = None
        navigate(page, "/match_day")

    def go_table(e):
        navigate(page, "/table")

    # ── Build the screen ────────────────────────────────────────────
    # Show achievement toasts
    if outcome.newly_unlocked:
        from src.core.achievements import get_achievements
        all_achs = {a["key"]: a for a in get_achievements(conn)}
        for key in outcome.newly_unlocked:
            ach = all_achs.get(key)
            if ach:
                show_snackbar(page,
                    f"{ach['icon']} Achievement: {ach['title']}!",
                    bgcolor=theme.ACCENT_DARK)

    from src.ui.widgets.cards import match_score_card, section_card
    from src.ui.widgets.dossier import section_tabs
    report = ft.Column(rtl=theme.rtl(), spacing=20, controls=[
        section_card(t("goals_label"), goal_widgets),
        section_card(t("match_stats"), [
            ft.Row(rtl=theme.rtl(), controls=[
                ft.Text(display_home_name(result), rtl=theme.rtl(), expand=True, size=12, color=theme.TEXT_MUTED),
                ft.Text(display_away_name(result), rtl=theme.rtl(), expand=True, size=12, color=theme.TEXT_MUTED,
                        text_align=ft.TextAlign.LEFT if theme.rtl() else ft.TextAlign.RIGHT),
            ]), *stat_widgets]),
        *([section_card(t("cards_injuries"), incident_widgets)] if incident_widgets else []),
    ])
    ratings = ft.Column(rtl=theme.rtl(), spacing=12, controls=rating_widgets)
    elsewhere = ft.Column(rtl=theme.rtl(), spacing=12, controls=other_widgets or [ft.Text(t("no_data"), rtl=theme.rtl())])
    tabs = section_tabs(page, [t("match_report"), t("top_performers"), t("other_results")],
                        [report, ratings, elsewhere])
    sections = [
        ft.Row(rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Text(result_text, rtl=theme.rtl(), size=38, font_family=theme.display_font(), color=result_color),
            ft.Text(t("full_time"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
        ]),
        match_score_card(display_home_name(result), display_away_name(result),
            result.home_goals, result.away_goals, result.competition,
            f"{t('matchday')} {outcome.matchday}", is_home),
        pos_widget,
        ft.Row(rtl=theme.rtl(), spacing=10, controls=[
            ft.ElevatedButton(t("continue_btn"), rtl=theme.rtl(), expand=True, height=50,
                             style=theme.PRIMARY_BTN_STYLE, on_click=go_match_day),
            ft.OutlinedButton(t("view_final_table"), rtl=theme.rtl(), expand=True, height=50,
                              style=theme.SECONDARY_BTN_STYLE, on_click=go_table),
        ]),
        ft.TextButton(t("press_conference"), rtl=theme.rtl(), icon=ft.Icons.MIC_NONE, on_click=_press_conference),
    ]
    if motm_player:
        sections.append(ft.Container(rtl=theme.rtl(), padding=18, border_radius=14, bgcolor=theme.ACCENT_BG,
            content=ft.Row(rtl=theme.rtl(), spacing=14, controls=[
                ft.Icon(ft.Icons.STAR_OUTLINE, rtl=theme.rtl(), color=theme.ACCENT, size=28),
                ft.Column(rtl=theme.rtl(), expand=True, spacing=5, controls=[
                    ft.Text(t("man_of_the_match"), rtl=theme.rtl(), size=11, color=theme.ACCENT),
                    ft.Text(display_name(motm_player), rtl=theme.rtl(), size=20, font_family=theme.display_font()),
                ]),
                ft.Text(f"{motm_rating:.1f}", rtl=theme.rtl(), size=36, font_family=theme.display_font(), color=theme.ACCENT),
            ])))
    if outcome.attendance:
        sections.append(ft.Text(f"{t('attendance')}: {outcome.attendance:,}", rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED))
    if outcome.newly_unlocked:
        from src.core.achievements import get_achievements
        unlocked = set(outcome.newly_unlocked)
        sections.append(section_card(t("achievements_unlocked"), [
            ft.Text(a["title"], rtl=theme.rtl(), size=14, color=theme.ACCENT)
            for a in get_achievements(conn) if a["key"] in unlocked]))
    sections.extend([tabs, report, ratings, elsewhere])
    return ft.Column(rtl=theme.rtl(), expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(rtl=theme.rtl(), padding=theme.PAGE_PADDING,
                     content=ft.Column(rtl=theme.rtl(), spacing=20, controls=sections))])


# ── Press Conference ────────────────────────────────────────────────────────

_PRESS_QUESTIONS = {
    "win": [
        ("How do you feel about today's result?",
         [("Delighted. The lads were fantastic.", "positive", 3, 2),
          ("Good result, but we can do better.", "neutral", 1, 0),
          ("We expected to win. Nothing special.", "dismissive", -1, -2)]),
        ("Your team dominated today. What's the secret?",
         [("Hard work on the training ground.", "humble", 2, 1),
          ("We have the best squad in the league.", "bold", 0, 3),
          ("I'd rather not reveal our tactics.", "cagey", 1, 0)]),
    ],
    "draw": [
        ("Were you disappointed not to win today?",
         [("Yes, we should have done better.", "honest", 1, 0),
          ("A point is a good result here.", "pragmatic", 2, -1),
          ("The referee cost us the game.", "angry", -2, 2)]),
        ("What do you take away from this game?",
         [("We need to be more clinical.", "analytical", 1, 0),
          ("The fighting spirit is there.", "positive", 2, 1),
          ("I have nothing to say.", "dismissive", -1, -1)]),
    ],
    "loss": [
        ("How would you assess your team's performance today?",
         [("Unacceptable. I expect a reaction.", "demanding", 0, -1),
          ("Credit to the opponent, they were better.", "gracious", 2, 0),
          ("The players let themselves down.", "critical", -2, -2)]),
        ("Are you worried about your position?",
         [("I'm fully focused on the next match.", "focused", 2, 0),
          ("The board knows what I bring.", "defiant", 0, 1),
          ("I'd be worried if I were the players.", "deflecting", -1, -1)]),
    ],
}


def _show_press_conference(page, conn, gs, result, is_home):
    """Show an interactive press conference dialog."""
    from src.ui.app import app_state, navigate, show_snackbar

    user_goals = result.home_goals if is_home else result.away_goals
    opp_goals = result.away_goals if is_home else result.home_goals

    if user_goals > opp_goals:
        result_type = "win"
    elif user_goals < opp_goals:
        result_type = "loss"
    else:
        result_type = "draw"

    questions = _PRESS_QUESTIONS.get(result_type, _PRESS_QUESTIONS["draw"])
    question_data = rng.choice(questions)
    question_text, answers = question_data

    def make_answer_handler(answer_text, tone, board_change, fan_change):
        def handler(e):
            club = queries.get_club(conn, gs.user_club_id)
            if club:
                club.board_confidence = max(0, min(100, club.board_confidence + board_change))
                club.fan_happiness = max(0, min(100, club.fan_happiness + fan_change))
                queries.update_club(conn, club)

            # Generate media reaction
            reaction = f"Manager's response: \"{answer_text}\""
            if board_change > 0:
                reaction += "\n\n👍 The board were pleased with the response."
            elif board_change < 0:
                reaction += "\n\n👎 The board were not impressed."
            if fan_change > 0:
                reaction += "\n🎉 Fans responded positively."
            elif fan_change < 0:
                reaction += "\n😤 Fans were disappointed."

            queries.insert_message(conn, InboxMessage(
                date=gs.current_date,
                subject="🎤 Press Conference Report",
                body=f"Q: {question_text}\n\n{reaction}",
                category="media",
            ))

            page.pop_dialog()
            show_snackbar(page, f"🎤 {t('press_conference')}!")

        return handler

    answer_buttons = []
    for answer_text, tone, board_change, fan_change in answers:
        answer_buttons.append(
            ft.Container(
                rtl=theme.rtl(), content=ft.ListTile(
                    rtl=theme.rtl(), title=ft.Text(display_news(answer_text, conn), rtl=theme.rtl(), size=13),
                    subtitle=ft.Text(display_news(tone), rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                    on_click=make_answer_handler(answer_text, tone, board_change, fan_change),
                ),
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                border_radius=10,
                border=ft.border.all(1, ft.Colors.with_opacity(0.10, theme.GOLD)),
            )
        )

    dlg = ft.AlertDialog(
        rtl=theme.rtl(), title=ft.Column(rtl=theme.rtl(), spacing=4, controls=[
            ft.Text(f"🎤 {t('press_conference')}", rtl=theme.rtl(), size=16,
                     weight=ft.FontWeight.BOLD, color=theme.GOLD),
            ft.Text(t("journalist_asks"), rtl=theme.rtl(), size=11, color=ft.Colors.GREY_400),
        ]),
        content=ft.Container(
            rtl=theme.rtl(), content=ft.Column(
                rtl=theme.rtl(), spacing=8,
                controls=[
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Text(display_news(question_text, conn), rtl=theme.rtl(), size=14, italic=True),
                        padding=10,
                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.BLUE),
                        border_radius=8,
                        border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.BLUE_300)),
                    ),
                    ft.Text(t("choose_your_response"), rtl=theme.rtl(), size=12, color=ft.Colors.GREY_400),
                    *answer_buttons,
                ],
            ),
            width=290, height=320,
        ),
        actions=[
            ft.TextButton(t("skip_to_end"), rtl=theme.rtl(), on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)

