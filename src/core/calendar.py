"""
Season calendar and game loop — day-by-day progression, match scheduling.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from src.data.models import (
    GameState, Club, Player, MatchResult, Fixture, InboxMessage,
)
from src.data import queries
from src.core import league, match_engine, club as club_module
from src.core.player import (
    update_form, update_fitness_after_match, rest_recovery,
)
from src.utils.config import MatchEventType


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

    # Check season completion
    if league.is_season_complete(conn):
        champion = league.get_champion(conn)
        if champion:
            msg = f"Season complete! {champion.club_name} are champions with {champion.points} points!"
            messages.append(msg)
            queries.insert_message(conn, InboxMessage(
                date=game_state.current_date,
                subject="Season Over!",
                body=msg,
                category="general",
            ))

    queries.save_game_state(conn, game_state)
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
    """Simulate all matches for a matchday."""
    messages: list[str] = []
    results: list[tuple[Fixture, MatchResult]] = []

    for fixture in fixtures:
        # Skip user's match — they handle it via the UI
        is_user_match = (
            fixture.home_club_id == game_state.user_club_id or
            fixture.away_club_id == game_state.user_club_id
        )

        if is_user_match:
            # Don't auto-simulate user matches
            continue

        # Load clubs and squads
        home_club, home_squad = club_module.get_club_with_squad(conn, fixture.home_club_id)
        away_club, away_squad = club_module.get_club_with_squad(conn, fixture.away_club_id)

        # AI prepares tactics
        home_tactics = club_module.prepare_team_for_match(home_club, home_squad)
        away_tactics = club_module.prepare_team_for_match(away_club, away_squad)

        # Simulate
        result = match_engine.simulate_match(
            home_club, away_club,
            home_squad, away_squad,
            home_tactics, away_tactics,
        )
        result.matchday = fixture.matchday
        result.date = fixture.date

        results.append((fixture, result))

        # Update player stats
        _update_player_stats_after_match(conn, result, home_squad, away_squad,
                                          home_tactics, away_tactics)

        msg = result.score_display
        messages.append(msg)

    # Update league standings
    if results:
        league.process_matchday_results(conn, results)

        # Add inbox messages
        for fixture, result in results:
            queries.insert_message(conn, InboxMessage(
                date=game_state.current_date,
                subject=f"Result: {result.score_display}",
                body=_format_result_body(result),
                category="match",
            ))

    return messages


def simulate_user_match(conn: sqlite3.Connection, game_state: GameState,
                         user_tactics: dict | None = None) -> MatchResult | None:
    """
    Simulate the user's next match.
    If user_tactics is None, auto-selects.
    """
    fixture = queries.get_user_next_fixture(conn, game_state.user_club_id)
    if fixture is None:
        return None

    # Load both clubs
    home_club, home_squad = club_module.get_club_with_squad(conn, fixture.home_club_id)
    away_club, away_squad = club_module.get_club_with_squad(conn, fixture.away_club_id)

    # Determine which is the user
    if fixture.home_club_id == game_state.user_club_id:
        user_club, user_squad = home_club, home_squad
        opp_club, opp_squad = away_club, away_squad
        user_is_home = True
    else:
        user_club, user_squad = away_club, away_squad
        opp_club, opp_squad = home_club, home_squad
        user_is_home = False

    # User tactics
    user_team_tactics = club_module.prepare_team_for_match(user_club, user_squad)
    opp_tactics = club_module.prepare_team_for_match(opp_club, opp_squad)

    # Simulate
    if user_is_home:
        result = match_engine.simulate_match(
            user_club, opp_club, user_squad, opp_squad,
            user_team_tactics, opp_tactics,
        )
    else:
        result = match_engine.simulate_match(
            opp_club, user_club, opp_squad, user_squad,
            opp_tactics, user_team_tactics,
        )

    result.matchday = fixture.matchday
    result.date = fixture.date

    # Save result
    queries.mark_fixture_played(conn, fixture.fixture_id, result)
    queries.update_standings_for_result(conn, result)

    # Update player stats
    _update_player_stats_after_match(conn, result, home_squad, away_squad,
                                      club_module.prepare_team_for_match(home_club, home_squad),
                                      club_module.prepare_team_for_match(away_club, away_squad))

    conn.commit()
    return result


def _update_player_stats_after_match(
    conn: sqlite3.Connection,
    result: MatchResult,
    home_squad: list[Player],
    away_squad: list[Player],
    home_tactics,
    away_tactics,
) -> None:
    """Update individual player statistics after a match."""
    # Build lookup
    all_players = {p.id: p for p in home_squad + away_squad}

    # Count goals and assists from events
    for event in result.events:
        if event.event_type == MatchEventType.GOAL and event.player_id:
            player = all_players.get(event.player_id)
            if player:
                player.season_stats.goals += 1
                player.season_stats.appearances += 1  # Simplified
                update_form(player, 8.0)  # Goal scorers get a form boost
                queries.update_player_stats(conn, player)

            if event.second_player_id:
                assister = all_players.get(event.second_player_id)
                if assister:
                    assister.season_stats.assists += 1
                    update_form(assister, 7.5)
                    queries.update_player_stats(conn, assister)

        elif event.event_type == MatchEventType.YELLOW_CARD and event.player_id:
            player = all_players.get(event.player_id)
            if player:
                player.season_stats.yellow_cards += 1
                queries.update_player_stats(conn, player)

    # Update appearances and fitness for all starters
    for pid in home_tactics.starting_xi + away_tactics.starting_xi:
        player = all_players.get(pid)
        if player:
            update_fitness_after_match(player, 90)


def _daily_recovery(conn: sqlite3.Connection, game_state: GameState) -> None:
    """Apply daily fitness recovery to all players."""
    clubs = queries.get_all_clubs(conn)
    for c in clubs:
        squad = queries.get_players_by_club(conn, c.id)
        for player in squad:
            rest_recovery(player, days=1)
            # Don't save every day for performance — could batch


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

