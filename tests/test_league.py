"""
Tests for league fixture generation and standings.
"""
import sqlite3
from datetime import date
from src.data.database import init_schema
from src.data.models import Club, ClubFinances, MatchResult
from src.data import queries
from src.core.league import generate_fixtures, get_current_standings
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


class TestLeague:
    """Test suite for league fixture generation and standings."""

    def setup_method(self):
        rng.seed(42)
        self.conn = _create_test_db()
        self.clubs = _create_test_clubs(self.conn)

    def teardown_method(self):
        self.conn.close()

    def test_fixture_generation_creates_correct_count(self):
        """Should generate 306 fixtures (18 teams × 34 matchdays / 2)."""
        fixtures = generate_fixtures(self.conn, self.clubs, date(2025, 8, 15))
        # 18 teams: 9 matches per matchday × 34 matchdays = 306 total
        assert len(fixtures) == 306

    def test_each_team_plays_correct_number_of_matches(self):
        """Each team should play exactly 34 matches."""
        fixtures = generate_fixtures(self.conn, self.clubs, date(2025, 8, 15))

        match_counts = {}
        for f in fixtures:
            match_counts[f.home_club_id] = match_counts.get(f.home_club_id, 0) + 1
            match_counts[f.away_club_id] = match_counts.get(f.away_club_id, 0) + 1

        for club in self.clubs:
            assert match_counts.get(club.id, 0) == 34, \
                f"Club {club.name} has {match_counts.get(club.id, 0)} matches"

    def test_no_team_plays_itself(self):
        """No fixture should have the same home and away team."""
        fixtures = generate_fixtures(self.conn, self.clubs, date(2025, 8, 15))
        for f in fixtures:
            assert f.home_club_id != f.away_club_id

    def test_standings_initialized_at_zero(self):
        """All standings should start at 0 points."""
        queries.init_standings(self.conn, self.clubs)
        standings = get_current_standings(self.conn)

        assert len(standings) == LEAGUE_TEAM_COUNT
        for s in standings:
            assert s.points == 0
            assert s.played == 0

    def test_standings_update_after_result(self):
        """Standings should update correctly after a match result."""
        queries.init_standings(self.conn, self.clubs)

        result = MatchResult(
            home_club_id=self.clubs[0].id,
            away_club_id=self.clubs[1].id,
            home_club_name=self.clubs[0].name,
            away_club_name=self.clubs[1].name,
            home_goals=2,
            away_goals=1,
        )
        queries.update_standings_for_result(self.conn, result)

        standings = get_current_standings(self.conn)
        winner = next(s for s in standings if s.club_id == self.clubs[0].id)
        loser = next(s for s in standings if s.club_id == self.clubs[1].id)

        assert winner.points == 3
        assert winner.won == 1
        assert winner.goals_for == 2
        assert winner.goals_against == 1

        assert loser.points == 0
        assert loser.lost == 1
        assert loser.goals_for == 1
        assert loser.goals_against == 2

    def test_draw_awards_one_point_each(self):
        """A draw should give 1 point to each team."""
        queries.init_standings(self.conn, self.clubs)

        result = MatchResult(
            home_club_id=self.clubs[0].id,
            away_club_id=self.clubs[1].id,
            home_goals=1,
            away_goals=1,
        )
        queries.update_standings_for_result(self.conn, result)

        standings = get_current_standings(self.conn)
        home = next(s for s in standings if s.club_id == self.clubs[0].id)
        away = next(s for s in standings if s.club_id == self.clubs[1].id)

        assert home.points == 1
        assert home.drawn == 1
        assert away.points == 1
        assert away.drawn == 1

