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

    # Always run migrations so existing saves get new tables/columns
    init_schema(_db_connection)

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
    user_club_name_ar TEXT NOT NULL DEFAULT '',
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
    pressing_intensity INTEGER NOT NULL DEFAULT 5,
    tempo INTEGER NOT NULL DEFAULT 5,
    width INTEGER NOT NULL DEFAULT 5,
    defensive_line INTEGER NOT NULL DEFAULT 5,
    is_user_controlled INTEGER NOT NULL DEFAULT 0,
    season_expectation TEXT NOT NULL DEFAULT 'mid_table',
    youth_promoted_count INTEGER NOT NULL DEFAULT 0,
    name_ar TEXT NOT NULL DEFAULT '',
    short_name_ar TEXT NOT NULL DEFAULT '',
    city_ar TEXT NOT NULL DEFAULT '',
    stadium_name_ar TEXT NOT NULL DEFAULT ''
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
    pace INTEGER NOT NULL DEFAULT 10,
    stamina INTEGER NOT NULL DEFAULT 10,
    strength INTEGER NOT NULL DEFAULT 10,
    agility INTEGER NOT NULL DEFAULT 10,
    jumping INTEGER NOT NULL DEFAULT 10,
    composure INTEGER NOT NULL DEFAULT 10,
    vision INTEGER NOT NULL DEFAULT 10,
    work_rate INTEGER NOT NULL DEFAULT 10,
    leadership INTEGER NOT NULL DEFAULT 10,
    aggression INTEGER NOT NULL DEFAULT 10,
    positioning INTEGER NOT NULL DEFAULT 10,
    decisions INTEGER NOT NULL DEFAULT 10,
    gk_reflexes INTEGER NOT NULL DEFAULT 5,
    gk_handling INTEGER NOT NULL DEFAULT 5,
    gk_positioning INTEGER NOT NULL DEFAULT 5,
    gk_one_on_ones INTEGER NOT NULL DEFAULT 5,
    gk_kicking INTEGER NOT NULL DEFAULT 5,
    wage_weekly INTEGER NOT NULL DEFAULT 0,
    contract_expiry TEXT,
    release_clause INTEGER,
    appearances INTEGER NOT NULL DEFAULT 0,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    clean_sheets INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0,
    minutes_played INTEGER NOT NULL DEFAULT 0,
    average_rating REAL NOT NULL DEFAULT 0.0,
    man_of_the_match INTEGER NOT NULL DEFAULT 0,
    injury_days_remaining INTEGER NOT NULL DEFAULT 0,
    injury_type TEXT NOT NULL DEFAULT '',
    suspension_matches INTEGER NOT NULL DEFAULT 0,
    training_focus TEXT NOT NULL DEFAULT '',
    matches_benched_streak INTEGER NOT NULL DEFAULT 0,
    name_ar TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS fixtures (
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

CREATE TABLE IF NOT EXISTS standings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL REFERENCES clubs(id),
    club_name TEXT NOT NULL,
    club_name_ar TEXT NOT NULL DEFAULT '',
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
    difficulty TEXT NOT NULL DEFAULT 'normal',
    language TEXT NOT NULL DEFAULT 'en'
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
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

CREATE TABLE IF NOT EXISTS loan_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL DEFAULT '',
    from_club_id INTEGER NOT NULL,
    from_club_name TEXT NOT NULL DEFAULT '',
    to_club_id INTEGER NOT NULL,
    to_club_name TEXT NOT NULL DEFAULT '',
    start_date TEXT NOT NULL DEFAULT '',
    end_date TEXT NOT NULL DEFAULT '',
    wage_split INTEGER NOT NULL DEFAULT 100,
    buy_option INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS transfer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL DEFAULT '',
    from_club_id INTEGER NOT NULL,
    from_club_name TEXT NOT NULL DEFAULT '',
    to_club_id INTEGER NOT NULL,
    to_club_name TEXT NOT NULL DEFAULT '',
    fee INTEGER NOT NULL DEFAULT 0,
    wage INTEGER NOT NULL DEFAULT 0,
    transfer_date TEXT NOT NULL DEFAULT '',
    transfer_type TEXT NOT NULL DEFAULT 'permanent'
);

CREATE TABLE IF NOT EXISTS head_to_head (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_a_id INTEGER NOT NULL,
    club_b_id INTEGER NOT NULL,
    club_a_wins INTEGER NOT NULL DEFAULT 0,
    club_b_wins INTEGER NOT NULL DEFAULT 0,
    draws INTEGER NOT NULL DEFAULT 0,
    club_a_goals INTEGER NOT NULL DEFAULT 0,
    club_b_goals INTEGER NOT NULL DEFAULT 0,
    UNIQUE(club_a_id, club_b_id)
);

CREATE TABLE IF NOT EXISTS season_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_year INTEGER NOT NULL UNIQUE,
    champion_club_id INTEGER,
    champion_club_name TEXT NOT NULL DEFAULT '',
    user_club_id INTEGER,
    user_position INTEGER NOT NULL DEFAULT 0,
    total_goals INTEGER NOT NULL DEFAULT 0,
    total_matches INTEGER NOT NULL DEFAULT 0,
    golden_boot_player TEXT NOT NULL DEFAULT '',
    golden_boot_goals INTEGER NOT NULL DEFAULT 0,
    golden_glove_player TEXT NOT NULL DEFAULT '',
    golden_glove_clean_sheets INTEGER NOT NULL DEFAULT 0,
    young_player_name TEXT NOT NULL DEFAULT '',
    most_assists_player TEXT NOT NULL DEFAULT '',
    most_assists_count INTEGER NOT NULL DEFAULT 0,
    cup_winner_club_id INTEGER,
    cup_winner_club_name TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS player_season_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_year INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL DEFAULT '',
    player_name_ar TEXT NOT NULL DEFAULT '',
    club_id INTEGER,
    club_name TEXT NOT NULL DEFAULT '',
    club_name_ar TEXT NOT NULL DEFAULT '',
    position TEXT NOT NULL DEFAULT '',
    age INTEGER NOT NULL DEFAULT 0,
    appearances INTEGER NOT NULL DEFAULT 0,
    goals INTEGER NOT NULL DEFAULT 0,
    assists INTEGER NOT NULL DEFAULT 0,
    clean_sheets INTEGER NOT NULL DEFAULT 0,
    yellow_cards INTEGER NOT NULL DEFAULT 0,
    red_cards INTEGER NOT NULL DEFAULT 0,
    minutes_played INTEGER NOT NULL DEFAULT 0,
    average_rating REAL NOT NULL DEFAULT 0.0,
    man_of_the_match INTEGER NOT NULL DEFAULT 0,
    UNIQUE(season_year, player_id)
);

CREATE TABLE IF NOT EXISTS club_season_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season_year INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    club_name TEXT NOT NULL DEFAULT '',
    club_name_ar TEXT NOT NULL DEFAULT '',
    position_finish INTEGER NOT NULL DEFAULT 0,
    played INTEGER NOT NULL DEFAULT 0,
    won INTEGER NOT NULL DEFAULT 0,
    drawn INTEGER NOT NULL DEFAULT 0,
    lost INTEGER NOT NULL DEFAULT 0,
    goals_for INTEGER NOT NULL DEFAULT 0,
    goals_against INTEGER NOT NULL DEFAULT 0,
    points INTEGER NOT NULL DEFAULT 0,
    UNIQUE(season_year, club_id)
);

CREATE TABLE IF NOT EXISTS cup_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    competition_name TEXT NOT NULL DEFAULT 'Egypt Cup',
    season_year INTEGER NOT NULL,
    current_round TEXT NOT NULL DEFAULT '',
    rounds_json TEXT NOT NULL DEFAULT '{}',
    champion_club_id INTEGER,
    champion_club_name TEXT NOT NULL DEFAULT '',
    is_complete INTEGER NOT NULL DEFAULT 0,
    UNIQUE(competition_name, season_year)
);

CREATE TABLE IF NOT EXISTS rivalries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_a_id INTEGER NOT NULL,
    club_b_id INTEGER NOT NULL,
    rivalry_name TEXT NOT NULL DEFAULT '',
    rivalry_name_ar TEXT NOT NULL DEFAULT '',
    intensity INTEGER NOT NULL DEFAULT 3,
    description TEXT NOT NULL DEFAULT '',
    description_ar TEXT NOT NULL DEFAULT '',
    UNIQUE(club_a_id, club_b_id)
);

CREATE INDEX IF NOT EXISTS idx_player_archive_season ON player_season_archive(season_year);
CREATE INDEX IF NOT EXISTS idx_player_archive_player ON player_season_archive(player_id);
CREATE INDEX IF NOT EXISTS idx_club_archive_season ON club_season_archive(season_year);
CREATE INDEX IF NOT EXISTS idx_club_archive_club ON club_season_archive(club_id);

CREATE TABLE IF NOT EXISTS manager_career (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total_wins INTEGER NOT NULL DEFAULT 0,
    total_draws INTEGER NOT NULL DEFAULT 0,
    total_losses INTEGER NOT NULL DEFAULT 0,
    trophies INTEGER NOT NULL DEFAULT 0,
    longest_win_streak INTEGER NOT NULL DEFAULT 0,
    current_win_streak INTEGER NOT NULL DEFAULT 0,
    current_unbeaten INTEGER NOT NULL DEFAULT 0,
    longest_unbeaten INTEGER NOT NULL DEFAULT 0,
    clean_sheets INTEGER NOT NULL DEFAULT 0,
    total_goals_scored INTEGER NOT NULL DEFAULT 0,
    total_goals_conceded INTEGER NOT NULL DEFAULT 0,
    best_signing_name TEXT NOT NULL DEFAULT '',
    best_signing_fee INTEGER NOT NULL DEFAULT 0,
    manager_rating REAL NOT NULL DEFAULT 50.0
);

CREATE TABLE IF NOT EXISTS achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT '🏆',
    unlocked INTEGER NOT NULL DEFAULT 0,
    unlock_date TEXT NOT NULL DEFAULT ''
);
"""


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Run versioned schema migrations. Each migration runs at most once."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")

    row = conn.execute("SELECT MAX(version) as v FROM schema_version").fetchone()
    current_version = row["v"] if row and row["v"] is not None else 0

    for ver, sqls in _MIGRATIONS:
        if ver <= current_version:
            continue
        for sql in sqls:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError as e:
                msg = str(e).lower()
                if "already exists" in msg or "duplicate column name" in msg:
                    pass  # Column/table already exists
                else:
                    # Log or raise other errors
                    raise e
        conn.execute("INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (ver,))

    conn.commit()


# ── Ordered Migrations ────────────────────────────────────────────────────────

_MIGRATIONS = [
    (1, [
        "ALTER TABLE players ADD COLUMN injury_days_remaining INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE players ADD COLUMN injury_type TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE players ADD COLUMN suspension_matches INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE players ADD COLUMN training_focus TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN season_expectation TEXT NOT NULL DEFAULT 'mid_table'",
        "ALTER TABLE players ADD COLUMN matches_benched_streak INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE clubs ADD COLUMN youth_promoted_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE clubs ADD COLUMN pressing_intensity INTEGER NOT NULL DEFAULT 5",
        "ALTER TABLE clubs ADD COLUMN tempo INTEGER NOT NULL DEFAULT 5",
        "ALTER TABLE clubs ADD COLUMN width INTEGER NOT NULL DEFAULT 5",
        "ALTER TABLE clubs ADD COLUMN defensive_line INTEGER NOT NULL DEFAULT 5",
    ]),
    (2, [
        """CREATE TABLE IF NOT EXISTS season_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_year INTEGER NOT NULL UNIQUE,
            champion_club_id INTEGER,
            champion_club_name TEXT NOT NULL DEFAULT '',
            user_club_id INTEGER,
            user_position INTEGER NOT NULL DEFAULT 0,
            total_goals INTEGER NOT NULL DEFAULT 0,
            total_matches INTEGER NOT NULL DEFAULT 0,
            golden_boot_player TEXT NOT NULL DEFAULT '',
            golden_boot_goals INTEGER NOT NULL DEFAULT 0,
            golden_glove_player TEXT NOT NULL DEFAULT '',
            golden_glove_clean_sheets INTEGER NOT NULL DEFAULT 0,
            young_player_name TEXT NOT NULL DEFAULT '',
            most_assists_player TEXT NOT NULL DEFAULT '',
            most_assists_count INTEGER NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS player_season_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_year INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            player_name TEXT NOT NULL DEFAULT '',
            club_id INTEGER,
            club_name TEXT NOT NULL DEFAULT '',
            position TEXT NOT NULL DEFAULT '',
            age INTEGER NOT NULL DEFAULT 0,
            appearances INTEGER NOT NULL DEFAULT 0,
            goals INTEGER NOT NULL DEFAULT 0,
            assists INTEGER NOT NULL DEFAULT 0,
            clean_sheets INTEGER NOT NULL DEFAULT 0,
            yellow_cards INTEGER NOT NULL DEFAULT 0,
            red_cards INTEGER NOT NULL DEFAULT 0,
            minutes_played INTEGER NOT NULL DEFAULT 0,
            average_rating REAL NOT NULL DEFAULT 0.0,
            man_of_the_match INTEGER NOT NULL DEFAULT 0,
            UNIQUE(season_year, player_id)
        )""",
        """CREATE TABLE IF NOT EXISTS club_season_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season_year INTEGER NOT NULL,
            club_id INTEGER NOT NULL,
            club_name TEXT NOT NULL DEFAULT '',
            position_finish INTEGER NOT NULL DEFAULT 0,
            played INTEGER NOT NULL DEFAULT 0,
            won INTEGER NOT NULL DEFAULT 0,
            drawn INTEGER NOT NULL DEFAULT 0,
            lost INTEGER NOT NULL DEFAULT 0,
            goals_for INTEGER NOT NULL DEFAULT 0,
            goals_against INTEGER NOT NULL DEFAULT 0,
            points INTEGER NOT NULL DEFAULT 0,
            UNIQUE(season_year, club_id)
        )""",
        "CREATE INDEX IF NOT EXISTS idx_player_archive_season ON player_season_archive(season_year)",
        "CREATE INDEX IF NOT EXISTS idx_player_archive_player ON player_season_archive(player_id)",
        "CREATE INDEX IF NOT EXISTS idx_club_archive_season ON club_season_archive(season_year)",
        "CREATE INDEX IF NOT EXISTS idx_club_archive_club ON club_season_archive(club_id)",
    ]),
    (3, [
        "ALTER TABLE fixtures ADD COLUMN player_ratings_json TEXT NOT NULL DEFAULT '{}'",
    ]),
    (4, [
        # ── Egypt Cup state table ────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS cup_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_name TEXT NOT NULL DEFAULT 'Egypt Cup',
            season_year INTEGER NOT NULL,
            current_round TEXT NOT NULL DEFAULT '',
            rounds_json TEXT NOT NULL DEFAULT '{}',
            champion_club_id INTEGER,
            champion_club_name TEXT NOT NULL DEFAULT '',
            is_complete INTEGER NOT NULL DEFAULT 0,
            UNIQUE(competition_name, season_year)
        )""",
        # Extra-time / penalty columns for knockout matches
        "ALTER TABLE fixtures ADD COLUMN extra_time INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE fixtures ADD COLUMN penalties_json TEXT NOT NULL DEFAULT ''",
        # ── Rivalries table ──────────────────────────────────────────
        """CREATE TABLE IF NOT EXISTS rivalries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_a_id INTEGER NOT NULL,
            club_b_id INTEGER NOT NULL,
            rivalry_name TEXT NOT NULL DEFAULT '',
            rivalry_name_ar TEXT NOT NULL DEFAULT '',
            intensity INTEGER NOT NULL DEFAULT 3,
            description TEXT NOT NULL DEFAULT '',
            description_ar TEXT NOT NULL DEFAULT '',
            UNIQUE(club_a_id, club_b_id)
        )""",
        # ── Arabic name columns ──────────────────────────────────────
        "ALTER TABLE clubs ADD COLUMN name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN short_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN city_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN stadium_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE players ADD COLUMN name_ar TEXT NOT NULL DEFAULT ''",
        # ── Language setting ─────────────────────────────────────────
        "ALTER TABLE game_settings ADD COLUMN language TEXT NOT NULL DEFAULT 'en'",
        # ── Cup winner in season history ─────────────────────────────
        "ALTER TABLE season_history ADD COLUMN cup_winner_club_id INTEGER",
        "ALTER TABLE season_history ADD COLUMN cup_winner_club_name TEXT NOT NULL DEFAULT ''",
    ]),
    (5, [
        # REPAIR: Ensure critical columns exist (might have been skipped due to bug in migration runner)
        "ALTER TABLE fixtures ADD COLUMN player_ratings_json TEXT NOT NULL DEFAULT '{}'",
        "ALTER TABLE fixtures ADD COLUMN extra_time INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE fixtures ADD COLUMN penalties_json TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN short_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN city_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE clubs ADD COLUMN stadium_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE players ADD COLUMN name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE game_settings ADD COLUMN language TEXT NOT NULL DEFAULT 'en'",
        "ALTER TABLE season_history ADD COLUMN cup_winner_club_id INTEGER",
        "ALTER TABLE season_history ADD COLUMN cup_winner_club_name TEXT NOT NULL DEFAULT ''",
    ]),
    (6, [
        "ALTER TABLE fixtures ADD COLUMN home_club_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE fixtures ADD COLUMN away_club_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE standings ADD COLUMN club_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE player_season_archive ADD COLUMN player_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE player_season_archive ADD COLUMN club_name_ar TEXT NOT NULL DEFAULT ''",
        "ALTER TABLE club_season_archive ADD COLUMN club_name_ar TEXT NOT NULL DEFAULT ''",
    ]),
    (7, [
        "ALTER TABLE game_state ADD COLUMN user_club_name_ar TEXT NOT NULL DEFAULT ''",
    ]),
    (8, [
        # RELAX FOREIGN KEY CONSTRAINTS on fixtures to allow virtual Cup clubs (negative IDs)
        "CREATE TABLE fixtures_new (id INTEGER PRIMARY KEY AUTOINCREMENT, matchday INTEGER NOT NULL, home_club_id INTEGER NOT NULL, away_club_id INTEGER NOT NULL, home_club_name TEXT NOT NULL DEFAULT '', away_club_name TEXT NOT NULL DEFAULT '', home_club_name_ar TEXT NOT NULL DEFAULT '', away_club_name_ar TEXT NOT NULL DEFAULT '', match_date TEXT, played INTEGER NOT NULL DEFAULT 0, home_goals INTEGER DEFAULT NULL, away_goals INTEGER DEFAULT NULL, events_json TEXT NOT NULL DEFAULT '[]', home_stats_json TEXT NOT NULL DEFAULT '{}', away_stats_json TEXT NOT NULL DEFAULT '{}', competition TEXT NOT NULL DEFAULT 'Egyptian Premier League', player_ratings_json TEXT NOT NULL DEFAULT '{}', extra_time INTEGER NOT NULL DEFAULT 0, penalties_json TEXT NOT NULL DEFAULT '')",
        "INSERT INTO fixtures_new SELECT * FROM fixtures",
        "DROP TABLE fixtures",
        "ALTER TABLE fixtures_new RENAME TO fixtures",
        "CREATE INDEX IF NOT EXISTS idx_fixtures_matchday ON fixtures(matchday)",
        "CREATE INDEX IF NOT EXISTS idx_fixtures_played ON fixtures(played)",
    ]),
]

