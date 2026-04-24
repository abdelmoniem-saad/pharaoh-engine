import pytest
import sqlite3
from datetime import date
from src.core.calendar import advance_day
from src.data.models import GameState, Club, ClubFinances, Player, PlayerAttributes, PlayerContract
from src.data.database import init_schema
from src.data import queries
from src.utils.config import is_ramadan, Position

def _create_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    return conn

def test_is_ramadan():
    # 2025: (2, 28, 30) -> Feb 28 to Mar 30
    assert is_ramadan(date(2025, 2, 27)) is False
    assert is_ramadan(date(2025, 2, 28)) is True
    assert is_ramadan(date(2025, 3, 30)) is True
    assert is_ramadan(date(2025, 3, 31)) is False

def test_advance_day_logic():
    conn = _create_test_db()
    gs = GameState(current_date=date(2025, 8, 15), user_club_id=1)
    queries.save_game_state(conn, gs)
    
    club = Club(id=1, name="Test", short_name="T", city="C", governorate="C")
    queries.insert_club(conn, club)
    
    advance_day(conn, gs)
    assert gs.current_date == date(2025, 8, 16)
    
    new_gs = queries.load_game_state(conn)
    assert new_gs.current_date == date(2025, 8, 16)

def test_monthly_finances_trigger():
    conn = _create_test_db()
    # Day 29 -> Day 30 should trigger monthly finances
    gs = GameState(current_date=date(2025, 8, 31), user_club_id=1, day_count=29)
    
    club = Club(id=1, name="Test", short_name="T", city="C", governorate="C",
                finances=ClubFinances(balance=1000000, wage_bill_weekly=10000))
    queries.insert_club(conn, club)
    queries.save_game_state(conn, gs)
    
    advance_day(conn, gs)
    
    updated_club = queries.get_club(conn, 1)
    # Balance should have changed from monthly processing
    assert updated_club.finances.balance != 1000000
    
    messages = queries.get_inbox(conn)
    assert any(m.subject == "💰 Monthly Financial Report" for m in messages)

def test_daily_recovery():
    conn = _create_test_db()
    gs = GameState(current_date=date(2025, 8, 15), user_club_id=1)
    
    club = Club(id=1, name="Test", short_name="T", city="C", governorate="C")
    queries.insert_club(conn, club)
    
    player = Player(
        id=1, name="Tired Player", age=25, position=Position.CM,
        attributes=PlayerAttributes(), current_ability=100,
        contract=PlayerContract(), fitness=70, club_id=1
    )
    queries.insert_player(conn, player)
    queries.save_game_state(conn, gs)
    
    advance_day(conn, gs)
    
    updated_player = queries.get_player(conn, 1)
    assert updated_player.fitness > 70
