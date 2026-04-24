"""
Tests for season lifecycle — end-of-season processing and new season creation.
"""

import sqlite3
from datetime import date, timedelta
from src.data.database import init_schema
from src.data.models import GameState, Club, ClubFinances
from src.data import queries
from src.core.season import start_new_season, get_season_awards
from src.core.league import generate_fixtures
from src.utils.config import LEAGUE_TEAM_COUNT
from src.utils import rng


def _create_test_db() -> sqlite3.Connection:
    """Create an in-memory test database."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn


def _create_test_clubs(conn: sqlite3.Connection) -> list[Club]:
    """Create 18 test clubs in the database."""
    clubs = []
    for i in range(1, LEAGUE_TEAM_COUNT + 1):
        club = Club(
            name=f"Test Club {i}",
            short_name=f"TC{i}",
            city="Cairo",
            governorate="Cairo",
            reputation=200 - i * 5,
            finances=ClubFinances(balance=10000000),
        )
        club_id = queries.insert_club(conn, club)
        club.id = club_id
        clubs.append(club)
    return clubs


def _create_game_state(
    conn: sqlite3.Connection, clubs: list[Club], season_year: int = 2025
) -> GameState:
    """Create a test game state with user's first club."""
    gs = GameState(
        save_name="test_save",
        season_year=season_year,
        current_date=date(season_year, 8, 15),
        user_club_id=clubs[0].id,
        user_club_name=clubs[0].name,
        manager_name="Test Manager",
        rng_seed=42,
        day_count=0,
    )
    queries.save_game_state(conn, gs)
    return gs


class TestSeasonAwards:
    """Test suite for season awards calculation."""

    def setup_method(self):
        rng.seed(42)
        self.conn = _create_test_db()
        self.clubs = _create_test_clubs(self.conn)
        generate_fixtures(self.conn, self.clubs, date(2025, 8, 15))
        queries.init_standings(self.conn, self.clubs)
        self.gs = _create_game_state(self.conn, self.clubs)

    def teardown_method(self):
        self.conn.close()

    def test_get_season_awards_returns_dict(self):
        """get_season_awards should return a dictionary."""
        awards = get_season_awards(self.conn, self.gs)
        assert isinstance(awards, dict)
        assert "champion" in awards
        assert "standings" in awards
        assert "top_scorers" in awards
        assert "golden_boot" in awards
        assert "golden_glove" in awards
        assert "young_player" in awards
        assert "most_assists" in awards

    def test_is_user_champion_flag(self):
        """Should correctly identify if user is champion."""
        awards = get_season_awards(self.conn, self.gs)
        assert "is_user_champion" in awards
        assert isinstance(awards["is_user_champion"], bool)

    def test_user_position_recorded(self):
        """User's final position should be in awards."""
        awards = get_season_awards(self.conn, self.gs)
        assert "user_position" in awards
        assert isinstance(awards["user_position"], int)
        assert awards["user_position"] > 0


class TestStartNewSeason:
    """Test suite for new season creation."""

    def setup_method(self):
        rng.seed(42)
        self.conn = _create_test_db()
        self.clubs = _create_test_clubs(self.conn)
        generate_fixtures(self.conn, self.clubs, date(2025, 8, 15))
        queries.init_standings(self.conn, self.clubs)
        self.gs = _create_game_state(self.conn, self.clubs)

    def teardown_method(self):
        self.conn.close()

    def test_start_new_season_increments_year(self):
        """Season year should increment by 1."""
        original_year = self.gs.season_year
        messages = start_new_season(self.conn, self.gs)

        assert self.gs.season_year == original_year + 1
        assert any(f"Season {self.gs.season_year}" in m for m in messages)

    def test_start_new_season_resets_date(self):
        """Current date should reset to August 15 of new season year."""
        start_new_season(self.conn, self.gs)

        assert self.gs.current_date.month == 8
        assert self.gs.current_date.day == 15
        assert self.gs.day_count == 0

    def test_start_new_season_regenerates_fixtures(self):
        """New season should have fresh fixtures."""
        start_new_season(self.conn, self.gs)

        fixtures = queries.get_fixtures_by_matchday(self.conn, 1)
        assert len(fixtures) > 0

    def test_start_new_season_resets_standings(self):
        """Standings should be reset for new season."""
        start_new_season(self.conn, self.gs)

        standings = queries.get_standings(self.conn)
        for s in standings:
            assert s.played == 0
            assert s.points == 0

    def test_start_new_season_creates_inbox_messages(self):
        """Should create inbox messages for new season."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM inbox")
        initial_count = cursor.fetchone()[0]

        start_new_season(self.conn, self.gs)

        cursor = self.conn.execute("SELECT COUNT(*) FROM inbox")
        new_count = cursor.fetchone()[0]
        assert new_count > initial_count

    def test_start_new_season_creates_egypt_cup(self):
        """New season should create Egypt Cup."""
        start_new_season(self.conn, self.gs)

        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM fixtures WHERE competition LIKE '%Cup%'"
        )
        cup_count = cursor.fetchone()[0]
        assert cup_count > 0

    def test_start_new_season_returns_messages_list(self):
        """Should return a list of status messages."""
        messages = start_new_season(self.conn, self.gs)

        assert isinstance(messages, list)
        assert len(messages) > 0
        assert all(isinstance(m, str) for m in messages)
