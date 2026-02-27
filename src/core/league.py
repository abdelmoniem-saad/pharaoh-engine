"""
League management — fixture generation, standings, season progression.

Uses a circle method for balanced double round-robin scheduling.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

from src.data.models import (
    Club, Fixture, LeagueStanding, MatchResult, LeagueSeason,
)
from src.data import queries
from src.utils.config import LEAGUE_TEAM_COUNT, MATCHES_PER_SEASON, CompetitionType
from src.utils import rng


COMPETITION_NAME = "Egyptian Premier League"


def generate_fixtures(conn: sqlite3.Connection, clubs: list[Club],
                       season_start: date) -> list[Fixture]:
    """
    Generate a full double round-robin fixture list for the season.

    Uses the circle method: fix team 0, rotate the rest.
    First half = matchdays 1-17, second half = matchdays 18-34 (reversed H/A).
    """
    n = len(clubs)
    if n != LEAGUE_TEAM_COUNT:
        raise ValueError(f"Expected {LEAGUE_TEAM_COUNT} clubs, got {n}")

    club_ids = [c.id for c in clubs]
    club_names = {c.id: c.name for c in clubs}

    # Shuffle for random fixture order each season
    rng.shuffle(club_ids)

    fixtures: list[Fixture] = []
    matchday_date = season_start

    # First half: n-1 rounds
    rounds_first_half = _generate_round_robin(club_ids)

    for matchday_idx, round_matches in enumerate(rounds_first_half, start=1):
        for home_id, away_id in round_matches:
            fixture = Fixture(
                matchday=matchday_idx,
                home_club_id=home_id,
                away_club_id=away_id,
                home_club_name=club_names[home_id],
                away_club_name=club_names[away_id],
                date=matchday_date,
                competition=COMPETITION_NAME,
            )
            fid = queries.insert_fixture(conn, fixture)
            fixture.fixture_id = fid
            fixtures.append(fixture)
        matchday_date += timedelta(days=7)  # One matchday per week

    # Second half: reverse home/away
    for matchday_idx, round_matches in enumerate(rounds_first_half, start=n):
        for home_id, away_id in round_matches:
            fixture = Fixture(
                matchday=matchday_idx,
                home_club_id=away_id,    # Reversed
                away_club_id=home_id,    # Reversed
                home_club_name=club_names[away_id],
                away_club_name=club_names[home_id],
                date=matchday_date,
                competition=COMPETITION_NAME,
            )
            fid = queries.insert_fixture(conn, fixture)
            fixture.fixture_id = fid
            fixtures.append(fixture)
        matchday_date += timedelta(days=7)

    return fixtures


def _generate_round_robin(team_ids: list[int]) -> list[list[tuple[int, int]]]:
    """
    Generate a single round-robin schedule using the circle method.

    Returns a list of rounds, each containing (home, away) pairs.
    """
    teams = list(team_ids)
    n = len(teams)
    if n % 2 != 0:
        teams.append(-1)  # Bye
        n += 1

    rounds = []
    fixed = teams[0]
    rotating = teams[1:]

    for _ in range(n - 1):
        round_matches = []
        # Fixed team plays against first in rotating list
        if fixed != -1 and rotating[0] != -1:
            # Alternate home/away for fixed team
            if len(rounds) % 2 == 0:
                round_matches.append((fixed, rotating[0]))
            else:
                round_matches.append((rotating[0], fixed))

        # Pair remaining
        for i in range(1, len(rotating) // 2 + 1):
            home = rotating[i]
            away = rotating[-(i)]
            if home != -1 and away != -1:
                round_matches.append((home, away))

        rounds.append(round_matches)

        # Rotate: move last to front
        rotating = [rotating[-1]] + rotating[:-1]

    return rounds


def get_current_standings(conn: sqlite3.Connection) -> list[LeagueStanding]:
    """Get the current league standings sorted properly."""
    return queries.get_standings(conn)


def get_matchday_fixtures(conn: sqlite3.Connection, matchday: int) -> list[Fixture]:
    """Get all fixtures for a given matchday."""
    return queries.get_fixtures_by_matchday(conn, matchday)


def process_matchday_results(conn: sqlite3.Connection,
                              results: list[tuple[Fixture, MatchResult]]) -> None:
    """Process all results for a matchday — update fixtures and standings."""
    for fixture, result in results:
        queries.mark_fixture_played(conn, fixture.fixture_id, result)
        queries.update_standings_for_result(conn, result)
    conn.commit()


def is_season_complete(conn: sqlite3.Connection) -> bool:
    """Check if all fixtures have been played."""
    next_md = queries.get_next_unplayed_matchday(conn)
    return next_md is None


def get_champion(conn: sqlite3.Connection) -> LeagueStanding | None:
    """Get the league champion (top of standings when season is complete)."""
    if not is_season_complete(conn):
        return None
    standings = get_current_standings(conn)
    return standings[0] if standings else None


def create_league_season(conn: sqlite3.Connection, clubs: list[Club],
                          season_year: int) -> LeagueSeason:
    """Create and initialize a full league season."""
    season_start = date(season_year, 8, 15)

    # Initialize standings
    queries.init_standings(conn, clubs)

    # Generate fixtures
    fixtures = generate_fixtures(conn, clubs, season_start)

    standings = queries.get_standings(conn)

    return LeagueSeason(
        season_year=season_year,
        competition_name=COMPETITION_NAME,
        competition_type=CompetitionType.LEAGUE,
        standings=standings,
        fixtures=fixtures,
        current_matchday=1,
    )

