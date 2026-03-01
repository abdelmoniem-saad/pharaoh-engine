"""
SQLite database management for Pharaoh Engine.

Handles connection lifecycle, schema creation, and migrations.
Uses raw sqlite3 for maximum portability on mobile.
"""
from __future__ import annotations

import sqlite3
import os
from pathlib import Path


# Default DB path — will be set to app storage dir on mobile
_DEFAULT_DB_DIR = Path(__file__).parent.parent.parent / "saves"
_db_connection: sqlite3.Connection | None = None


def get_db_path(save_name: str = "default") -> Path:
    """Get the database file path for a save game."""
    db_dir = _DEFAULT_DB_DIR
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / f"{save_name}.db"


def connect(save_name: str = "default") -> sqlite3.Connection:
    """Open or return an existing database connection."""
    global _db_connection
    if _db_connection is not None:
        return _db_connection

    db_path = get_db_path(save_name)
    _db_connection = sqlite3.connect(str(db_path))
    _db_connection.row_factory = sqlite3.Row
    _db_connection.execute("PRAGMA journal_mode=WAL")
    _db_connection.execute("PRAGMA foreign_keys=ON")
    return _db_connection


def close() -> None:
    """Close the current database connection."""
    global _db_connection
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None


def delete_save(save_name: str) -> None:
    """Delete a save game database file."""
    db_path = get_db_path(save_name)
    close()
    if db_path.exists():
        os.remove(db_path)


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all database tables if they don't exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    _migrate_schema(conn)


# ── Schema Definition ────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS game_state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    save_name TEXT NOT NULL DEFAULT '',
    season_year INTEGER NOT NULL DEFAULT 2025,
    current_date TEXT NOT NULL DEFAULT '2025-08-15',
    user_club_id INTEGER NOT NULL DEFAULT 0,
    user_club_name TEXT NOT NULL DEFAULT '',
    manager_name TEXT NOT NULL DEFAULT 'Manager',
    rng_seed INTEGER NOT NULL DEFAULT 42,
    day_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS clubs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT '',
    governorate TEXT NOT NULL DEFAULT '',
    reputation INTEGER NOT NULL DEFAULT 100,
    facilities_level INTEGER NOT NULL DEFAULT 5,
    youth_rating INTEGER NOT NULL DEFAULT 5,
    stadium_name TEXT NOT NULL DEFAULT '',
    stadium_capacity INTEGER NOT NULL DEFAULT 10000,
    primary_color TEXT NOT NULL DEFAULT '#FFFFFF',
    secondary_color TEXT NOT NULL DEFAULT '#000000',
    balance INTEGER NOT NULL DEFAULT 0,
    transfer_budget INTEGER NOT NULL DEFAULT 0,
    wage_budget_weekly INTEGER NOT NULL DEFAULT 0,
    wage_bill_weekly INTEGER NOT NULL DEFAULT 0,
    matchday_income INTEGER NOT NULL DEFAULT 0,
    sponsorship_income_yearly INTEGER NOT NULL DEFAULT 0,
    tv_revenue_yearly INTEGER NOT NULL DEFAULT 0,
    board_confidence INTEGER NOT NULL DEFAULT 60,
    fan_happiness INTEGER NOT NULL DEFAULT 50,
    formation TEXT NOT NULL DEFAULT '4-2-3-1',
    mentality INTEGER NOT NULL DEFAULT 4,
    is_user_controlled INTEGER NOT NULL DEFAULT 0,
    season_expectation TEXT NOT NULL DEFAULT 'mid_table'
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    nationality TEXT NOT NULL DEFAULT 'Egyptian',
    governorate TEXT NOT NULL DEFAULT 'Cairo',
    position TEXT NOT NULL,
    secondary_positions TEXT NOT NULL DEFAULT '[]',
    preferred_foot TEXT NOT NULL DEFAULT 'Right',
    current_ability INTEGER NOT NULL DEFAULT 100,
    potential_ability INTEGER NOT NULL DEFAULT 120,
    club_id INTEGER REFERENCES clubs(id),
    morale INTEGER NOT NULL DEFAULT 50,
    fitness INTEGER NOT NULL DEFAULT 100,
    form REAL NOT NULL DEFAULT 7.0,
    is_captain INTEGER NOT NULL DEFAULT 0,
    shirt_number INTEGER,
    transfer_listed INTEGER NOT NULL DEFAULT 0,

    -- Technical attributes
    finishing INTEGER NOT NULL DEFAULT 10,
    passing INTEGER NOT NULL DEFAULT 10,
    dribbling INTEGER NOT NULL DEFAULT 10,
    first_touch INTEGER NOT NULL DEFAULT 10,
    crossing INTEGER NOT NULL DEFAULT 10,
    heading INTEGER NOT NULL DEFAULT 10,
    long_shots INTEGER NOT NULL DEFAULT 10,
    tackling INTEGER NOT NULL DEFAULT 10,
    marking INTEGER NOT NULL DEFAULT 10,
    free_kicks INTEGER NOT NULL DEFAULT 10,

    -- Physical attributes
    pace INTEGER NOT NULL DEFAULT 10,
    stamina INTEGER NOT NULL DEFAULT 10,
    strength INTEGER NOT NULL DEFAULT 10,
    agility INTEGER NOT NULL DEFAULT 10,
    jumping INTEGER NOT NULL DEFAULT 10,

    -- Mental attributes
    composure INTEGER NOT NULL DEFAULT 10,
    vision INTEGER NOT NULL DEFAULT 10,
    work_rate INTEGER NOT NULL DEFAULT 10,
    leadership INTEGER NOT NULL DEFAULT 10,
    aggression INTEGER NOT NULL DEFAULT 10,
    positioning INTEGER NOT NULL DEFAULT 10,
    decisions INTEGER NOT NULL DEFAULT 10,

    -- GK attributes
    gk_reflexes INTEGER NOT NULL DEFAULT 5,
    gk_handling INTEGER NOT NULL DEFAULT 5,
    gk_positioning INTEGER NOT NULL DEFAULT 5,
    gk_one_on_ones INTEGER NOT NULL DEFAULT 5,
    gk_kicking INTEGER NOT NULL DEFAULT 5,

    -- Contract
    wage_weekly INTEGER NOT NULL DEFAULT 0,
    contract_expiry TEXT,
    release_clause INTEGER,

    -- Season stats
    appearances INTEGER NOT NULL DEFAULT 0,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    clean_sheets INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0,
    minutes_played INTEGER NOT NULL DEFAULT 0,
    average_rating REAL NOT NULL DEFAULT 0.0,
    man_of_the_match INTEGER NOT NULL DEFAULT 0,

    -- Injury & suspension
    injury_days_remaining INTEGER NOT NULL DEFAULT 0,
    injury_type TEXT NOT NULL DEFAULT '',
    suspension_matches INTEGER NOT NULL DEFAULT 0,

    -- Training
    training_focus TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fixtures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    matchday INTEGER NOT NULL,
    home_club_id INTEGER NOT NULL REFERENCES clubs(id),
    away_club_id INTEGER NOT NULL REFERENCES clubs(id),
    home_club_name TEXT NOT NULL DEFAULT '',
    away_club_name TEXT NOT NULL DEFAULT '',
    match_date TEXT,
    played INTEGER NOT NULL DEFAULT 0,
    home_goals INTEGER DEFAULT NULL,
    away_goals INTEGER DEFAULT NULL,
    events_json TEXT NOT NULL DEFAULT '[]',
    home_stats_json TEXT NOT NULL DEFAULT '{}',
    away_stats_json TEXT NOT NULL DEFAULT '{}',
    competition TEXT NOT NULL DEFAULT 'Egyptian Premier League'
);

CREATE TABLE IF NOT EXISTS standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    club_name TEXT NOT NULL,
    played INTEGER NOT NULL DEFAULT 0,
    won INTEGER NOT NULL DEFAULT 0,
    drawn INTEGER NOT NULL DEFAULT 0,
    lost INTEGER NOT NULL DEFAULT 0,
    goals_for INTEGER NOT NULL DEFAULT 0,
    goals_against INTEGER NOT NULL DEFAULT 0,
    UNIQUE(club_id)
);

CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_date TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    is_read INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_players_club ON players(club_id);
CREATE INDEX IF NOT EXISTS idx_fixtures_matchday ON fixtures(matchday);
CREATE INDEX IF NOT EXISTS idx_fixtures_played ON fixtures(played);

CREATE TABLE IF NOT EXISTS game_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    match_speed INTEGER NOT NULL DEFAULT 3,
    auto_save INTEGER NOT NULL DEFAULT 1,
    auto_save_interval INTEGER NOT NULL DEFAULT 7,
    difficulty TEXT NOT NULL DEFAULT 'normal'
);

CREATE TABLE IF NOT EXISTS transfer_negotiations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL DEFAULT '',
    from_club_id INTEGER NOT NULL,
    from_club_name TEXT NOT NULL DEFAULT '',
    to_club_id INTEGER NOT NULL,
    to_club_name TEXT NOT NULL DEFAULT '',
    phase TEXT NOT NULL DEFAULT 'fee',
    status TEXT NOT NULL DEFAULT 'pending',
    current_offer INTEGER NOT NULL DEFAULT 0,
    asking_price INTEGER NOT NULL DEFAULT 0,
    counter_price INTEGER NOT NULL DEFAULT 0,
    wage_offer INTEGER NOT NULL DEFAULT 0,
    current_wage INTEGER NOT NULL DEFAULT 0,
    attempt INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    submitted_date TEXT NOT NULL DEFAULT '',
    respond_date TEXT NOT NULL DEFAULT '',
    direction TEXT NOT NULL DEFAULT 'user_buying'
);
"""


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Add columns that may not exist in older saves."""
    migrations = [
        ("players", "injury_days_remaining", "INTEGER NOT NULL DEFAULT 0"),
        ("players", "injury_type", "TEXT NOT NULL DEFAULT ''"),
        ("players", "suspension_matches", "INTEGER NOT NULL DEFAULT 0"),
        ("players", "training_focus", "TEXT NOT NULL DEFAULT ''"),
        ("clubs", "season_expectation", "TEXT NOT NULL DEFAULT 'mid_table'"),
    ]
    for table, col, col_def in migrations:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()


