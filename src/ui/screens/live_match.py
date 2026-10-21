"""
Live Match screen — FIFA-style minute-by-minute match simulation.

Shows a running clock from 0' → 90'+, with events popping up in real-time,
a live scoreline, and a "Skip to End" button.

Uses page.run_task() with an async function so that asyncio.sleep() yields
back to the Flet event loop, allowing page.update() to flush immediately.
"""
from __future__ import annotations

import asyncio

import flet as ft
from src.ui import theme

from src.utils.config import MatchEventType
from src.data.models import MatchEvent
from src.data import queries
from src.core import club as club_module, match_engine
from src.core.calendar import finalize_user_matchday
from src.utils.localization import t, display_name, display_home_name, display_away_name, is_rtl
# from src.utils.audio import play_goal, play_full_time  # [SOUND DISABLED]
from src.utils import rng


# Event icons
_EVENT_ICONS = {
    MatchEventType.GOAL: "⚽",
    MatchEventType.SHOT_ON_TARGET: "🎯",
    MatchEventType.SHOT_OFF_TARGET: "💨",
    MatchEventType.YELLOW_CARD: "🟡",
    MatchEventType.RED_CARD: "🟥",
    MatchEventType.CORNER: "📐",
    MatchEventType.HALF_TIME: "⏸️",
    MatchEventType.FULL_TIME: "🏁",
    MatchEventType.INJURY: "🏥",
    MatchEventType.KICKOFF: "🏟️",
    MatchEventType.PENALTY: "⚽",
    MatchEventType.PENALTY_MISS: "❌",
    MatchEventType.SAVE: "🧤",
}

_MAJOR_EVENTS = {
    MatchEventType.GOAL,
    MatchEventType.YELLOW_CARD,
    MatchEventType.RED_CARD,
    MatchEventType.INJURY,
    MatchEventType.HALF_TIME,
    MatchEventType.FULL_TIME,
    MatchEventType.KICKOFF,
    MatchEventType.PENALTY,
    MatchEventType.PENALTY_MISS,
}


def _compute_target_minute(elapsed_seconds: float, seconds_per_minute: float, total_minutes: int) -> int:
    """Map elapsed wall time to an in-match minute index, clamped to bounds."""
    if total_minutes <= 1:
        return 0
    if seconds_per_minute <= 0:
        return total_minutes - 1
    if elapsed_seconds <= 0:
        return 0
    return min(total_minutes - 1, int(elapsed_seconds / seconds_per_minute))


def _next_minute_to_render(last_rendered: int, target_minute: int, total_minutes: int) -> int | None:
    """Return the next minute to render, or None when already caught up."""
    nxt = last_rendered + 1
    if nxt > target_minute or nxt >= total_minutes:
        return None
    return nxt


def build_live_match_screen(page: ft.Page, outcome) -> ft.Column:
    """Build the live match simulation view."""
    from src.ui.app import app_state, navigate

    match_token = object()
    app_state._live_match_token = match_token

    # Store outcome for the post-match screen
    app_state._last_outcome = outcome
    app_state._post_match_nav_in_progress = False

    result = outcome.user_result
    conn = app_state.db_conn
    gs = app_state.game_state
    user_is_home = result.home_club_id == gs.user_club_id

    # Mutable active XI displayed by the live substitution picker.
    active_user_xi = [list(outcome.home_starting_xi if user_is_home else outcome.away_starting_xi)]
    if not active_user_xi[0] and conn and gs:
        club = queries.get_club(conn, gs.user_club_id)
        squad = queries.get_players_by_club(conn, gs.user_club_id)
        if club and squad:
            active_user_xi[0] = list(club_module.prepare_team_for_match(club, squad).starting_xi)

    # Snapshot of who actually kicked off (the user's submitted XI). The sub
    # dialog uses this to tell players subbed OFF/ON during the match apart
    # from the real current pitch state.
    original_user_xi = list(active_user_xi[0])

    # ── Pre-index events by minute ───────────────────────────────────
    events_by_minute: dict[int, list] = {}
    for ev in result.events:
        events_by_minute.setdefault(ev.minute, []).append(ev)

    max_minute = 90
    for ev in result.events:
        if ev.minute > max_minute:
            max_minute = ev.minute
    total_minutes = max_minute + 1

    # Mutable state
    home_goals = [0]
    away_goals = [0]
    skip_flag = [False]
    halftime_done = [False]
    halftime_choice = [None]  # Will store the team talk choice
    subs_remaining = [3]      # 3 substitutions allowed per match
    subs_made = []            # Track (off_name, on_name, minute) for display
    sub_pending = [False]     # True while sub dialog is open

    # ── UI Controls ──────────────────────────────────────────────────
    score_text = ft.Text(
        "0 - 0", size=36, weight=ft.FontWeight.BOLD,
        color=theme.GOLD, text_align=ft.TextAlign.CENTER,
    )
    minute_text = ft.Text(
        "0'", size=20, color=ft.Colors.GREY_400,
        weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER,
    )
    progress_bar = ft.ProgressBar(
        value=0, color=theme.ACCENT_DARK,
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
    )
    status_text = ft.Text(
        ("⏳ قبل المباراة" if is_rtl() else "⏳ Pre-Match"), size=13, color=ft.Colors.GREY_500,
        text_align=ft.TextAlign.CENTER,
    )
    event_list = ft.ListView(spacing=6, height=max(180, min(340, (page.height or 844) - 400)), auto_scroll=True)

    skip_btn = ft.ElevatedButton(
        ("⏩ تخطي للنهاية" if is_rtl() else "⏩ Skip to End"), width=140, height=42,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            color=ft.Colors.WHITE,
            text_style=ft.TextStyle(size=13),
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, ft.Colors.with_opacity(0.18, theme.GOLD)),
        ),
    )
    subs_btn = ft.ElevatedButton(
        f"🔄 {t('substitution')} ({subs_remaining[0]})", width=120, height=42, visible=False,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.BLUE),
            color=ft.Colors.WHITE,
            text_style=ft.TextStyle(size=13),
            shape=ft.RoundedRectangleBorder(radius=10),
            side=ft.BorderSide(1, ft.Colors.with_opacity(0.25, ft.Colors.BLUE)),
        ),
    )
    continue_btn = ft.ElevatedButton(
        t("continue_btn"), width=200, height=48, visible=False,
        style=ft.ButtonStyle(
            bgcolor=theme.ACCENT_DARK, color=ft.Colors.WHITE,
            text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
            shape=ft.RoundedRectangleBorder(radius=12),
            elevation=4,
            shadow_color=ft.Colors.with_opacity(0.25, theme.GOLD),
        ),
    )

    def on_skip(e):
        skip_flag[0] = True

    def on_continue(e):
        if getattr(app_state, "_post_match_nav_in_progress", False):
            return
        app_state._post_match_nav_in_progress = True
        continue_btn.disabled = True
        continue_btn.text = "⏳ Continuing..."
        page.update()

        from src.ui.app import show_snackbar

        # ── Apply halftime team talk effects to player morale ────────
        try:
            _apply_team_talk(conn, gs, halftime_choice[0], result)

            # Persist the live-edited result (including substitutions) now.
            finalized = finalize_user_matchday(conn, gs, outcome)
            if finalized:
                outcome.fixture_id = finalized.fixture_id
                outcome.user_result = finalized.user_result
                outcome.other_results = finalized.other_results
                outcome.position_before = finalized.position_before
                outcome.position_after = finalized.position_after
                outcome.attendance = finalized.attendance
                outcome.newly_unlocked = finalized.newly_unlocked

            # ── Restore root page structure ──────────────────────────────
            # play_match() in pre_match.py cleared page.controls and added
            # the live-match content directly, which orphaned the
            # transition_container / notification overlay Stack.  We must
            # rebuild it before calling navigate() so the transition
            # container is back in the page's control tree.
            _restore_page_root(page)

            navigate(page, "/post_match")
        except Exception as ex:
            app_state._post_match_nav_in_progress = False
            continue_btn.disabled = False
            continue_btn.text = t("continue_btn")
            page.update()
            show_snackbar(page, f"{t('error')}: {ex}", bgcolor=ft.Colors.RED_800)

    def on_subs(e):
        if subs_remaining[0] <= 0 or sub_pending[0]:
            return
        sub_pending[0] = True
        _show_sub_dialog(
            page,
            outcome,
            event_list,
            events_by_minute,
            active_user_xi,
            subs_remaining,
            subs_made,
            sub_pending,
            subs_btn,
            minute_text,
            original_user_xi=original_user_xi,
        )

    skip_btn.on_click = on_skip
    continue_btn.on_click = on_continue
    subs_btn.on_click = on_subs

    comp_text = result.competition or "Egyptian Premier League"
    matchday_label = f"Matchday {result.matchday}" if result.matchday else ""

    # ── Event row builder ────────────────────────────────────────────
    def _make_event_row(ev) -> ft.Container:
        icon = _EVENT_ICONS.get(ev.event_type, "📌")
        is_goal = ev.event_type == MatchEventType.GOAL
        is_major = ev.event_type in _MAJOR_EVENTS

        if is_goal:
            bg = ft.Colors.with_opacity(0.15, ft.Colors.GREEN)
        elif ev.event_type == MatchEventType.RED_CARD:
            bg = ft.Colors.with_opacity(0.15, ft.Colors.RED)
        elif ev.event_type == MatchEventType.INJURY:
            bg = ft.Colors.with_opacity(0.12, ft.Colors.ORANGE)
        elif ev.event_type == MatchEventType.HALF_TIME:
            bg = ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
        else:
            bg = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)

        return ft.Container(
            content=ft.Row(
                spacing=8,
                controls=[
                    ft.Text(f"{ev.minute}'", size=11, color=ft.Colors.GREY_500,
                             width=30, text_align=ft.TextAlign.RIGHT),
                    ft.Text(icon, size=14),
                    ft.Text(
                        ev.description_ar if is_rtl() else ev.description,
                        size=13 if is_major else 11,
                        weight=ft.FontWeight.BOLD if is_goal else ft.FontWeight.NORMAL,
                        color=ft.Colors.GREEN_300 if is_goal else ft.Colors.WHITE,
                        expand=True,
                    ),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=8, vertical=5),
            border_radius=8,
            bgcolor=bg,
            border=ft.border.only(
                left=ft.BorderSide(2,
                    ft.Colors.GREEN_400 if is_goal else
                    ft.Colors.RED_400 if ev.event_type == MatchEventType.RED_CARD else
                    ft.Colors.with_opacity(0.15, ft.Colors.WHITE)),
            ),
        )

    # ── Async simulation (runs on the Flet event loop) ───────────────
    async def _run_simulation():
        """
        Tick through EVERY minute from 0 → 90+ at a steady pace.
        Using asyncio.sleep() yields to the Flet event loop each tick,
        so page.update() flushes to the client immediately — no focus needed.
        """
        speed = 3
        if conn:
            row = conn.execute("SELECT match_speed FROM game_settings WHERE id=1").fetchone()
            if row:
                speed = int(row[0])
        SECONDS_PER_MINUTE = {1: 0.6, 2: 0.3, 3: 0.12, 4: 0.04, 5: 0.01}.get(speed, 0.12)
        GOAL_PAUSE = 1.5
        MAJOR_PAUSE = 0.8
        HALF_TIME_PAUSE = 1.2
        MINOR_EVENT_EXTRA = 0.15

        for minute in range(total_minutes):
            if app_state._live_match_token is not match_token:
                return
            while sub_pending[0] and not skip_flag[0]:
                if app_state._live_match_token is not match_token:
                    return
                await asyncio.sleep(0.1)
            if skip_flag[0]:
                break

            # ── Update clock every single minute ─────────────────
            minute_text.value = f"{minute}'"
            progress_bar.value = min(minute / max(total_minutes - 1, 1), 1.0)

            if minute == 0:
                status_text.value = ("🏟️ انطلاق المباراة" if is_rtl() else "🏟️ Kick Off!")
                status_text.color = ft.Colors.GREEN_400
            elif minute < 45:
                status_text.value = (f"الشوط الأول — {minute}'" if is_rtl() else f"1st Half — {minute}'")
                status_text.color = ft.Colors.GREY_500
            elif minute == 45:
                status_text.value = ("الشوط الأول — 45'" if is_rtl() else "1st Half — 45'")
                status_text.color = ft.Colors.GREY_500
            elif minute <= 90:
                status_text.value = (f"الشوط الثاني — {minute}'" if is_rtl() else f"2nd Half — {minute}'")
                status_text.color = ft.Colors.GREY_500
                # Show subs button in second half
                if subs_remaining[0] > 0 and minute >= 46 and minute <= 85:
                    subs_btn.visible = True
                else:
                    subs_btn.visible = False
            else:
                status_text.value = (f"الوقت بدل الضائع — {minute}'" if is_rtl() else f"Added Time — {minute}'")
                status_text.color = theme.ACCENT
                subs_btn.visible = False

            page.update()

            # ── Show events that happen at this minute ───────────
            events_now = events_by_minute.get(minute, [])
            extra_pause = 0.0

            for ev in events_now:
                if skip_flag[0]:
                    break

                if ev.event_type in (MatchEventType.GOAL, MatchEventType.PENALTY):
                    if ev.club_id == result.home_club_id:
                        home_goals[0] += 1
                    else:
                        away_goals[0] += 1
                    score_text.value = f"{home_goals[0]} - {away_goals[0]}"
                    # play_goal()  # [SOUND DISABLED]

                if ev.event_type == MatchEventType.HALF_TIME:
                    status_text.value = ("⏸️ استراحة" if is_rtl() else "⏸️ Half Time")
                    status_text.color = ft.Colors.BLUE_400
                    # Show team talk at halftime (unless skipping)
                    if not skip_flag[0] and not halftime_done[0]:
                        halftime_done[0] = True
                        _show_halftime_talk(page, event_list, halftime_choice)
                        page.update()
                        # Wait until user makes a choice
                        while halftime_choice[0] is None and not skip_flag[0]:
                            if app_state._live_match_token is not match_token:
                                return
                            await asyncio.sleep(0.15)
                        if halftime_choice[0]:
                            event_list.controls.append(ft.Container(
                                content=ft.Row(spacing=6, controls=[
                                    ft.Text("HT", size=11, color=ft.Colors.GREY_500, width=30,
                                            text_align=ft.TextAlign.RIGHT),
                                    ft.Text("🗣️", size=14),
                                    ft.Text(f"Team Talk: {halftime_choice[0]}", size=12,
                                            color=ft.Colors.BLUE_300, weight=ft.FontWeight.W_500),
                                ]),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=6,
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
                            ))
                            page.update()
                elif ev.event_type == MatchEventType.FULL_TIME:
                    status_text.value = f"🏁 {t('full_time')}"
                    status_text.color = theme.GOLD
                    # play_full_time()  # [SOUND DISABLED]

                event_list.controls.append(_make_event_row(ev))
                page.update()

                if ev.event_type in (MatchEventType.GOAL, MatchEventType.PENALTY):
                    extra_pause = max(extra_pause, GOAL_PAUSE)
                elif ev.event_type == MatchEventType.HALF_TIME:
                    extra_pause = max(extra_pause, HALF_TIME_PAUSE)
                elif ev.event_type in (MatchEventType.RED_CARD, MatchEventType.INJURY):
                    extra_pause = max(extra_pause, MAJOR_PAUSE)
                elif ev.event_type in _MAJOR_EVENTS:
                    extra_pause = max(extra_pause, MINOR_EVENT_EXTRA)

            # ── Yield to event loop with asyncio.sleep ───────────
            if not skip_flag[0]:
                await asyncio.sleep(extra_pause if extra_pause > 0 else SECONDS_PER_MINUTE)
                # Pause while substitution dialog is open
                while sub_pending[0] and not skip_flag[0]:
                    if app_state._live_match_token is not match_token:
                        return
                    await asyncio.sleep(0.1)

        # ── Finish ───────────────────────────────────────────────
        home_goals[0] = result.home_goals
        away_goals[0] = result.away_goals
        score_text.value = f"{result.home_goals} - {result.away_goals}"
        minute_text.value = "FT"
        progress_bar.value = 1.0
        status_text.value = f"🏁 {t('full_time')}"
        status_text.color = theme.GOLD
        skip_btn.visible = False
        subs_btn.visible = False          # ← hide subs at full time
        continue_btn.visible = True

        if skip_flag[0]:
            event_list.controls.clear()
            for m in sorted(events_by_minute.keys()):
                for ev in events_by_minute[m]:
                    if ev.event_type in _MAJOR_EVENTS:
                        event_list.controls.append(_make_event_row(ev))

        page.update()

    # ── Layout ───────────────────────────────────────────────────────
    content = ft.Column(
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        # Header
                        ft.Container(
                            content=ft.Text(comp_text, size=12, color=theme.GOLD,
                                             weight=ft.FontWeight.W_600),
                            padding=ft.padding.symmetric(horizontal=12, vertical=4),
                            border_radius=8,
                            bgcolor=ft.Colors.with_opacity(0.10, theme.GOLD),
                        ),
                        ft.Text(matchday_label, size=11, color=ft.Colors.GREY_600),

                        # Scoreboard — glass card
                        ft.Container(
                            content=ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=10,
                                        controls=[
                                            ft.Text(
                                                display_home_name(result), size=14,
                                                weight=ft.FontWeight.BOLD,
                                                text_align=ft.TextAlign.RIGHT, expand=True,
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                            score_text,
                                            ft.Text(
                                                display_away_name(result), size=14,
                                                weight=ft.FontWeight.BOLD,
                                                text_align=ft.TextAlign.LEFT, expand=True,
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ],
                                    ),
                                    minute_text,
                                    progress_bar,
                                    status_text,
                                ],
                            ),
                            padding=ft.padding.symmetric(horizontal=12, vertical=14),
                            border_radius=14,
                            bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                            border=ft.border.all(1, ft.Colors.with_opacity(0.18, theme.GOLD)),
                            shadow=ft.BoxShadow(
                                spread_radius=0, blur_radius=8,
                                color=ft.Colors.with_opacity(0.08, theme.GOLD),
                            ),
                        ),

                        # Event feed
                        ft.Container(
                            content=ft.Text(f"📜 {t('match_commentary')}", size=14,
                                             weight=ft.FontWeight.W_500, color=ft.Colors.GREY_400),
                            padding=ft.padding.only(top=4),
                        ),
                        event_list,

                        # Buttons
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                            controls=[subs_btn, skip_btn, continue_btn],
                        ),
                    ],
                ),
            ),
        ],
    )

    # ── Launch the async simulation on the Flet event loop ───────────
    page.run_task(_run_simulation)

    return content


def _show_halftime_talk(page: ft.Page, event_list, halftime_choice):
    """Show halftime team talk options in the event list."""
    talks = [
        ("💪 Encourage", "Encourage", "Keep it up lads, we're doing well!"),
        ("🔥 Demand More", "Demand More", "I want more intensity! Push harder!"),
        ("🧘 Stay Calm", "Stay Calm", "Relax and stick to the plan."),
        ("😤 Criticize", "Criticize", "That first half was NOT good enough!"),
    ]

    talk_controls = []
    for emoji_label, key, desc in talks:
        def make_handler(k=key):
            def handler(e):
                halftime_choice[0] = k
                # Remove the talk buttons from event list
                for ctrl in talk_controls:
                    if ctrl in event_list.controls:
                        event_list.controls.remove(ctrl)
                page.update()
            return handler

        btn = ft.Container(
            content=ft.Column(spacing=2, controls=[
                ft.Text(emoji_label, size=14, weight=ft.FontWeight.W_600),
                ft.Text(desc, size=11, color=ft.Colors.GREY_400, italic=True),
            ]),
            padding=ft.padding.symmetric(horizontal=12, vertical=12),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.BLUE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.20, ft.Colors.BLUE_300)),
            on_click=make_handler(),
            ink=True,
        )
        talk_controls.append(btn)

    header = ft.Container(
        content=ft.Text(f"🗣️ {t('halftime_team_talk')}",
                        size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_300),
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
    )
    talk_controls.insert(0, header)

    event_list.controls.extend(talk_controls)


def _show_sub_dialog(page, outcome, event_list, events_by_minute, active_user_xi, subs_remaining, subs_made,
                      sub_pending, subs_btn, minute_text, original_user_xi=None):
    """Show a substitution selection dialog — pick a starter to take OFF, then a bench player ON."""
    from src.ui.app import app_state
    from src.core.player import calculate_overall_rating

    result = outcome.user_result
    gs = app_state.game_state
    conn = app_state.db_conn
    if not conn or not gs:
        sub_pending[0] = False
        return

    user_club_id = gs.user_club_id
    squad = queries.get_players_by_club(conn, user_club_id)
    player_map = {p.id: p for p in squad}

    # ── Roster derivation ────────────────────────────────────────────────────
    # The OFF list must mirror who is ACTUALLY on the pitch right now: the
    # user's submitted XI plus any in-match substitutions so far. Previously
    # this rebuilt tactics from scratch (auto_select_xi), which resurrected
    # pre-match-subbed-out players and hid subbed-on ones.
    current_minute = int(minute_text.value.replace("'", ""))
    active_ids = match_engine.lineup_at(result, user_club_id, original_user_xi or active_user_xi[0], current_minute)
    starters = [player_map[pid] for pid in active_ids if pid in player_map]

    # Used players cannot return from the bench. Incoming players may come off. IDs are tracked (names are not unique).
    original_ids = set(original_user_xi or [])
    # Tuple layout: (off_name, on_name, minute_str, off_id, on_id)
    off_history = {s[3] for s in subs_made if len(s) > 3}   # sent to the bench
    on_history = {s[4] for s in subs_made if len(s) > 3}    # came onto the pitch
    used_ids = (set(active_ids) | on_history | off_history | original_ids)

    match_tactics = result._replay.get("inputs", {}).get(
        "home_tactics" if result.home_club_id == user_club_id else "away_tactics")
    allowed_bench = set(match_tactics.bench if match_tactics else [])
    available_squad = [
        p for p in squad
        if p.id in allowed_bench and p.injury_days_remaining <= 0 and p.suspension_matches <= 0
    ]
    bench = sorted(
        (p for p in available_squad if p.id not in used_ids),
        key=lambda p: calculate_overall_rating(p),
        reverse=True,
    )

    if not bench:
        sub_pending[0] = False
        return

    selected_off = [None]
    selected_on = [None]

    off_label = ft.Text(f"1. {t('select_player_off')}:", size=12,
                         color=ft.Colors.RED_300, weight=ft.FontWeight.W_500)
    on_label = ft.Text(f"2. {t('select_player_on')}:", size=12,
                        color=ft.Colors.GREEN_300, weight=ft.FontWeight.W_500)

    off_list = ft.Column(spacing=2)
    on_list = ft.Column(spacing=2)
    confirm_btn = ft.ElevatedButton(
        f"✅ {t('confirm')}", disabled=True, width=200, height=40,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREEN_800, color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
        ),
    )
    summary = ft.Text("", size=11, color=ft.Colors.GREY_400)

    def _player_btn(player, is_off=True):
        ovr = calculate_overall_rating(player)
        color = ft.Colors.RED_400 if is_off else ft.Colors.GREEN_400

        def handler(e):
            if is_off:
                selected_off[0] = player
                off_label.value = f"1. OFF: {player.name} ({player.position.value} {ovr})"
            else:
                selected_on[0] = player
                on_label.value = f"2. ON: {player.name} ({player.position.value} {ovr})"
            if selected_off[0] and selected_on[0]:
                confirm_btn.disabled = False
                summary.value = (f"🔄 {selected_off[0].name} ➡️ {selected_on[0].name}")
            page.update()

        return ft.Container(
            content=ft.Row(spacing=6, controls=[
                ft.Text(player.position.value, size=10, color=theme.GOLD, width=30),
                ft.Text(player.name, size=12, expand=True, max_lines=1,
                         overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(str(ovr), size=11, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(f"{'🟢' if player.fitness >= 70 else '🟡' if player.fitness >= 40 else '🔴'}",
                         size=10),
            ]),
            padding=ft.padding.symmetric(horizontal=8, vertical=8),
            border_radius=8,
            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.12, color)),
            on_click=handler,
            ink=True,
        )

    for p in starters:
        off_list.controls.append(_player_btn(p, is_off=True))
    for p in bench:
        on_list.controls.append(_player_btn(p, is_off=False))

    def do_sub(e):
        if not selected_off[0] or not selected_on[0]:
            return
        off_p = selected_off[0]
        on_p = selected_on[0]
        current_min = int(minute_text.value.replace("'", ""))
        try:
            updated = match_engine.substitute(result, current_min, gs.user_club_id,
                                              off_p.id, on_p.id)
        except ValueError as exc:
            summary.value = str(exc)
            page.update()
            return
        for field in ("events", "home_goals", "away_goals", "home_stats", "away_stats", "player_ratings"):
            setattr(result, field, getattr(updated, field))
        result._replay = updated._replay
        subs_remaining[0] -= 1
        subs_made.append((off_p.name, on_p.name, str(current_min), off_p.id, on_p.id))
        active_user_xi[0] = match_engine.lineup_at(result, gs.user_club_id,
                                                 original_user_xi, current_min)
        events_by_minute.clear()
        for ev in result.events:
            events_by_minute.setdefault(ev.minute, []).append(ev)

        # Add substitution event to the event feed
        event_list.controls.append(ft.Container(
            content=ft.Row(spacing=6, controls=[
                ft.Text(f"{current_min}'", size=11, color=ft.Colors.GREY_500,
                         width=30, text_align=ft.TextAlign.RIGHT),
                ft.Text("🔄", size=14),
                ft.Text(f"{display_name(off_p)} ⬇️  {display_name(on_p)} ⬆️",
                         size=12, color=ft.Colors.CYAN_300, weight=ft.FontWeight.W_500,
                         expand=True),
            ]),
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=6,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN),
        ))

        subs_btn.text = f"🔄 {t('substitution')} ({subs_remaining[0]})"
        if subs_remaining[0] <= 0:
            subs_btn.visible = False

        sub_pending[0] = False
        page.pop_dialog()
        page.update()

    def cancel_sub(e):
        sub_pending[0] = False
        page.pop_dialog()
        page.update()

    confirm_btn.on_click = do_sub

    dlg = ft.AlertDialog(
        on_dismiss=lambda e: sub_pending.__setitem__(0, False),
        title=ft.Text(f"🔄 {t('substitution')} ({subs_remaining[0]})",
                       size=15, weight=ft.FontWeight.BOLD, color=theme.GOLD),
        content=ft.Container(
            content=ft.Column(
                scroll=ft.ScrollMode.AUTO, spacing=6,
                controls=[
                    off_label,
                    off_list,
                    ft.Divider(height=1),
                    on_label,
                    on_list,
                    ft.Divider(height=1),
                    summary,
                ],
            ),
            width=290, height=380,
        ),
        actions=[
            ft.TextButton(t("cancel"), on_click=cancel_sub),
            confirm_btn,
        ],
    )
    page.show_dialog(dlg)


def _apply_team_talk(conn, gs, talk_choice, result):
    """
    Apply halftime team talk effects to player morale.

    The effect depends on the talk type AND the match result:
    - "Encourage" after a win = big morale boost
    - "Criticize" after a loss = risk of morale drop or motivating
    - "Demand More" when winning = small boost
    - "Stay Calm" = safe neutral option
    """
    if not conn or not gs or not talk_choice:
        return

    from src.utils.rng import clamp

    is_home = result.home_club_id == gs.user_club_id
    user_goals = result.home_goals if is_home else result.away_goals
    opp_goals = result.away_goals if is_home else result.home_goals

    if user_goals > opp_goals:
        match_context = "winning"
    elif user_goals < opp_goals:
        match_context = "losing"
    else:
        match_context = "drawing"

    # Define morale deltas per talk × context
    effects = {
        ("Encourage", "winning"):  5,
        ("Encourage", "drawing"):  3,
        ("Encourage", "losing"):   2,
        ("Demand More", "winning"):  2,
        ("Demand More", "drawing"):  1,
        ("Demand More", "losing"):  -1,  # already losing, demanding more hurts morale
        ("Stay Calm", "winning"):  1,
        ("Stay Calm", "drawing"):  1,
        ("Stay Calm", "losing"):   0,
        ("Criticize", "winning"):  -1,  # why criticize when winning?
        ("Criticize", "drawing"):  1,   # fair criticism
        ("Criticize", "losing"):  -2,   # piling on = bad for morale
    }

    morale_delta = effects.get((talk_choice, match_context), 0)

    # Apply to all user squad players
    squad = queries.get_players_by_club(conn, gs.user_club_id)
    for p in squad:
        # Players with high composure respond better to criticism
        if talk_choice == "Criticize" and p.attributes.composure >= 14:
            adj_delta = morale_delta + 2  # tough players are motivated by it
        elif talk_choice == "Encourage" and p.age <= 21:
            adj_delta = morale_delta + 1  # young players respond well to encouragement
        else:
            adj_delta = morale_delta

        p.morale = int(clamp(p.morale + adj_delta, 0, 100))
        queries.update_player_stats(conn, p)


def _restore_page_root(page: ft.Page):
    """
    Rebuild the root page structure (transition container + notification
    overlay) that was destroyed when play_match() called
    page.controls.clear().

    This must be called before navigate() so that the transition container
    is present in the page's control tree.
    """
    from src.ui.app import app_state

    tc = app_state._transition_container
    nc = app_state._notification_column

    # If the transition container is already parented (i.e. the root Stack
    # is still in the page), there's nothing to do.
    if tc is not None and any(tc is c or _contains(c, tc) for c in page.controls):
        return

    # Rebuild the root stack from scratch, reusing the same objects so that
    # app_state references remain valid.
    if tc is None:
        tc = ft.Container(
            expand=True,
            opacity=1,
            animate_opacity=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
        )
        app_state._transition_container = tc

    if nc is None:
        nc = ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        app_state._notification_column = nc

    notification_overlay = ft.Container(
        content=nc,
        alignment=ft.Alignment(0, -1),
    )

    root = ft.Stack(
        controls=[
            tc,
            ft.TransparentPointer(
                content=notification_overlay,
                top=10,
                left=0,
                right=0,
            ),
        ],
        expand=True,
    )

    page.controls.clear()
    # Apply global SafeArea when restoring the root
    page.controls.append(ft.SafeArea(content=root, expand=True))
    page.update()


def _contains(parent, target) -> bool:
    """Recursively check whether *target* is anywhere inside *parent*."""
    if parent is target:
        return True
    children = getattr(parent, 'controls', None) or []
    if not isinstance(children, list):
        children = []
    content = getattr(parent, 'content', None)
    if content is not None:
        if content is target:
            return True
        if _contains(content, target):
            return True
    for child in children:
        if _contains(child, target):
            return True
    return False
