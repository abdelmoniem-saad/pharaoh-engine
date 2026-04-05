"""
Season calendar and game loop — day-by-day progression, match scheduling.
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

from src.data.models import (
    GameState, Player, MatchResult, Fixture, InboxMessage,
    MatchdayOutcome,
)
from src.data import queries
from src.core import league, match_engine, club as club_module
from src.core.player import (
    update_form, update_fitness_after_match, rest_recovery,
    update_morale,
)
from src.core.media import (
    create_match_report_message,
    generate_random_event,
    generate_league_roundup,
    create_weekly_board_brief_message,
)
from src.core.board import (
    update_confidence_after_match,
    get_confidence_level,
    evaluate_objective_progress,
)
from src.core.fans import update_fan_happiness, calculate_attendance
from src.core.youth import develop_player
from src.core.finance import process_monthly_finances
from src.core.transfers import generate_ai_bids, check_expiring_contracts, process_pending_negotiations, process_loan_returns
from src.utils.config import MatchEventType, INJURY_TYPES
from src.utils import rng


def advance_day(conn: sqlite3.Connection, game_state: GameState) -> list[str]:
    """
    Advance the game by one day.

    Returns a list of summary messages about what happened.
    """
    messages: list[str] = []
    game_state.current_date += timedelta(days=1)
    game_state.day_count += 1

    # Check if today is a match day (league)
    is_match_day = False
    next_matchday = queries.get_next_unplayed_matchday(conn)
    if next_matchday is not None:
        fixtures = queries.get_fixtures_by_matchday(conn, next_matchday)

        # Check if any fixtures are scheduled for today
        todays_fixtures = [f for f in fixtures if f.date == game_state.current_date]

        if todays_fixtures:
            is_match_day = True
            messages.extend(_simulate_matchday(conn, game_state, todays_fixtures))

    # ── Cup match simulation ─────────────────────────────────────────
    try:
        from src.core.competition import (
            get_cup_state, simulate_cup_match_result,
            advance_cup_round, CUP_NAME, is_cup_match,
        )
        cup = get_cup_state(conn, game_state.season_year)
        if cup and not cup.is_complete:
            # Find today's cup fixtures (non-user matches only)
            cup_rows = conn.execute(
                """SELECT id FROM fixtures
                   WHERE competition=? AND played=0 AND match_date=?
                   AND home_club_id != ? AND away_club_id != ?""",
                (CUP_NAME, game_state.current_date.isoformat(),
                 game_state.user_club_id, game_state.user_club_id),
            ).fetchall()
            for row in cup_rows:
                simulate_cup_match_result(conn, row["id"], cup)

            # Try advancing the round
            cup_msgs = advance_cup_round(conn, cup, game_state)
            messages.extend(cup_msgs)
    except Exception:
        pass  # Cup not available yet

    # ── Ramadan notification (once per Ramadan period) ────────────────
    from src.utils.config import is_ramadan
    if is_ramadan(game_state.current_date) and game_state.day_count % 30 == 1:
        from src.utils.localization import t
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject="🌙 Ramadan Mubarak",
            body=t("ramadan_notice") + "\n\n" + t("ramadan_schedule"),
            category="general",
        ))
        messages.append("Ramadan period — fitness and training affected.")

    # Daily fitness recovery and injury healing for ALL clubs (every day)
    _daily_recovery(conn, game_state)

    # Process pending transfer negotiations (responses arrive)
    messages.extend(process_pending_negotiations(conn, game_state))

    # Process loan returns
    messages.extend(process_loan_returns(conn, game_state))

    # AI transfer offers for listed players (daily)
    messages.extend(generate_ai_bids(conn, game_state))

    # Weekly player development (every 7 days)
    if game_state.day_count % 7 == 0:
        messages.extend(_weekly_development(conn, game_state))
        messages.extend(_weekly_board_brief(conn, game_state))

    # Monthly finances + contract checks (every 30 days)
    if game_state.day_count % 30 == 0:
        messages.extend(_monthly_finances(conn, game_state))
        messages.extend(check_expiring_contracts(conn, game_state))

    # Random mid-season events (varied inbox messages)
    squad = queries.get_players_by_club(conn, game_state.user_club_id)
    if squad:
        random_player = rng.choice(squad)
        event_msg = generate_random_event(
            game_state.user_club_name, random_player.name,
            game_state.current_date,
        )
        if event_msg:
            queries.insert_message(conn, event_msg)

    # Interactive random events (stored on app_state for UI to display)
    from src.core.events import generate_daily_event
    daily_event = generate_daily_event(conn, game_state)
    if daily_event:
        try:
            from src.ui.app import app_state
            app_state.pending_event = daily_event
        except Exception:
            pass

    # Check season completion
    if league.is_season_complete(conn):
        champion = league.get_champion(conn)
        if champion:
            msg = f"Season complete! {champion.club_name} are champions with {champion.points} points!"
            messages.append(msg)
            queries.insert_message(conn, InboxMessage(
                date=game_state.current_date,
                subject="🏆 Season Over!",
                body=msg,
                category="general",
            ))

    queries.save_game_state(conn, game_state)

    # Autosave check
    try:
        row = conn.execute("SELECT auto_save, auto_save_interval FROM game_settings WHERE id = 1").fetchone()
        if row and row["auto_save"] and game_state.day_count % row["auto_save_interval"] == 0:
            queries.save_game_state(conn, game_state)
    except Exception:
        pass

    return messages


def advance_to_next_match(conn: sqlite3.Connection,
                           game_state: GameState) -> list[str]:
    """
    Fast-forward to the next match day for the user's club.
    Simulates all intermediate days.
    """
    all_messages: list[str] = []
    max_days = 60  # Safety limit

    for _ in range(max_days):
        # Check if user has a match today
        user_fixture = queries.get_user_next_fixture(conn, game_state.user_club_id)
        if user_fixture and user_fixture.date == game_state.current_date:
            break

        day_messages = advance_day(conn, game_state)
        all_messages.extend(day_messages)

        if league.is_season_complete(conn):
            break

    return all_messages


def _simulate_matchday(conn: sqlite3.Connection, game_state: GameState,
                        fixtures: list[Fixture]) -> list[str]:
    """Simulate all matches for a matchday (excludes user match — handled via UI)."""
    messages: list[str] = []
    results: list[tuple[Fixture, MatchResult]] = []

    for fixture in fixtures:
        # Skip user's match — they handle it via the UI
        is_user_match = (
            fixture.home_club_id == game_state.user_club_id or
            fixture.away_club_id == game_state.user_club_id
        )

        if is_user_match:
            continue

        result = _simulate_single_fixture(conn, fixture)
        results.append((fixture, result))
        msg = result.score_display
        messages.append(msg)

    # Update league standings
    if results:
        league.process_matchday_results(conn, results)


    return messages


def _simulate_single_fixture(conn: sqlite3.Connection,
                               fixture: Fixture) -> MatchResult:
    """Simulate a single fixture and update player stats."""
    home_club, home_squad = club_module.get_club_with_squad(conn, fixture.home_club_id)
    away_club, away_squad = club_module.get_club_with_squad(conn, fixture.away_club_id)

    home_tactics = club_module.prepare_team_for_match(home_club, home_squad)
    away_tactics = club_module.prepare_team_for_match(away_club, away_squad)

    result = match_engine.simulate_match(
        home_club, away_club,
        home_squad, away_squad,
        home_tactics, away_tactics,
    )
    result.matchday = fixture.matchday
    result.date = fixture.date

    # Update player stats
    _update_player_stats_after_match(conn, result, home_squad, away_squad,
                                      home_tactics, away_tactics)
    return result


def simulate_user_match(conn: sqlite3.Connection,
                         game_state: GameState,
                         user_starting_xi: list[int] | None = None,
                         user_bench: list[int] | None = None,
                         commit: bool = True) -> MatchdayOutcome | None:
    """
    Simulate the user's next match AND all other fixtures on the same matchday.
    Returns a MatchdayOutcome with user result + other results.
    """
    fixture = queries.get_user_next_fixture(conn, game_state.user_club_id)
    if fixture is None:
        return None

    # Prefer explicit call-time overrides; otherwise use fixture-persisted pre-match submission.
    if user_starting_xi is None and getattr(fixture, "submitted_starting_xi", None):
        user_starting_xi = list(fixture.submitted_starting_xi)
    if user_bench is None and getattr(fixture, "submitted_bench", None):
        user_bench = list(fixture.submitted_bench)

    # ── 1. Simulate user's match ─────────────────────────────────────────
    home_club, home_squad = club_module.get_club_with_squad(conn, fixture.home_club_id)
    away_club, away_squad = club_module.get_club_with_squad(conn, fixture.away_club_id)

    if fixture.home_club_id == game_state.user_club_id:
        user_club, user_squad = home_club, home_squad
        opp_club, opp_squad = away_club, away_squad
        user_is_home = True
    else:
        user_club, user_squad = away_club, away_squad
        opp_club, opp_squad = home_club, home_squad
        user_is_home = False

    user_team_tactics = club_module.prepare_team_for_match(user_club, user_squad)

    # If the user submitted a custom XI/bench from pre-match, honor it for this fixture.
    if user_starting_xi is not None:
        available_ids = {
            p.id for p in user_squad
            if p.injury_days_remaining <= 0 and p.suspension_matches <= 0
        }
        defaults_xi = list(user_team_tactics.starting_xi)
        defaults_bench = [pid for pid in user_team_tactics.bench if pid in available_ids]

        # Keep order, drop duplicates/invalid/unavailable IDs.
        seen: set[int] = set()
        cleaned_xi: list[int] = []
        for pid in user_starting_xi:
            if pid in seen or pid not in available_ids:
                continue
            cleaned_xi.append(pid)
            seen.add(pid)
            if len(cleaned_xi) >= 11:
                break

        # Backfill missing XI slots from defaults.
        for pid in defaults_xi:
            if len(cleaned_xi) >= 11:
                break
            if pid in seen or pid not in available_ids:
                continue
            cleaned_xi.append(pid)
            seen.add(pid)

        # Build bench from submitted bench first (if provided), then default bench.
        cleaned_bench: list[int] = []
        bench_source = user_bench if user_bench is not None else []
        for pid in bench_source:
            if pid in seen or pid not in available_ids:
                continue
            cleaned_bench.append(pid)
            seen.add(pid)
            if len(cleaned_bench) >= 7:
                break
        for pid in defaults_bench:
            if len(cleaned_bench) >= 7:
                break
            if pid in seen or pid not in available_ids:
                continue
            cleaned_bench.append(pid)
            seen.add(pid)

        user_team_tactics.starting_xi = cleaned_xi
        user_team_tactics.bench = cleaned_bench

    opp_tactics = club_module.prepare_team_for_match(opp_club, opp_squad)

    # Keep explicit references so downstream stats use the exact match tactics.
    if user_is_home:
        home_tactics_used = user_team_tactics
        away_tactics_used = opp_tactics
    else:
        home_tactics_used = opp_tactics
        away_tactics_used = user_team_tactics

    if user_is_home:
        user_result = match_engine.simulate_match(
            user_club, opp_club, user_squad, opp_squad,
            user_team_tactics, opp_tactics,
        )
    else:
        user_result = match_engine.simulate_match(
            opp_club, user_club, opp_squad, user_squad,
            opp_tactics, user_team_tactics,
        )

    user_result.matchday = fixture.matchday
    user_result.date = fixture.date

    # Snapshot league position BEFORE this result
    standings_before = queries.get_standings(conn)
    position_before = 0
    for i, s in enumerate(standings_before, 1):
        if s.club_id == game_state.user_club_id:
            position_before = i
            break

    # In live mode we defer persistence until the user finishes the live screen.
    if not commit:
        return MatchdayOutcome(
            user_result=user_result,
            other_results=[],
            matchday=fixture.matchday,
            position_before=position_before,
            position_after=position_before,
            attendance=0,
            newly_unlocked=[],
            home_starting_xi=list(home_tactics_used.starting_xi),
            away_starting_xi=list(away_tactics_used.starting_xi),
        )

    # Calculate attendance and generate real matchday income
    opp_rep = opp_club.reputation if opp_club else 100
    is_home_match = fixture.home_club_id == game_state.user_club_id
    opp_id = opp_club.id if opp_club else 0
    attendance = calculate_attendance(user_club, is_home_match, opp_rep,
                                      opponent_club_id=opp_id, conn=conn)

    # Ticket revenue: only for home matches (average ticket ~50 EGP)
    if is_home_match and attendance > 0:
        ticket_price = 50  # EGP per ticket (base)
        # Bigger matches charge more
        if opp_rep >= 170:
            ticket_price = 80
        elif opp_rep >= 140:
            ticket_price = 65
        ticket_revenue = attendance * ticket_price
        user_club.finances.balance += ticket_revenue
        # Update the dynamic matchday_income for future monthly calculations
        user_club.finances.matchday_income = ticket_revenue
        queries.update_club(conn, user_club)

    # Save user result
    queries.mark_fixture_played(conn, fixture.fixture_id, user_result)
    queries.clear_submitted_lineup(conn, fixture.fixture_id)
    queries.update_standings_for_result(conn, user_result)

    # Track head-to-head
    queries.update_head_to_head(conn, user_result.home_club_id, user_result.away_club_id,
                                user_result.home_goals, user_result.away_goals)

    # Update player stats for user match
    _update_player_stats_after_match(
        conn,
        user_result,
        home_squad,
        away_squad,
        home_tactics_used,
        away_tactics_used,
    )

    # Track youth promoted count (U21 players with ≥5 appearances)
    user_club_refreshed = queries.get_club(conn, game_state.user_club_id)
    if user_club_refreshed:
        user_squad_refreshed = queries.get_players_by_club(conn, game_state.user_club_id)
        youth_count = sum(1 for p in user_squad_refreshed
                          if p.age <= 21 and p.season_stats.appearances >= 5)
        user_club_refreshed.youth_promoted_count = youth_count
        queries.update_club(conn, user_club_refreshed)
        # Re-read the user_club for rest of function
        user_club = user_club_refreshed

    # ── 2. Determine result type for board/fans/media ────────────────────
    if user_is_home:
        user_goals = user_result.home_goals
        opp_goals = user_result.away_goals
    else:
        user_goals = user_result.away_goals
        opp_goals = user_result.home_goals

    if user_goals > opp_goals:
        result_type = "win"
    elif user_goals < opp_goals:
        result_type = "loss"
    else:
        result_type = "draw"

    # Update board confidence
    update_confidence_after_match(user_club, result_type)

    # Update fan happiness (with derby amplification)
    opponent_id = away_club.id if user_is_home else home_club.id
    update_fan_happiness(user_club, result_type,
                         opponent_club_id=opponent_id, conn=conn)

    # Save updated club
    queries.update_club(conn, user_club)

    # ── Career stats & achievements ──────────────────────────────────
    from src.core.achievements import update_career_after_match, seed_achievements
    seed_achievements(conn)  # Ensure tables exist for old saves
    newly_unlocked = update_career_after_match(
        conn, result_type, user_goals, opp_goals,
        user_club.board_confidence, user_club.fan_happiness,
        game_state.current_date,
    )
    # Store on the outcome so post-match screen can show toasts
    # (we'll attach to the MatchdayOutcome later via app_state)

    # Decrement suspensions for user squad after matchday
    full_squad = queries.get_players_by_club(conn, game_state.user_club_id)
    for p in full_squad:
        if p.suspension_matches > 0:
            p.suspension_matches -= 1
            queries.update_player_stats(conn, p)
            if p.suspension_matches == 0:
                queries.insert_message(conn, InboxMessage(
                    date=game_state.current_date,
                    subject=f"🔓 {p.name} Available",
                    body=f"{p.name} has served their suspension and is available for selection.",
                    category="general",
                ))

    # Generate media headline
    media_msg = create_match_report_message(
        user_result, game_state.user_club_id, game_state.current_date
    )
    queries.insert_message(conn, media_msg)

    # ── 3. Simulate ALL OTHER fixtures on the same matchday ──────────────
    all_md_fixtures = queries.get_fixtures_by_matchday(conn, fixture.matchday)
    other_results: list[MatchResult] = []

    for other_fixture in all_md_fixtures:
        if other_fixture.played:
            continue
        # Skip user match (already done)
        if other_fixture.fixture_id == fixture.fixture_id:
            continue

        result = _simulate_single_fixture(conn, other_fixture)
        queries.mark_fixture_played(conn, other_fixture.fixture_id, result)
        queries.update_standings_for_result(conn, result)
        # Track head-to-head for other matches too
        queries.update_head_to_head(conn, result.home_club_id, result.away_club_id,
                                    result.home_goals, result.away_goals)
        other_results.append(result)


    conn.commit()

    # Snapshot league position AFTER all results
    standings_after = queries.get_standings(conn)
    position_after = 0
    for i, s in enumerate(standings_after, 1):
        if s.club_id == game_state.user_club_id:
            position_after = i
            break

    # Generate league roundup for the matchday
    all_results_for_roundup = [user_result] + other_results
    roundup_msg = generate_league_roundup(
        fixture.matchday, all_results_for_roundup,
        standings_after, game_state.current_date,
    )
    queries.insert_message(conn, roundup_msg)

    return MatchdayOutcome(
        user_result=user_result,
        other_results=other_results,
        matchday=fixture.matchday,
        position_before=position_before,
        position_after=position_after,
        attendance=attendance,
        newly_unlocked=newly_unlocked,
        home_starting_xi=list(home_tactics_used.starting_xi),
        away_starting_xi=list(away_tactics_used.starting_xi),
    )


def finalize_user_matchday(conn: sqlite3.Connection,
                           game_state: GameState,
                           outcome: MatchdayOutcome) -> MatchdayOutcome | None:
    """Persist a live-played user matchday result and process remaining fixtures."""
    fixture = queries.get_user_next_fixture(conn, game_state.user_club_id)
    if fixture is None:
        return None

    user_result = outcome.user_result
    user_result.matchday = fixture.matchday
    user_result.date = fixture.date

    home_club, home_squad = club_module.get_club_with_squad(conn, fixture.home_club_id)
    away_club, away_squad = club_module.get_club_with_squad(conn, fixture.away_club_id)
    user_is_home = fixture.home_club_id == game_state.user_club_id
    user_club = home_club if user_is_home else away_club
    opp_club = away_club if user_is_home else home_club

    # Snapshot position before applying any matchday updates.
    standings_before = queries.get_standings(conn)
    position_before = 0
    for i, s in enumerate(standings_before, 1):
        if s.club_id == game_state.user_club_id:
            position_before = i
            break

    # Attendance and matchday income.
    opp_rep = opp_club.reputation if opp_club else 100
    is_home_match = fixture.home_club_id == game_state.user_club_id
    opp_id = opp_club.id if opp_club else 0
    attendance = calculate_attendance(user_club, is_home_match, opp_rep,
                                      opponent_club_id=opp_id, conn=conn)
    if is_home_match and attendance > 0:
        ticket_price = 50
        if opp_rep >= 170:
            ticket_price = 80
        elif opp_rep >= 140:
            ticket_price = 65
        ticket_revenue = attendance * ticket_price
        user_club.finances.balance += ticket_revenue
        user_club.finances.matchday_income = ticket_revenue
        queries.update_club(conn, user_club)

    # Persist user result and standings.
    queries.mark_fixture_played(conn, fixture.fixture_id, user_result)
    queries.clear_submitted_lineup(conn, fixture.fixture_id)
    queries.update_standings_for_result(conn, user_result)
    queries.update_head_to_head(conn, user_result.home_club_id, user_result.away_club_id,
                                user_result.home_goals, user_result.away_goals)

    # Rebuild tactics for stat processing and force the exact starting XI used.
    home_tactics_used = club_module.prepare_team_for_match(home_club, home_squad)
    away_tactics_used = club_module.prepare_team_for_match(away_club, away_squad)
    if outcome.home_starting_xi:
        home_tactics_used.starting_xi = list(outcome.home_starting_xi)
    if outcome.away_starting_xi:
        away_tactics_used.starting_xi = list(outcome.away_starting_xi)

    _update_player_stats_after_match(
        conn,
        user_result,
        home_squad,
        away_squad,
        home_tactics_used,
        away_tactics_used,
    )

    # Apply in-match substitution minute corrections captured in live events.
    subs = [e for e in user_result.events if e.event_type == MatchEventType.SUBSTITUTION]
    if subs:
        for ev in subs:
            current_min = max(1, min(90, ev.minute))
            if ev.player_id:
                off_p = queries.get_player(conn, ev.player_id)
                if off_p:
                    mins_not_played = max(0, 90 - current_min)
                    off_p.season_stats.minutes_played = max(0, off_p.season_stats.minutes_played - mins_not_played)
                    off_p.fitness = min(100, off_p.fitness + 3)
                    queries.update_player_stats(conn, off_p)
            if ev.second_player_id:
                on_p = queries.get_player(conn, ev.second_player_id)
                if on_p:
                    mins_played = max(0, 90 - current_min)
                    on_p.season_stats.minutes_played += mins_played
                    on_p.season_stats.appearances += 1
                    on_p.morale = min(100, on_p.morale + 3)
                    on_p.matches_benched_streak = 0
                    on_p.fitness = max(0, on_p.fitness - (mins_played // 10))
                    queries.update_player_stats(conn, on_p)

    # Track youth promoted count.
    user_club_refreshed = queries.get_club(conn, game_state.user_club_id)
    if user_club_refreshed:
        user_squad_refreshed = queries.get_players_by_club(conn, game_state.user_club_id)
        youth_count = sum(1 for p in user_squad_refreshed
                          if p.age <= 21 and p.season_stats.appearances >= 5)
        user_club_refreshed.youth_promoted_count = youth_count
        queries.update_club(conn, user_club_refreshed)
        user_club = user_club_refreshed

    if user_is_home:
        user_goals = user_result.home_goals
        opp_goals = user_result.away_goals
    else:
        user_goals = user_result.away_goals
        opp_goals = user_result.home_goals

    if user_goals > opp_goals:
        result_type = "win"
    elif user_goals < opp_goals:
        result_type = "loss"
    else:
        result_type = "draw"

    update_confidence_after_match(user_club, result_type)
    opponent_id = away_club.id if user_is_home else home_club.id
    update_fan_happiness(user_club, result_type,
                         opponent_club_id=opponent_id, conn=conn)
    queries.update_club(conn, user_club)

    from src.core.achievements import update_career_after_match, seed_achievements
    seed_achievements(conn)
    newly_unlocked = update_career_after_match(
        conn, result_type, user_goals, opp_goals,
        user_club.board_confidence, user_club.fan_happiness,
        game_state.current_date,
    )

    full_squad = queries.get_players_by_club(conn, game_state.user_club_id)
    for p in full_squad:
        if p.suspension_matches > 0:
            p.suspension_matches -= 1
            queries.update_player_stats(conn, p)
            if p.suspension_matches == 0:
                queries.insert_message(conn, InboxMessage(
                    date=game_state.current_date,
                    subject=f"🔓 {p.name} Available",
                    body=f"{p.name} has served their suspension and is available for selection.",
                    category="general",
                ))

    media_msg = create_match_report_message(
        user_result, game_state.user_club_id, game_state.current_date
    )
    queries.insert_message(conn, media_msg)

    all_md_fixtures = queries.get_fixtures_by_matchday(conn, fixture.matchday)
    other_results: list[MatchResult] = []
    for other_fixture in all_md_fixtures:
        if other_fixture.played:
            continue
        if other_fixture.fixture_id == fixture.fixture_id:
            continue

        result = _simulate_single_fixture(conn, other_fixture)
        queries.mark_fixture_played(conn, other_fixture.fixture_id, result)
        queries.update_standings_for_result(conn, result)
        queries.update_head_to_head(conn, result.home_club_id, result.away_club_id,
                                    result.home_goals, result.away_goals)
        other_results.append(result)

    conn.commit()

    standings_after = queries.get_standings(conn)
    position_after = 0
    for i, s in enumerate(standings_after, 1):
        if s.club_id == game_state.user_club_id:
            position_after = i
            break

    all_results_for_roundup = [user_result] + other_results
    roundup_msg = generate_league_roundup(
        fixture.matchday, all_results_for_roundup,
        standings_after, game_state.current_date,
    )
    queries.insert_message(conn, roundup_msg)

    return MatchdayOutcome(
        user_result=user_result,
        other_results=other_results,
        matchday=fixture.matchday,
        position_before=position_before,
        position_after=position_after,
        attendance=attendance,
        newly_unlocked=newly_unlocked,
        home_starting_xi=list(home_tactics_used.starting_xi),
        away_starting_xi=list(away_tactics_used.starting_xi),
    )


def _update_player_stats_after_match(
    conn: sqlite3.Connection,
    result: MatchResult,
    home_squad: list[Player],
    away_squad: list[Player],
    home_tactics,
    away_tactics,
) -> None:
    """Update individual player statistics after a match."""
    all_players = {p.id: p for p in home_squad + away_squad}

    # Determine result type for each side
    if result.home_goals > result.away_goals:
        home_result, away_result = "win", "loss"
    elif result.home_goals < result.away_goals:
        home_result, away_result = "loss", "win"
    else:
        home_result = away_result = "draw"

    # Count goals/assists from events (for stats deduplication)
    goal_players: set[int] = set()
    assist_players: set[int] = set()
    yellow_players: set[int] = set()

    for event in result.events:
        if event.event_type == MatchEventType.GOAL and event.player_id:
            player = all_players.get(event.player_id)
            if player and event.player_id not in goal_players:
                player.season_stats.goals += 1
                goal_players.add(event.player_id)
            elif player:
                player.season_stats.goals += 1  # multiple goals

            if event.second_player_id:
                assister = all_players.get(event.second_player_id)
                if assister:
                    assister.season_stats.assists += 1

        elif event.event_type == MatchEventType.YELLOW_CARD and event.player_id:
            player = all_players.get(event.player_id)
            if player:
                player.season_stats.yellow_cards += 1
                yellow_players.add(event.player_id)

    # Process all starters — appearances, form, fitness, morale, rating
    home_starters = set(home_tactics.starting_xi)
    away_starters = set(away_tactics.starting_xi)

    # Clean sheet check
    home_clean = result.away_goals == 0
    away_clean = result.home_goals == 0

    for pid in home_starters:
        player = all_players.get(pid)
        if not player:
            continue
        player.season_stats.appearances += 1
        player.season_stats.minutes_played += 90
        rating = result.player_ratings.get(pid, 6.5)
        player.season_stats.average_rating = round(
            (player.season_stats.average_rating * (player.season_stats.appearances - 1) + rating)
            / player.season_stats.appearances, 1
        )
        if home_clean and player.position.value in ("GK", "CB", "LB", "RB"):
            player.season_stats.clean_sheets += 1
        if rating >= 8.5:
            player.season_stats.man_of_the_match += 1
        update_form(player, rating)
        update_fitness_after_match(player, 90)
        update_morale(player, home_result, rating, played=True)
        queries.update_player_stats(conn, player)

    for pid in away_starters:
        player = all_players.get(pid)
        if not player:
            continue
        player.season_stats.appearances += 1
        player.season_stats.minutes_played += 90
        rating = result.player_ratings.get(pid, 6.5)
        player.season_stats.average_rating = round(
            (player.season_stats.average_rating * (player.season_stats.appearances - 1) + rating)
            / player.season_stats.appearances, 1
        )
        if away_clean and player.position.value in ("GK", "CB", "LB", "RB"):
            player.season_stats.clean_sheets += 1
        if rating >= 8.5:
            player.season_stats.man_of_the_match += 1
        update_form(player, rating)
        update_fitness_after_match(player, 90)
        update_morale(player, away_result, rating, played=True)
        queries.update_player_stats(conn, player)

    # Non-starters morale drop (bench + unused)
    for player in home_squad:
        if player.id not in home_starters:
            # Check if player was a starter last game (was_dropped)
            was_dropped = player.season_stats.appearances > 0 and player.matches_benched_streak == 0
            update_morale(player, home_result, played=False, was_dropped=was_dropped)
            queries.update_player_stats(conn, player)
    for player in away_squad:
        if player.id not in away_starters:
            was_dropped = player.season_stats.appearances > 0 and player.matches_benched_streak == 0
            update_morale(player, away_result, played=False, was_dropped=was_dropped)
            queries.update_player_stats(conn, player)

    # ── Process injuries from match events ──────────────────────────────
    for event in result.events:
        if event.event_type == MatchEventType.INJURY and event.player_id:
            player = all_players.get(event.player_id)
            if player:
                inj_days = rng.randint(7, 42)
                inj_type = ""
                # Extract injury type from description
                for it in INJURY_TYPES:
                    if it.lower() in event.description.lower():
                        inj_type = it
                        break
                player.injury_days_remaining = inj_days
                player.injury_type = inj_type or "Unknown"
                player.fitness = max(0, player.fitness - 30)
                queries.update_player_stats(conn, player)

    # ── Suspension: 5 yellows = 1 match ban, red = 1-3 match ban ────────
    for event in result.events:
        if event.event_type == MatchEventType.YELLOW_CARD and event.player_id:
            player = all_players.get(event.player_id)
            if player and player.season_stats.yellow_cards > 0 and player.season_stats.yellow_cards % 5 == 0:
                player.suspension_matches = 1
                queries.update_player_stats(conn, player)
        elif event.event_type == MatchEventType.RED_CARD and event.player_id:
            player = all_players.get(event.player_id)
            if player:
                player.season_stats.red_cards += 1
                player.suspension_matches = rng.randint(1, 3)
                queries.update_player_stats(conn, player)


def _daily_recovery(conn: sqlite3.Connection, game_state: GameState) -> None:
    """Apply daily fitness recovery and injury recovery to ALL players (all clubs).
    Previously only user club players recovered, causing AI teams to degrade."""
    # Get all players across all clubs
    all_clubs = queries.get_all_clubs(conn)
    for club in all_clubs:
        squad = queries.get_players_by_club(conn, club.id)
        for player in squad:
            changed = False
            old_fitness = player.fitness
            rest_recovery(player, days=1)
            if player.fitness != old_fitness:
                changed = True

            # Injury recovery countdown
            if player.injury_days_remaining > 0:
                player.injury_days_remaining -= 1
                changed = True
                if player.injury_days_remaining == 0:
                    player.injury_type = ""
                    player.fitness = max(player.fitness, 60)
                    # Only notify user about their own players
                    if club.id == game_state.user_club_id:
                        queries.insert_message(conn, InboxMessage(
                            date=game_state.current_date,
                            subject=f"🏥 {player.name} Recovered!",
                            body=f"{player.name} has recovered from injury and is available for selection.",
                            category="general",
                        ))

            if changed:
                queries.update_player_stats(conn, player)


def _weekly_development(conn: sqlite3.Connection,
                         game_state: GameState) -> list[str]:
    """Weekly player development using the training system.
    Applies to ALL clubs — AI clubs train at Normal intensity with position-based focus."""
    messages: list[str] = []

    from src.core.training import process_weekly_training, TrainingIntensity, get_recommended_focus

    all_clubs = queries.get_all_clubs(conn)
    user_dev_lines = []

    for club in all_clubs:
        squad = queries.get_players_by_club(conn, club.id)
        is_user = club.id == game_state.user_club_id

        for player in squad:
            if player.injury_days_remaining > 0:
                continue

            # AI players get auto-assigned training focus if they don't have one
            if not is_user and not player.training_focus:
                player.training_focus = get_recommended_focus(player)

            dev_msgs = process_weekly_training(player, club, TrainingIntensity.NORMAL)
            if dev_msgs:
                if is_user:
                    user_dev_lines.extend(dev_msgs)
                    messages.extend(dev_msgs)
                queries.update_player_stats(conn, player)

            # Check milestones (user only to avoid inbox spam)
            if is_user:
                milestone_msgs = queries.check_player_milestones(conn, player, game_state.current_date)
                for m in milestone_msgs:
                    queries.insert_message(conn, m)

    # Send a consolidated training report if anything changed (user only)
    if user_dev_lines:
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject="📈 Weekly Training Report",
            body="\n".join(user_dev_lines),
            category="general",
        ))
    return messages


def _monthly_finances(conn: sqlite3.Connection,
                       game_state: GameState) -> list[str]:
    """Process monthly finances for user club."""
    messages: list[str] = []
    club = queries.get_club(conn, game_state.user_club_id)
    if not club:
        return messages
    summary = process_monthly_finances(club)
    queries.update_club(conn, club)
    messages.append(summary)
    queries.insert_message(conn, InboxMessage(
        date=game_state.current_date,
        subject="💰 Monthly Financial Report",
        body=summary,
        category="board",
    ))
    return messages


def _weekly_board_brief(conn: sqlite3.Connection,
                        game_state: GameState) -> list[str]:
    """Generate a weekly board progress brief from current trajectory."""
    messages: list[str] = []
    user_club = queries.get_club(conn, game_state.user_club_id)
    if not user_club:
        return messages

    standings = queries.get_standings(conn)
    if not standings:
        return messages

    row = next((s for s in standings if s.club_id == game_state.user_club_id), None)
    if row is None:
        return messages

    total_teams = len(standings)
    position = next((i for i, s in enumerate(standings, 1)
                    if s.club_id == game_state.user_club_id), total_teams)
    total_matches = max(1, (total_teams - 1) * 2)
    season_progress = row.played / total_matches

    objective_progress = evaluate_objective_progress(
        user_club,
        position=position,
        total_teams=total_teams,
        goals_for=row.goals_for,
        goal_difference=row.goal_difference,
        season_progress=season_progress,
    )

    brief = create_weekly_board_brief_message(
        club_name=user_club.name,
        board_confidence=user_club.board_confidence,
        confidence_level=get_confidence_level(user_club.board_confidence).value,
        season_expectation=user_club.season_expectation,
        position=position,
        total_teams=total_teams,
        progress=objective_progress,
        current_date=game_state.current_date,
    )
    queries.insert_message(conn, brief)
    messages.append(
        f"Board weekly brief: {position}/{total_teams} ({user_club.board_confidence} confidence)"
    )
    return messages


def _format_result_body(result: MatchResult) -> str:
    """Format a match result into a readable message body."""
    lines = [result.score_display, ""]
    goals = [e for e in result.events if e.event_type == MatchEventType.GOAL]
    for g in goals:
        line = f"  {g.minute}' {g.player_name}"
        if g.second_player_name:
            line += f" (assist: {g.second_player_name})"
        lines.append(line)

    lines.append("")
    lines.append(f"Possession: {result.home_stats.possession:.0f}% - {result.away_stats.possession:.0f}%")
    lines.append(f"Shots: {result.home_stats.shots} - {result.away_stats.shots}")
    return "\n".join(lines)

