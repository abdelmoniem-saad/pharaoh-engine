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
from src.core.media import create_match_report_message, generate_random_event, generate_league_roundup
from src.core.board import update_confidence_after_match
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

    # Check if today is a match day
    next_matchday = queries.get_next_unplayed_matchday(conn)
    if next_matchday is not None:
        fixtures = queries.get_fixtures_by_matchday(conn, next_matchday)

        # Check if any fixtures are scheduled for today
        todays_fixtures = [f for f in fixtures if f.date == game_state.current_date]

        if todays_fixtures:
            messages.extend(_simulate_matchday(conn, game_state, todays_fixtures))

    # Rest recovery for all players on non-match days
    if not messages:
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
                         game_state: GameState) -> MatchdayOutcome | None:
    """
    Simulate the user's next match AND all other fixtures on the same matchday.
    Returns a MatchdayOutcome with user result + other results.
    """
    fixture = queries.get_user_next_fixture(conn, game_state.user_club_id)
    if fixture is None:
        return None

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
    opp_tactics = club_module.prepare_team_for_match(opp_club, opp_squad)

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

    # Calculate attendance
    opp_rep = opp_club.reputation if opp_club else 100
    is_home_match = fixture.home_club_id == game_state.user_club_id
    attendance = calculate_attendance(user_club, is_home_match, opp_rep)

    # Save user result
    queries.mark_fixture_played(conn, fixture.fixture_id, user_result)
    queries.update_standings_for_result(conn, user_result)

    # Track head-to-head
    queries.update_head_to_head(conn, user_result.home_club_id, user_result.away_club_id,
                                user_result.home_goals, user_result.away_goals)

    # Update player stats for user match
    _update_player_stats_after_match(conn, user_result, home_squad, away_squad,
                                      club_module.prepare_team_for_match(home_club, home_squad),
                                      club_module.prepare_team_for_match(away_club, away_squad))

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

    # Update fan happiness
    update_fan_happiness(user_club, result_type)

    # Save updated club
    queries.update_club(conn, user_club)

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
    """Apply daily fitness recovery and injury recovery to user club players."""
    squad = queries.get_players_by_club(conn, game_state.user_club_id)
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
                player.fitness = max(player.fitness, 60)  # minimum fitness on return
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
    """Weekly player development using the training system."""
    messages: list[str] = []
    club = queries.get_club(conn, game_state.user_club_id)
    if not club:
        return messages

    from src.core.training import process_weekly_training, TrainingIntensity

    squad = queries.get_players_by_club(conn, club.id)
    dev_lines = []
    for player in squad:
        if player.injury_days_remaining > 0:
            continue
        dev_msgs = process_weekly_training(player, club, TrainingIntensity.NORMAL)
        if dev_msgs:
            dev_lines.extend(dev_msgs)
            messages.extend(dev_msgs)
            queries.update_player_stats(conn, player)

        # Check milestones
        milestone_msgs = queries.check_player_milestones(conn, player, game_state.current_date)
        for m in milestone_msgs:
            queries.insert_message(conn, m)

    # Send a consolidated training report if anything changed
    if dev_lines:
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject="📈 Weekly Training Report",
            body="\n".join(dev_lines),
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

