"""
Match Day screen — pre-match info, simulate, and show results.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.calendar import simulate_user_match, advance_to_next_match, advance_day
from src.core.league import is_season_complete, get_champion
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.cards import (
    section_card, info_tile, match_score_card, form_chips, action_card,
)
from src.ui.theme import (
    ACCENT, ACCENT_DARK, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    TEXT_SUCCESS, TEXT_WARNING, TEXT_DANGER,
    CARD_BG, CARD_GLASS, CARD_GLASS_STRONG, CARD_BG_HIGHLIGHT,
    CARD_RADIUS, CARD_RADIUS_SM,
    PAGE_PADDING, SECTION_SPACING,
    TITLE_SIZE, BODY_SIZE, CAPTION_SIZE, TINY_SIZE,
    GOLD, GOLD_BORDER, GOLD_BORDER_STRONG, GOLD_GLOW,
    BG_DARK, BG_MID, BG_TEAL, BG_SURFACE,
    header_bar, gradient_bg, glass_card, golden_divider,
    PRIMARY_BTN_STYLE, SECONDARY_BTN_STYLE,
)
from src.utils.config import MatchEventType, expectation_display


def build_match_day_screen(page: ft.Page) -> ft.Column:
    """Build the match day content."""
    from src.ui.app import app_state, navigate
    page.navigation_bar = build_nav_bar(page, 2)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.SPORTS_SOCCER, size=60, color=ft.Colors.GREY_700),
                ft.Container(height=10),
                ft.Text("No game loaded", size=18, color=ft.Colors.GREY_400),
                ft.Text("Start a new game from the main menu.", size=14, color=ft.Colors.GREY_600),
                ft.Container(height=20),
                ft.ElevatedButton(
                    "🏠 Main Menu",
                    width=250, height=48,
                    style=PRIMARY_BTN_STYLE,
                    on_click=lambda e: navigate(page, "/"),
                ),
            ],
        )

    conn = app_state.db_conn
    gs = app_state.game_state

    # ── Show pending interactive event if any ────────────────────────
    if hasattr(app_state, 'pending_event') and app_state.pending_event is not None:
        _show_event_dialog(page, app_state.pending_event)
        app_state.pending_event = None

    # Check if season is complete
    if is_season_complete(conn):
        champ = get_champion(conn)
        champ_name = champ.club_name if champ else "Unknown"
        champ_pts = champ.points if champ else 0
        is_user_champ = champ and champ.club_id == gs.user_club_id

        trophy_color = ft.Colors.AMBER_400 if is_user_champ else ft.Colors.GREY_400
        congrats_text = "🎉 Congratulations! You are CHAMPIONS!" if is_user_champ else f"{champ_name} are CHAMPIONS!"

        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.EMOJI_EVENTS, size=80, color=trophy_color),
                ft.Container(height=10),
                ft.Text("Season Complete!", size=28, weight=ft.FontWeight.BOLD,
                         color=GOLD, text_align=ft.TextAlign.CENTER),
                ft.Container(height=5),
                ft.Text(congrats_text, size=18, weight=ft.FontWeight.W_500,
                         text_align=ft.TextAlign.CENTER),
                ft.Text(f"{champ_pts} points", size=16, color=ft.Colors.GREY_400,
                         text_align=ft.TextAlign.CENTER),
                ft.Container(height=30),
                ft.ElevatedButton("📊 Season Summary", width=250, height=48,
                                   style=PRIMARY_BTN_STYLE,
                                   on_click=lambda e: navigate(page, "/season_summary")),
                ft.Container(height=10),
                ft.OutlinedButton("📊 View Final Table", width=250, height=45,
                                   on_click=lambda e: navigate(page, "/table"),
                                   style=SECONDARY_BTN_STYLE),
                ft.Container(height=10),
                ft.OutlinedButton("💾 Save Game", width=250, height=45,
                                   on_click=lambda e: _save_and_notify(page, conn, gs),
                                   style=SECONDARY_BTN_STYLE),
                ft.Container(height=10),
                ft.OutlinedButton("🏠 Main Menu", width=250, height=45,
                                   on_click=lambda e: navigate(page, "/"),
                                   style=SECONDARY_BTN_STYLE),
            ],
        )

    # Next fixture for user
    fixture = queries.get_user_next_fixture(conn, gs.user_club_id)

    if fixture is not None:
        return _build_match_preview(page, conn, gs, fixture)
    else:
        return _build_no_match_view(page, conn, gs)


def _build_match_preview(page, conn, gs, fixture):
    """Build the pre-match preview with opponent info and simulate button."""
    from src.ui.app import navigate, show_snackbar

    is_home = fixture.home_club_id == gs.user_club_id
    venue_text = "🏟️ HOME" if is_home else "✈️ AWAY"
    venue_color = ft.Colors.GREEN_400 if is_home else ft.Colors.ORANGE_400

    match_date = fixture.date
    date_str = match_date.strftime("%A, %d %B %Y") if match_date else "TBD"
    matchday_str = f"Matchday {fixture.matchday}"

    user_club = queries.get_club(conn, gs.user_club_id)
    opp_id = fixture.away_club_id if is_home else fixture.home_club_id
    opp_club = queries.get_club(conn, opp_id)

    days_until = (match_date - gs.current_date).days if match_date else 0

    # Opponent form
    opp_form = _build_club_form(conn, opp_id)

    # Head-to-head record
    h2h = queries.get_head_to_head(conn, gs.user_club_id, opp_id)

    # Transfer window status
    from src.core.transfers import get_window_status
    window_status = get_window_status(gs.current_date)

    def simulate_click(e):
        navigate(page, "/pre_match")

    def advance_to_match_click(e):
        advance_to_next_match(conn, gs)
        navigate(page, "/match_day")

    def advance_one_day(e):
        advance_day(conn, gs)
        navigate(page, "/match_day")

    # Match card — use shared widget
    match_card = match_score_card(
        home_name=fixture.home_club_name,
        away_name=fixture.away_club_name,
        competition=fixture.competition,
        matchday=matchday_str,
        is_home=is_home,
        date_str=date_str,
    )

    # Squad availability
    user_squad = queries.get_players_by_club(conn, gs.user_club_id)
    injured_count = sum(1 for p in user_squad if p.injury_days_remaining > 0)
    suspended_count = sum(1 for p in user_squad if p.suspension_matches > 0)

    # Info chips — using shared info_tile
    info_items = []
    if user_club and user_club.formation:
        info_items.append(info_tile("Formation", user_club.formation, icon=ft.Icons.GRID_VIEW))
    if user_club and user_club.mentality:
        info_items.append(info_tile("Mentality",
                                     user_club.mentality.name.replace("_", " ").title(),
                                     icon=ft.Icons.PSYCHOLOGY))
    if opp_club:
        info_items.append(info_tile("Opp. Rep", str(opp_club.reputation), icon=ft.Icons.STAR))
    if user_club:
        from src.core.board import get_confidence_level
        info_items.append(info_tile("Board",
                                     get_confidence_level(user_club.board_confidence).value,
                                     icon=ft.Icons.ACCOUNT_BALANCE))
        info_items.append(info_tile("Target",
                                     expectation_display(user_club.season_expectation),
                                     icon=ft.Icons.FLAG))
    if injured_count > 0:
        info_items.append(info_tile("Injured", str(injured_count),
                                     icon=ft.Icons.LOCAL_HOSPITAL, color=TEXT_DANGER))
    if suspended_count > 0:
        info_items.append(info_tile("Suspended", str(suspended_count),
                                     icon=ft.Icons.BLOCK, color=TEXT_WARNING))

    # Attendance preview
    from src.core.fans import calculate_attendance, get_atmosphere_description
    is_home_match = fixture.home_club_id == gs.user_club_id
    opp_rep_val = opp_club.reputation if opp_club else 100
    expected_attendance = calculate_attendance(user_club, is_home_match, opp_rep_val) if user_club else 0
    atmosphere_text = get_atmosphere_description(user_club.fan_happiness) if user_club else ""

    # Form streak
    form_streak_widget = _build_form_streak(conn, gs.user_club_id)

    # Recent form
    user_form = _build_club_form(conn, gs.user_club_id)

    # Action buttons
    action_controls = []
    if days_until <= 0:
        action_controls.append(
            ft.ElevatedButton(
                "⚽ Play Match",
                width=280, height=56,
                style=PRIMARY_BTN_STYLE,
                on_click=simulate_click,
            )
        )
    else:
        action_controls.append(
            ft.Container(
                content=ft.Text(
                    f"⏳ {days_until} day{'s' if days_until != 1 else ''} until match",
                    size=14, color=GOLD, weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.padding.symmetric(horizontal=16, vertical=10),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.08, GOLD),
                border=ft.border.all(1, GOLD_BORDER),
            )
        )
        action_controls.append(
            ft.ElevatedButton(
                "⏩ Skip to Match Day", width=280, height=50,
                style=PRIMARY_BTN_STYLE,
                on_click=advance_to_match_click,
            )
        )
        action_controls.append(
            ft.OutlinedButton("📅 Advance 1 Day", width=280, height=45,
                               style=SECONDARY_BTN_STYLE,
                               on_click=advance_one_day),
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    controls=[
                        header_bar(
                            title="Match Day",
                            subtitle=f"📅 {gs.current_date.strftime('%d %B %Y')}",
                            icon=ft.Icons.SPORTS_SOCCER,
                            page=page,
                        ),
                        match_card,
                        ft.Row(alignment=ft.MainAxisAlignment.CENTER,
                               spacing=8, wrap=True, controls=info_items
                        ) if info_items else ft.Container(),
                        # Attendance + atmosphere
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER, spacing=12,
                            controls=[
                                ft.Text(f"🏟️ {expected_attendance:,} expected", size=11,
                                         color=ft.Colors.GREY_400) if expected_attendance > 0 else ft.Container(),
                                form_streak_widget if form_streak_widget else ft.Container(),
                            ],
                        ),
                        ft.Text(f"🎤 {atmosphere_text}", size=11, color=ft.Colors.GREY_500,
                                 italic=True, text_align=ft.TextAlign.CENTER) if atmosphere_text else ft.Container(),
                        # Form rows
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER, spacing=15,
                            controls=[
                                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                           spacing=2, controls=[
                                    ft.Text("Your Form", size=10, color=ft.Colors.GREY_500),
                                    user_form,
                                ]),
                                ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                           spacing=2, controls=[
                                    ft.Text("Opponent Form", size=10, color=ft.Colors.GREY_500),
                                    opp_form,
                                ]),
                            ],
                        ),
                        # Head-to-head record
                        *(
                            [ft.Container(
                                content=ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER, spacing=12,
                                    controls=[
                                        ft.Text("📊 H2H:", size=11, color=ft.Colors.GREY_400),
                                        ft.Text(f"W{h2h['wins']}", size=11,
                                                color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                                        ft.Text(f"D{h2h['draws']}", size=11,
                                                color=ft.Colors.YELLOW_400),
                                        ft.Text(f"L{h2h['losses']}", size=11,
                                                color=ft.Colors.RED_400),
                                        ft.Text(f"({h2h['goals_for']}:{h2h['goals_against']})", size=10,
                                                color=ft.Colors.GREY_500),
                                    ],
                                ),
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=8,
                                bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
                                border=ft.border.all(1, ft.Colors.with_opacity(0.12, "#FFD54F")),
                            )] if h2h['total'] > 0 else []
                        ),
                        # Transfer window status
                        ft.Text(window_status, size=10, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(height=5),
                        *action_controls,
                        ft.Container(height=10),

                        # ── Quick Actions ────────────────────────────
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=6, wrap=True,
                            controls=[
                                ft.OutlinedButton("📋 Tactics", height=36,
                                                   on_click=lambda e: navigate(page, "/tactics"),
                                                   style=ft.ButtonStyle(
                                                       shape=ft.RoundedRectangleBorder(radius=10),
                                                       side=ft.BorderSide(1, GOLD_BORDER),
                                                   )),
                                ft.OutlinedButton("💰 Transfers", height=36,
                                                   on_click=lambda e: navigate(page, "/transfers"),
                                                   style=ft.ButtonStyle(
                                                       shape=ft.RoundedRectangleBorder(radius=10),
                                                       side=ft.BorderSide(1, GOLD_BORDER),
                                                   )),
                                ft.OutlinedButton("🏟️ Club", height=36,
                                                   on_click=lambda e: navigate(page, "/club"),
                                                   style=ft.ButtonStyle(
                                                       shape=ft.RoundedRectangleBorder(radius=10),
                                                       side=ft.BorderSide(1, GOLD_BORDER),
                                                   )),
                                *(
                                    [ft.OutlinedButton(
                                        f"🏥 {injured_count + suspended_count}",
                                        height=36,
                                        style=ft.ButtonStyle(color=ft.Colors.RED_400),
                                        on_click=lambda e: _show_availability_dialog(page, user_squad),
                                    )] if (injured_count + suspended_count) > 0 else []
                                ),
                            ],
                        ),

                        # ── Mini League Table ────────────────────────
                        *_build_mini_table(conn, gs.user_club_id),
                        ft.Container(height=5),

                        # ── Matchday Fixture List ────────────────────
                        *_build_matchday_fixtures(conn, fixture, gs.user_club_id),
                    ],
                ),
            ),
        ],
    )


def _build_no_match_view(page, conn, gs):
    """Build the view when there's no upcoming match."""
    from src.ui.app import navigate

    def advance_one(e):
        advance_day(conn, gs)
        navigate(page, "/match_day")

    def advance_to_match(e):
        advance_to_next_match(conn, gs)
        navigate(page, "/match_day")

    return ft.Column(
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Icon(ft.Icons.EVENT_BUSY, size=60, color=ft.Colors.GREY_600),
            ft.Container(height=10),
            ft.Text("No upcoming match found", size=18, color=ft.Colors.GREY_400,
                      weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
            ft.Text(f"Current date: {gs.current_date.strftime('%d %B %Y')}",
                      size=13, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            ft.Container(height=15),
            ft.Text("Try advancing the calendar to find your next fixture.",
                      size=14, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER),
            ft.Container(height=20),
            ft.ElevatedButton("⏩ Skip to Next Match", width=260, height=48,
                               style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700,
                                                     color=ft.Colors.WHITE,
                                                     text_style=ft.TextStyle(size=16)),
                               on_click=advance_to_match),
            ft.Container(height=8),
            ft.OutlinedButton("📅 Advance 1 Day", width=260, height=42,
                               on_click=advance_one),
        ],
    )


def _info_chip(label: str, value: str, icon) -> ft.Container:
    """Create a small info chip."""
    return ft.Container(
        content=ft.Row(
            spacing=5, tight=True,
            controls=[
                ft.Icon(icon, size=14, color=ft.Colors.AMBER_300),
                ft.Column(spacing=0, controls=[
                    ft.Text(label, size=9, color=ft.Colors.GREY_500),
                    ft.Text(value, size=12, weight=ft.FontWeight.BOLD),
                ]),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        border_radius=8,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
    )


def _build_club_form(conn, club_id) -> ft.Row:
    """Build form display (last 5 W/D/L chips) for any club."""
    recent = queries.get_user_recent_fixtures(conn, club_id, limit=5)
    chips = []
    for fixture in recent:
        if not fixture.result:
            continue
        r = fixture.result
        is_home = fixture.home_club_id == club_id
        cg = r.home_goals if is_home else r.away_goals
        og = r.away_goals if is_home else r.home_goals

        if cg > og:
            label, color = "W", ft.Colors.GREEN_400
        elif cg < og:
            label, color = "L", ft.Colors.RED_400
        else:
            label, color = "D", ft.Colors.YELLOW_400

        chips.append(
            ft.Container(
                content=ft.Text(label, size=10, weight=ft.FontWeight.BOLD,
                                 color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                width=24, height=24, border_radius=12,
                bgcolor=color, alignment=ft.Alignment(0, 0),
            )
        )

    if not chips:
        chips.append(ft.Text("—", size=11, color=ft.Colors.GREY_600))

    return ft.Row(spacing=4, controls=chips)


def _pos_suffix(pos: int) -> str:
    """Ordinal suffix for a league position."""
    return {1: "st", 2: "nd", 3: "rd"}.get(pos if pos < 20 else pos % 10, "th")


def _build_form_streak(conn, user_club_id) -> ft.Text | None:
    """Build a form streak text widget (e.g. '3-match win streak 🔥')."""
    try:
        recent = queries.get_user_recent_fixtures(conn, user_club_id, limit=10)
        if not recent:
            return None

        # Determine streak
        streak_type = None
        streak_count = 0
        for fix in recent:
            if not fix.result:
                continue
            if fix.home_club_id == user_club_id:
                ug, og = fix.result.home_goals, fix.result.away_goals
            else:
                ug, og = fix.result.away_goals, fix.result.home_goals

            if ug > og:
                res = "W"
            elif ug < og:
                res = "L"
            else:
                res = "D"

            if streak_type is None:
                streak_type = res
                streak_count = 1
            elif res == streak_type:
                streak_count += 1
            else:
                break

        if streak_count < 2:
            return None

        if streak_type == "W":
            return ft.Text(f"🔥 {streak_count}-match win streak!", size=11,
                            color=ft.Colors.GREEN_400, weight=ft.FontWeight.W_500)
        elif streak_type == "L":
            return ft.Text(f"⚠️ Winless in {streak_count}", size=11,
                            color=ft.Colors.RED_400, weight=ft.FontWeight.W_500)
        elif streak_type == "D":
            return ft.Text(f"😐 {streak_count} draws in a row", size=11,
                            color=ft.Colors.YELLOW_400, weight=ft.FontWeight.W_500)
    except Exception:
        pass
    return None


def _save_and_notify(page, conn, gs):
    """Quick save game from match day screen."""
    from src.ui.app import show_snackbar
    queries.save_game_state(conn, gs)
    show_snackbar(page, "💾 Game saved!")


def _show_result_dialog(page, outcome):
    """Show match result dialog with user result + all other matchday results."""
    from src.ui.app import navigate

    result = outcome.user_result

    # ── Position change ──────────────────────────────────────────────
    pos_widgets = []
    if outcome.position_before > 0 and outcome.position_after > 0:
        delta = outcome.position_before - outcome.position_after  # positive = moved up
        if delta > 0:
            pos_text = f"▲ {outcome.position_after}{_pos_suffix(outcome.position_after)} (up {delta})"
            pos_color = ft.Colors.GREEN_400
        elif delta < 0:
            pos_text = f"▼ {outcome.position_after}{_pos_suffix(outcome.position_after)} (down {abs(delta)})"
            pos_color = ft.Colors.RED_400
        else:
            pos_text = f"— {outcome.position_after}{_pos_suffix(outcome.position_after)} (unchanged)"
            pos_color = ft.Colors.GREY_400
        pos_widgets.append(ft.Text(pos_text, size=13, color=pos_color, weight=ft.FontWeight.W_500,
                                    text_align=ft.TextAlign.CENTER))

    # ── Attendance ───────────────────────────────────────────────────
    attendance_text = ""
    if outcome.attendance > 0:
        attendance_text = f"🏟️ Attendance: {outcome.attendance:,}"

    # Goal widgets
    goal_widgets = []
    goals = [e for e in result.events if e.event_type == MatchEventType.GOAL]
    if goals:
        for g in goals:
            goal_text = f"⚽ {g.minute}' {g.player_name}"
            if g.second_player_name:
                goal_text += f" (assist: {g.second_player_name})"
            side = "🏠" if g.club_id == result.home_club_id else "✈️"
            goal_widgets.append(ft.Text(f"{side} {goal_text}", size=12))
    else:
        goal_widgets.append(ft.Text("No goals scored", size=12, color=ft.Colors.GREY_500))

    # Stats rows
    stats_rows = [
        ("Possession", f"{result.home_stats.possession:.0f}%", f"{result.away_stats.possession:.0f}%"),
        ("Shots", str(result.home_stats.shots), str(result.away_stats.shots)),
        ("On Target", str(result.home_stats.shots_on_target), str(result.away_stats.shots_on_target)),
        ("Corners", str(result.home_stats.corners), str(result.away_stats.corners)),
        ("Fouls", str(result.home_stats.fouls), str(result.away_stats.fouls)),
        ("Yellow Cards", str(result.home_stats.yellow_cards), str(result.away_stats.yellow_cards)),
        ("Red Cards", str(result.home_stats.red_cards), str(result.away_stats.red_cards)),
    ]
    stat_widgets = []
    for label, home_val, away_val in stats_rows:
        stat_widgets.append(ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(home_val, size=12, width=40, text_align=ft.TextAlign.CENTER),
                ft.Text(label, size=11, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
                ft.Text(away_val, size=12, width=40, text_align=ft.TextAlign.CENTER),
            ],
        ))

    # Cards & injuries
    card_injury_widgets = []
    cards = [e for e in result.events if e.event_type in (MatchEventType.YELLOW_CARD, MatchEventType.RED_CARD)]
    injuries = [e for e in result.events if e.event_type == MatchEventType.INJURY]
    if cards:
        for c in cards:
            icon = "🟡" if c.event_type == MatchEventType.YELLOW_CARD else "🟥"
            card_injury_widgets.append(
                ft.Text(f"{icon} {c.minute}' {c.player_name}", size=11)
            )
    if injuries:
        for inj in injuries:
            card_injury_widgets.append(
                ft.Text(f"🏥 {inj.minute}' {inj.description}", size=11, color=ft.Colors.RED_400)
            )

    # Other results on the same matchday
    other_results_widgets = []
    if outcome.other_results:
        other_results_widgets.append(ft.Divider())
        other_results_widgets.append(
            ft.Text(f"📋 Other Matchday {outcome.matchday} Results",
                     size=14, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_300))
        for r in outcome.other_results:
            other_results_widgets.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Text(r.home_club_name, size=11,
                                     text_align=ft.TextAlign.RIGHT, expand=True,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Container(
                                content=ft.Text(f"{r.home_goals}-{r.away_goals}",
                                                 size=12, weight=ft.FontWeight.BOLD),
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                                padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=4,
                            ),
                            ft.Text(r.away_club_name, size=11,
                                     text_align=ft.TextAlign.LEFT, expand=True,
                                     max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ],
                    ),
                    padding=ft.padding.symmetric(vertical=2),
                )
            )

    def close_and_refresh(e):
        page.pop_dialog()
        navigate(page, "/match_day")

    def show_commentary(e):
        """Show full minute-by-minute commentary log."""
        all_events = [ev for ev in result.events
                      if ev.event_type not in (MatchEventType.KICKOFF, MatchEventType.FULL_TIME)]
        event_rows = []
        for ev in all_events:
            icon = {
                MatchEventType.GOAL: "⚽",
                MatchEventType.SHOT_ON_TARGET: "🎯",
                MatchEventType.SHOT_OFF_TARGET: "💨",
                MatchEventType.YELLOW_CARD: "🟡",
                MatchEventType.RED_CARD: "🟥",
                MatchEventType.CORNER: "📐",
                MatchEventType.HALF_TIME: "⏸️",
                MatchEventType.INJURY: "🏥",
            }.get(ev.event_type, "📌")
            event_rows.append(
                ft.Text(f"{ev.minute}' {icon} {ev.description}", size=11)
            )
        if not event_rows:
            event_rows.append(ft.Text("No notable events.", size=12, color=ft.Colors.GREY_500))

        commentary_dlg = ft.AlertDialog(
            title=ft.Text("📜 Match Commentary", size=16,
                           weight=ft.FontWeight.BOLD, color="#FFD54F"),
            content=ft.Container(
                content=ft.Column(controls=event_rows, spacing=3, scroll=ft.ScrollMode.AUTO),
                width=290, height=400,
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
        )
        page.show_dialog(commentary_dlg)

    def show_ratings(e):
        """Show individual player ratings grouped by team."""
        from src.ui.app import app_state

        conn = app_state.db_conn
        all_ratings = result.player_ratings

        # Build a name lookup: load both squads from DB
        home_players = queries.get_players_by_club(conn, result.home_club_id) if conn else []
        away_players = queries.get_players_by_club(conn, result.away_club_id) if conn else []
        name_map = {p.id: p.name for p in home_players + away_players}
        home_ids = {p.id for p in home_players}

        # Split ratings by team
        home_ratings = [(pid, r) for pid, r in all_ratings.items() if pid in home_ids]
        away_ratings = [(pid, r) for pid, r in all_ratings.items() if pid not in home_ids]

        # Sort each team by rating descending
        home_ratings.sort(key=lambda x: -x[1])
        away_ratings.sort(key=lambda x: -x[1])

        def _rating_color(rating: float) -> str:
            if rating >= 7.5:
                return ft.Colors.GREEN_400
            elif rating >= 6.5:
                return ft.Colors.YELLOW_400
            else:
                return ft.Colors.RED_400

        def _build_rating_row(pid: int, rating: float) -> ft.Container:
            name = name_map.get(pid, f"Player #{pid}")
            return ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(name, size=12, expand=True),
                        ft.Container(
                            content=ft.Text(
                                f"{rating:.1f}",
                                size=13, weight=ft.FontWeight.BOLD,
                                color=_rating_color(rating),
                            ),
                            width=40,
                            alignment=ft.Alignment(1, 0),
                        ),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=4, vertical=2),
            )

        rating_controls = []

        # Home team section
        rating_controls.append(
            ft.Text(f"🏠 {result.home_club_name}", size=13,
                     weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)
        )
        if home_ratings:
            for pid, r in home_ratings:
                rating_controls.append(_build_rating_row(pid, r))
        else:
            rating_controls.append(ft.Text("No ratings", size=11, color=ft.Colors.GREY_500))

        rating_controls.append(ft.Divider(height=1))

        # Away team section
        rating_controls.append(
            ft.Text(f"✈️ {result.away_club_name}", size=13,
                     weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_300)
        )
        if away_ratings:
            for pid, r in away_ratings:
                rating_controls.append(_build_rating_row(pid, r))
        else:
            rating_controls.append(ft.Text("No ratings", size=11, color=ft.Colors.GREY_500))

        ratings_dlg = ft.AlertDialog(
            title=ft.Text("📊 Player Ratings", size=16,
                           weight=ft.FontWeight.BOLD, color="#FFD54F"),
            content=ft.Container(
                content=ft.Column(
                    controls=rating_controls,
                    spacing=2,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=290, height=420,
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
        )
        page.show_dialog(ratings_dlg)

    dlg = ft.AlertDialog(
        title=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2,
            controls=[
                ft.Text("Full Time", size=12, color=ft.Colors.GREY_500),
                ft.Text(result.score_display, size=20, weight=ft.FontWeight.BOLD,
                         text_align=ft.TextAlign.CENTER, color=ft.Colors.AMBER_300),
                *pos_widgets,
                *(
                    [ft.Text(attendance_text, size=11, color=ft.Colors.GREY_500)]
                    if attendance_text else []
                ),
            ],
        ),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Divider(),
                    ft.Text("⚽ Goals", size=14, weight=ft.FontWeight.W_500),
                    *goal_widgets,
                    ft.Divider(),
                    ft.Text("📊 Match Stats", size=14, weight=ft.FontWeight.W_500),
                    ft.Container(height=5),
                    ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                        ft.Text(result.home_club_name, size=11, weight=ft.FontWeight.BOLD,
                                expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text("", size=11),
                        ft.Text(result.away_club_name, size=11, weight=ft.FontWeight.BOLD,
                                 expand=True, text_align=ft.TextAlign.RIGHT,
                                 max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ]),
                    *stat_widgets,
                    *(
                        [ft.Divider(),
                         ft.Text("📋 Cards & Injuries", size=14, weight=ft.FontWeight.W_500)]
                        + card_injury_widgets
                        if card_injury_widgets else []
                    ),
                    *other_results_widgets,
                ],
                spacing=5,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=290,
            height=420,
        ),
        actions=[
            ft.TextButton("📜 Commentary", on_click=show_commentary),
            ft.TextButton("📊 Ratings", on_click=show_ratings),
            ft.TextButton("Continue ➡️", on_click=close_and_refresh),
        ],
    )
    page.show_dialog(dlg)


def _show_event_dialog(page, event):
    """Show an interactive event dialog with choices."""
    from src.ui.app import app_state, show_snackbar
    from src.core.events import apply_event_choice

    choice_buttons = []
    for i, choice in enumerate(event.choices):
        def make_handler(idx=i):
            def handler(e):
                conn = app_state.db_conn
                gs = app_state.game_state
                if conn and gs:
                    response = apply_event_choice(conn, gs, event, idx)
                    show_snackbar(page, response[:80], bgcolor=ft.Colors.AMBER_800)
                page.pop_dialog()
            return handler

        # Show effect hints
        hints = []
        if choice.board_delta > 0:
            hints.append(f"👔+{choice.board_delta}")
        elif choice.board_delta < 0:
            hints.append(f"👔{choice.board_delta}")
        if choice.fan_delta > 0:
            hints.append(f"👥+{choice.fan_delta}")
        elif choice.fan_delta < 0:
            hints.append(f"👥{choice.fan_delta}")
        if choice.finance_delta > 0:
            hints.append(f"💰+{choice.finance_delta:,}")
        elif choice.finance_delta < 0:
            hints.append(f"💰{choice.finance_delta:,}")
        if choice.morale_delta > 0:
            hints.append(f"😊+{choice.morale_delta}")
        elif choice.morale_delta < 0:
            hints.append(f"😊{choice.morale_delta}")
        hint_text = "  ".join(hints) if hints else ""

        choice_buttons.append(
            ft.Container(
                content=ft.Column(spacing=2, controls=[
                    ft.Text(choice.text, size=13, weight=ft.FontWeight.W_500),
                    ft.Text(hint_text, size=9, color=ft.Colors.GREY_500) if hint_text else ft.Container(),
                ]),
                padding=ft.padding.symmetric(horizontal=12, vertical=12),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                border=ft.border.all(1, ft.Colors.with_opacity(0.12, "#FFD54F")),
                on_click=make_handler(),
                ink=True,
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text(event.title, size=16, weight=ft.FontWeight.BOLD, color="#FFD54F"),
        content=ft.Container(
            content=ft.Column(spacing=8, controls=[
                ft.Container(
                    content=ft.Text(event.body, size=13),
                    padding=10,
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.BLUE),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.BLUE_300)),
                ),
                ft.Text("Choose your response:", size=12, color=ft.Colors.GREY_400),
                *choice_buttons,
            ]),
            width=300, height=min(320, 100 + len(event.choices) * 65),
        ),
    )
    page.show_dialog(dlg)


def _build_mini_table(conn, user_club_id) -> list:
    """Build a mini 5-row league table centered on the user's position."""
    standings = queries.get_standings(conn)
    if not standings:
        return []

    user_idx = -1
    for i, s in enumerate(standings):
        if s.club_id == user_club_id:
            user_idx = i
            break

    if user_idx < 0:
        return []

    # Show 2 above and 2 below (clamped to bounds)
    start = max(0, user_idx - 2)
    end = min(len(standings), user_idx + 3)
    subset = standings[start:end]

    rows = []
    for i, s in enumerate(subset):
        pos = start + i + 1
        is_user = s.club_id == user_club_id
        bg = ft.Colors.with_opacity(0.15, ft.Colors.AMBER) if is_user else ft.Colors.with_opacity(0.04, ft.Colors.WHITE)
        weight = ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL
        rows.append(
            ft.Container(
                content=ft.Row(
                    spacing=0,
                    controls=[
                        ft.Text(str(pos), size=11, width=22, weight=weight,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(s.club_name, size=11, expand=True, weight=weight,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(str(s.played), size=10, width=20, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{s.goal_difference:+d}", size=10, width=28,
                                color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(s.points), size=11, width=26, weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER,
                                color=ft.Colors.AMBER_300 if is_user else ft.Colors.WHITE),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=6, vertical=4),
                border_radius=4,
                bgcolor=bg,
            )
        )

    return [
        ft.Container(height=4),
        ft.Container(
            content=ft.Column(spacing=0, controls=[
                ft.Container(
                    content=ft.Row(spacing=0, controls=[
                        ft.Text("", width=22),
                        ft.Text("📊 League Table", size=12, weight=ft.FontWeight.W_500,
                                expand=True, color=ft.Colors.AMBER_300),
                        ft.Text("P", size=9, width=20, color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("GD", size=9, width=28, color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("Pts", size=9, width=26, color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER),
                    ]),
                    padding=ft.padding.only(left=6, right=6, bottom=2),
                ),
                *rows,
                ft.Container(
                    content=ft.Text("Tap Table tab for full standings", size=9,
                                     color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER,
                                     italic=True),
                    padding=ft.padding.only(top=4),
                ),
            ]),
            padding=ft.padding.symmetric(vertical=6, horizontal=4),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, "#FFD54F")),
        ),
    ]


def _build_matchday_fixtures(conn, current_fixture, user_club_id) -> list:
    """Build a list of all fixtures for the current matchday."""
    all_fixtures = queries.get_fixtures_by_matchday(conn, current_fixture.matchday)
    if not all_fixtures or len(all_fixtures) <= 1:
        return []

    fixture_rows = []
    for f in all_fixtures:
        is_user = (f.home_club_id == user_club_id or f.away_club_id == user_club_id)
        bg = ft.Colors.with_opacity(0.12, ft.Colors.AMBER) if is_user else None
        weight = ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL

        if f.played and f.result:
            score_text = f"{f.result.home_goals}-{f.result.away_goals}"
            score_color = ft.Colors.WHITE
        else:
            score_text = "vs"
            score_color = ft.Colors.GREY_500

        fixture_rows.append(
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER, spacing=4,
                    controls=[
                        ft.Text(f.home_club_name, size=11, weight=weight,
                                text_align=ft.TextAlign.RIGHT, expand=True,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(
                            content=ft.Text(score_text, size=11, weight=ft.FontWeight.BOLD,
                                            color=score_color),
                            width=36, alignment=ft.Alignment(0, 0),
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                            border_radius=4,
                            padding=ft.padding.symmetric(vertical=2),
                        ),
                        ft.Text(f.away_club_name, size=11, weight=weight,
                                text_align=ft.TextAlign.LEFT, expand=True,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=6, vertical=3),
                border_radius=4,
                bgcolor=bg,
            )
        )

    return [
        ft.Container(
            content=ft.Column(spacing=0, controls=[
                ft.Text(f"📋 Matchday {current_fixture.matchday} Fixtures",
                         size=12, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_300),
                ft.Container(height=4),
                *fixture_rows,
            ]),
            padding=ft.padding.symmetric(vertical=6, horizontal=4),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, "#FFD54F")),
        ),
    ]


def _show_availability_dialog(page, squad):
    """Show a dialog listing all injured and suspended players."""
    injured = [p for p in squad if p.injury_days_remaining > 0]
    suspended = [p for p in squad if p.suspension_matches > 0]

    rows = []
    if injured:
        rows.append(ft.Text("🏥 Injured", size=14, weight=ft.FontWeight.W_500,
                             color=ft.Colors.RED_400))
        for p in injured:
            rows.append(ft.Container(
                content=ft.Row(spacing=8, controls=[
                    ft.Text(p.position.value, size=10, color=ft.Colors.AMBER_300, width=28),
                    ft.Text(p.name, size=12, expand=True),
                    ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[
                        ft.Text(p.injury_type or "Injury", size=10, color=ft.Colors.RED_300),
                        ft.Text(f"{p.injury_days_remaining}d remaining", size=9,
                                color=ft.Colors.GREY_500),
                    ]),
                ]),
                padding=ft.padding.symmetric(horizontal=6, vertical=4),
            ))
        rows.append(ft.Divider(height=1))

    if suspended:
        rows.append(ft.Text("🚫 Suspended", size=14, weight=ft.FontWeight.W_500,
                             color=ft.Colors.ORANGE_400))
        for p in suspended:
            rows.append(ft.Container(
                content=ft.Row(spacing=8, controls=[
                    ft.Text(p.position.value, size=10, color=ft.Colors.AMBER_300, width=28),
                    ft.Text(p.name, size=12, expand=True),
                    ft.Text(f"{p.suspension_matches} match(es)", size=10,
                            color=ft.Colors.ORANGE_300),
                ]),
                padding=ft.padding.symmetric(horizontal=6, vertical=4),
            ))

    if not rows:
        rows.append(ft.Text("All players available! ✅", size=13, color=ft.Colors.GREEN_400))

    dlg = ft.AlertDialog(
        title=ft.Text("🏥 Squad Availability", size=16,
                       weight=ft.FontWeight.BOLD, color="#FFD54F"),
        content=ft.Container(
            content=ft.Column(spacing=4, controls=rows, scroll=ft.ScrollMode.AUTO),
            width=290, height=300,
        ),
        actions=[ft.TextButton("Close", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)


