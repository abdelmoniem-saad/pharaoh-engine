"""Database connection lifecycle tests (save-slot switching and schema repair)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from src.data import database


def _set_test_db_dir(tmp_path: Path) -> None:
    database.close()
    database._DEFAULT_DB_DIR = tmp_path  # type: ignore[attr-defined]


def test_connect_reuses_same_save_connection(tmp_path: Path) -> None:
    _set_test_db_dir(tmp_path)
    try:
        conn_a = database.connect("save_a")
        conn_b = database.connect("save_a")
        assert conn_a is conn_b
        assert database.get_active_save_name() == "save_a"
    finally:
        database.close()


def test_connect_switches_save_slot_connection(tmp_path: Path) -> None:
    _set_test_db_dir(tmp_path)
    try:
        conn_a = database.connect("save_a")
        conn_a.execute("INSERT OR IGNORE INTO game_state (id, save_name) VALUES (1, 'save_a')")
        conn_a.commit()

        conn_b = database.connect("save_b")
        assert conn_b is not conn_a
        assert database.get_active_save_name() == "save_b"

        row_b = conn_b.execute("SELECT save_name FROM game_state WHERE id=1").fetchone()
        # save_b DB is independent from save_a data.
        assert row_b is None or row_b["save_name"] != "save_a"
    finally:
        database.close()


def test_connect_repairs_drifted_fixture_lineup_columns(tmp_path: Path) -> None:
    _set_test_db_dir(tmp_path)
    db_path = database.get_db_path("drift")

    # Build a drifted DB file with advanced schema version but missing lineup columns.
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            """
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
            """
        )
        conn.commit()
    finally:
        conn.close()

    try:
        live_conn = database.connect("drift")
        cols = [r["name"] for r in live_conn.execute("PRAGMA table_info(fixtures)").fetchall()]
        assert "submitted_starting_xi_json" in cols
        assert "submitted_bench_json" in cols
    finally:
        database.close()

