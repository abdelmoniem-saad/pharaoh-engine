"""Tests for fixture-scoped submitted lineup persistence."""
import sqlite3
from datetime import date

from src.data import queries
from src.data.database import init_schema
from src.data.models import Club, ClubFinances, Fixture


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
        finances=ClubFinances(balance=1000000),
    )


def test_save_and_load_submitted_lineup_for_fixture() -> None:
    conn = _create_test_db()
    try:
        home = _create_club("Home FC")
        away = _create_club("Away FC")
        home.id = queries.insert_club(conn, home)
        away.id = queries.insert_club(conn, away)

        fixture = Fixture(
            matchday=1,
            home_club_id=home.id,
            away_club_id=away.id,
            home_club_name=home.name,
            away_club_name=away.name,
            date=date(2026, 8, 20),
        )
        fixture_id = queries.insert_fixture(conn, fixture)

        queries.save_submitted_lineup(conn, fixture_id, [11, 12, 13], [21, 22])

        loaded = queries.get_user_next_fixture(conn, home.id)
        assert loaded is not None
        assert loaded.submitted_starting_xi == [11, 12, 13]
        assert loaded.submitted_bench == [21, 22]
    finally:
        conn.close()


def test_clear_submitted_lineup_for_fixture() -> None:
    conn = _create_test_db()
    try:
        home = _create_club("Home FC")
        away = _create_club("Away FC")
        home.id = queries.insert_club(conn, home)
        away.id = queries.insert_club(conn, away)

        fixture = Fixture(
            matchday=2,
            home_club_id=home.id,
            away_club_id=away.id,
            home_club_name=home.name,
            away_club_name=away.name,
            date=date(2026, 8, 27),
        )
        fixture_id = queries.insert_fixture(conn, fixture)

        queries.save_submitted_lineup(conn, fixture_id, [1, 2, 3], [4, 5])
        queries.clear_submitted_lineup(conn, fixture_id)

        loaded = queries.get_user_next_fixture(conn, home.id)
        assert loaded is not None
        assert loaded.submitted_starting_xi == []
        assert loaded.submitted_bench == []
    finally:
        conn.close()


def test_init_schema_repairs_missing_fixture_lineup_columns_with_advanced_version() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        # Simulate a drifted save: advanced schema_version but fixtures table missing submitted_* columns.
        conn.executescript("""
        CREATE TABLE fixtures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matchday INTEGER NOT NULL,
            home_club_id INTEGER NOT NULL,
            away_club_id INTEGER NOT NULL,
            home_club_name TEXT NOT NULL DEFAULT '',
            away_club_name TEXT NOT NULL DEFAULT '',
            home_club_name_ar TEXT NOT NULL DEFAULT '',
            away_club_name_ar TEXT NOT NULL DEFAULT '',
            match_date TEXT,
            played INTEGER NOT NULL DEFAULT 0,
            home_goals INTEGER DEFAULT NULL,
            away_goals INTEGER DEFAULT NULL,
            events_json TEXT NOT NULL DEFAULT '[]',
            home_stats_json TEXT NOT NULL DEFAULT '{}',
            away_stats_json TEXT NOT NULL DEFAULT '{}',
            competition TEXT NOT NULL DEFAULT 'Egyptian Premier League',
            player_ratings_json TEXT NOT NULL DEFAULT '{}',
            extra_time INTEGER NOT NULL DEFAULT 0,
            penalties_json TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE schema_version (version INTEGER PRIMARY KEY);
        INSERT INTO schema_version(version) VALUES (11);
        """)

        init_schema(conn)

        cols = [r["name"] for r in conn.execute("PRAGMA table_info(fixtures)").fetchall()]
        assert "submitted_starting_xi_json" in cols
        assert "submitted_bench_json" in cols
    finally:
        conn.close()


