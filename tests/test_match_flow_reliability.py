"""Regression tests for live/post-match finalization reliability."""
from __future__ import annotations

import sqlite3
from datetime import date

from src.core.calendar import finalize_user_matchday
from src.data import queries
from src.data.database import init_schema
from src.data.models import (
    Club,
    ClubFinances,
    Fixture,
    GameState,
    LeagueStanding,
    MatchResult,
    MatchStats,
    MatchdayOutcome,
)


def _create_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def _create_club(name: str) -> Club:
    return Club(
        name=name,
        short_name=name[:3].upper(),
        city="Cairo",
        governorate="Cairo",
        finances=ClubFinances(balance=1_000_000),
    )


def _insert_baseline_state(conn: sqlite3.Connection) -> tuple[GameState, int, int, int, int]:
    home = _create_club("Home FC")
    away = _create_club("Away FC")
    home.id = queries.insert_club(conn, home)
    away.id = queries.insert_club(conn, away)

    queries.init_standings(conn, [home, away])

    fixture_1 = Fixture(
        matchday=1,
        home_club_id=home.id,
        away_club_id=away.id,
        home_club_name=home.name,
        away_club_name=away.name,
        date=date(2026, 8, 20),
    )
    fixture_2 = Fixture(
        matchday=2,
        home_club_id=home.id,
        away_club_id=away.id,
        home_club_name=home.name,
        away_club_name=away.name,
        date=date(2026, 8, 27),
    )
    fixture_1_id = queries.insert_fixture(conn, fixture_1)
    fixture_2_id = queries.insert_fixture(conn, fixture_2)

    gs = GameState(
        save_name="test",
        season_year=2026,
        current_date=date(2026, 8, 20),
        user_club_id=home.id,
        user_club_name=home.name,
    )
    queries.save_game_state(conn, gs)

    return gs, home.id, away.id, fixture_1_id, fixture_2_id


def _make_outcome(fixture_id: int, home_id: int, away_id: int) -> MatchdayOutcome:
    result = MatchResult(
        match_id=fixture_id,
        home_club_id=home_id,
        away_club_id=away_id,
        home_club_name="Home FC",
        away_club_name="Away FC",
        home_goals=1,
        away_goals=0,
        events=[],
        home_stats=MatchStats(),
        away_stats=MatchStats(),
    )
    return MatchdayOutcome(
        fixture_id=fixture_id,
        user_result=result,
        matchday=1,
    )


def test_finalize_user_matchday_is_idempotent_for_same_outcome() -> None:
    conn = _create_test_db()
    try:
        gs, home_id, away_id, fixture_1_id, _ = _insert_baseline_state(conn)
        outcome = _make_outcome(fixture_1_id, home_id, away_id)

        finalized_once = finalize_user_matchday(conn, gs, outcome)
        assert finalized_once is not None

        standings_once = {s.club_id: s for s in queries.get_standings(conn)}
        home_played_once = standings_once[home_id].played
        away_played_once = standings_once[away_id].played

        # Duplicate finalize on the exact same outcome must be a no-op.
        finalized_twice = finalize_user_matchday(conn, gs, outcome)
        assert finalized_twice is not None

        standings_twice = {s.club_id: s for s in queries.get_standings(conn)}
        assert standings_twice[home_id].played == home_played_once
        assert standings_twice[away_id].played == away_played_once

        fixture_1 = queries.get_fixture_by_id(conn, fixture_1_id)
        assert fixture_1 is not None and fixture_1.played
    finally:
        conn.close()


def test_finalize_does_not_apply_old_outcome_to_next_fixture() -> None:
    conn = _create_test_db()
    try:
        gs, home_id, away_id, fixture_1_id, fixture_2_id = _insert_baseline_state(conn)
        outcome = _make_outcome(fixture_1_id, home_id, away_id)

        # First finalize marks fixture 1 as played.
        finalized_once = finalize_user_matchday(conn, gs, outcome)
        assert finalized_once is not None

        # Second finalize call for the old outcome must NOT consume fixture 2.
        finalized_twice = finalize_user_matchday(conn, gs, outcome)
        assert finalized_twice is not None

        fixture_1 = queries.get_fixture_by_id(conn, fixture_1_id)
        fixture_2 = queries.get_fixture_by_id(conn, fixture_2_id)
        assert fixture_1 is not None and fixture_1.played
        assert fixture_2 is not None and not fixture_2.played
    finally:
        conn.close()

