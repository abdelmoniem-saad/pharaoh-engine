import sqlite3
from datetime import date
import pytest
from src.data.queries import transfer_player


def test_old_offer_cannot_move_player_or_money_twice():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE players(id INTEGER, club_id INTEGER, wage_weekly INTEGER, contract_expiry TEXT, transfer_listed INTEGER, morale INTEGER);
        CREATE TABLE clubs(id INTEGER, transfer_budget INTEGER, balance INTEGER, wage_bill_weekly INTEGER);
        INSERT INTO players VALUES(1, 1, 100, '', 1, 50);
        INSERT INTO clubs VALUES(1, 10000, 10000, 100);
        INSERT INTO clubs VALUES(2, 10000, 10000, 0);
    """)
    transfer_player(conn, 1, 1, 2, 1000, 200, current_date=date(2025,8,15))
    snapshot = [tuple(row) for row in conn.execute('SELECT * FROM clubs ORDER BY id')]
    with pytest.raises(ValueError):
        transfer_player(conn, 1, 1, 2, 1000, 200)
    assert [tuple(row) for row in conn.execute('SELECT * FROM clubs ORDER BY id')] == snapshot
    assert conn.execute('SELECT club_id FROM players').fetchone()[0] == 2
    conn.close()
