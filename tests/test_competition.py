import pytest
import sqlite3
from datetime import date
from src.core.competition import create_egypt_cup, is_cup_match, CUP_NAME
from src.data.models import Club, Fixture
from src.data.database import init_schema
from src.data import queries

def _create_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn

def _make_clubs(count=18):
    clubs = []
    for i in range(1, count + 1):
        clubs.append(Club(
            id=i, name=f"Club {i}", short_name=f"C{i}",
            city="Cairo", governorate="Cairo", reputation=100
        ))
    return clubs

def test_create_egypt_cup():
    conn = _create_test_db()
    clubs = _make_clubs(18)
    for c in clubs:
        queries.insert_club(conn, c)
    
    season_year = 2025
    start_date = date(2025, 8, 15)
    
    cup = create_egypt_cup(conn, clubs, season_year, start_date)
    
    assert cup.name == CUP_NAME
    assert cup.season_year == season_year
    # create_egypt_cup only initializes the first round
    assert len(cup.rounds) == 1
    
    # Check if Round of 32 was initialized with matches
    rnd32 = cup.rounds.get("Round of 32")
    assert rnd32 is not None
    assert len(rnd32.matches) == 16
    assert len(rnd32.fixture_ids) == 16

def test_is_cup_match():
    fixture_cup = Fixture(fixture_id=1, matchday=1, home_club_id=1, away_club_id=2, competition=CUP_NAME)
    fixture_league = Fixture(fixture_id=2, matchday=1, home_club_id=1, away_club_id=2, competition="Egyptian Premier League")
    
    assert is_cup_match(fixture_cup) is True
    assert is_cup_match(fixture_league) is False
