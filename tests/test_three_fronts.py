"""
Tests for the three depth fronts:
  1. AI substitutions driven by the per-player condition model
  2. Loan obligations executed at season/loan end
  3. Scouting reports (uncertainty until scouted)
Plus a regression proof that development plans change real attributes.
"""
import sqlite3
import tempfile
from datetime import date, timedelta
from pathlib import Path

from src.data.models import (
    Player, PlayerAttributes, PlayerContract, Club, ClubFinances,
    TeamTactics, GameState,
)
from src.core.match_engine import simulate_match, MatchEventType
from src.core.transfers import process_loan_returns
from src.core.tactics import auto_select_xi
from src.utils.config import Position, Mentality
from src.utils import rng


# ── Shared builders ──────────────────────────────────────────────────────────

def _player(pid, name, position, ca=110, stamina=13, fitness=90):
    return Player(
        id=pid, name=name, age=25, position=position,
        attributes=PlayerAttributes(stamina=stamina),
        current_ability=ca, potential_ability=ca + 30,
        contract=PlayerContract(wage_weekly=50000,
                                contract_expiry=date(2027, 6, 30)),
        fitness=fitness, morale=60, form=7.0,
    )


def _squad(start_id, stamina=13, fitness=90):
    positions = [
        Position.GK, Position.GK,
        Position.CB, Position.CB, Position.CB, Position.CB,
        Position.LB, Position.RB,
        Position.CDM, Position.CDM,
        Position.CM, Position.CM, Position.CM,
        Position.CAM, Position.CAM,
        Position.LW, Position.RW,
        Position.ST, Position.ST, Position.ST,
        Position.GK, Position.CB, Position.CM, Position.LW, Position.ST,
    ]
    return [_player(start_id + i, f"P{start_id + i}", pos,
                    stamina=stamina, fitness=fitness)
            for i, pos in enumerate(positions)]


def _club(cid, name):
    return Club(id=cid, name=name, short_name=name[:3].upper(),
                city="Cairo", governorate="Cairo", reputation=150,
                finances=ClubFinances(balance=50_000_000))


def _tactics(squad):
    xi, bench = auto_select_xi(squad, "4-2-3-1")
    return TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                       starting_xi=xi, bench=bench)


# ── 1. AI substitutions ─────────────────────────────────────────────────────

class TestAISubs:
    def test_tired_side_makes_subs(self):
        """A side worn to the bone must send on fresh legs; subs stay ≤3."""
        rng.seed(5)
        home_club = _club(1, "Home FC")
        away_club = _club(2, "Away FC")
        home_squad = _squad(1, stamina=6, fitness=60)   # will be exhausted
        away_squad = _squad(100, stamina=15, fitness=92)
        ht, at = _tactics(home_squad), _tactics(away_squad)

        offsets = {pid: 70 for pid in ht.starting_xi}
        result = simulate_match(home_club, away_club, home_squad, away_squad,
                                ht, at, minutes_played_offset=offsets)

        sub_events = [e for e in result.events
                      if e.event_type == MatchEventType.SUBSTITUTION]
        home_subs = [e for e in sub_events if e.club_id == home_club.id]

        # The exhausted home side should react at least once across seeds;
        # run a few seeds so a single unlucky stream can't fail the suite.
        total_home_subs = len(home_subs)
        for seed in range(1, 8):
            rng.seed(seed * 13)
            r = simulate_match(home_club, away_club, home_squad, away_squad,
                               ht, at, minutes_played_offset=offsets)
            total_home_subs += sum(
                1 for e in r.events
                if e.event_type == MatchEventType.SUBSTITUTION
                and e.club_id == home_club.id)

        assert total_home_subs >= 3, f"only {total_home_subs} AI subs in 8 sims"
        assert len(sub_events) <= 6  # both teams hard-capped at 3 each

    def test_fresh_side_may_skip_subs(self):
        """A fresh dominant side has no reason to burn substitutions."""
        rng.seed(9)
        home_club = _club(1, "Fresh FC")
        away_club = _club(2, "Tired FC")
        home_squad = _squad(1, stamina=17, fitness=95)
        away_squad = _squad(100, stamina=17, fitness=95)
        ht, at = _tactics(home_squad), _tactics(away_squad)

        result = simulate_match(home_club, away_club, home_squad, away_squad,
                                ht, at)  # no offsets → nobody tired early
        subs = [e for e in result.events
                if e.event_type == MatchEventType.SUBSTITUTION]
        assert all(e.minute > 55 for e in subs)  # never before fatigue bites


# ── 2. Loan obligations ─────────────────────────────────────────────────────

class TestLoanObligation:
    def _setup_db(self):
        tmp = Path(tempfile.mkdtemp())
        self._db = __import__("src.data.database", fromlist=["database"])
        self._db.close()                      # drop any cached connection
        self._db._DEFAULT_DB_DIR = tmp
        return self._db.connect("loan_test")

    _PLAYER_COLS = ("id, name, age, nationality, governorate, position, "
                    "preferred_foot, current_ability, potential_ability, "
                    "club_id")

    def test_obligation_triggers_permanent_transfer(self):
        conn = self._setup_db()

        # Two clubs with distinct balances
        conn.execute("INSERT INTO clubs (id, name, short_name, balance) "
                     "VALUES (1, 'Parent SC', 'PAR', 1000000)")
        conn.execute("INSERT INTO clubs (id, name, short_name, balance) "
                     "VALUES (2, 'Buyer FC', 'BUY', 5000000)")

        # One player loaned out with an obligation fee
        conn.execute(f"""
            INSERT INTO players ({self._PLAYER_COLS})
            VALUES (42, 'Wonder Kid', 25, 'Egyptian', 'Cairo', 'ST',
                    'Right', 120, 150, 2)
        """)
        yesterday = (date(2026, 5, 1) - timedelta(days=1)).isoformat()
        conn.execute("""
            INSERT INTO loan_deals (player_id, player_name, from_club_id,
                from_club_name, to_club_id, to_club_name, start_date,
                end_date, wage_split, buy_option, status)
            VALUES (42, 'Wonder Kid', 1, 'Parent SC', 2, 'Buyer FC',
                    '2025-09-01', ?, 50, 750000, 'active')
        """, (yesterday,))
        conn.commit()

        gs = GameState(manager_name="Tester")
        gs.current_date = date(2026, 5, 1)
        msgs = process_loan_returns(conn, gs)

        club_id = conn.execute(
            "SELECT club_id FROM players WHERE id=42").fetchone()[0]
        assert club_id == 2, "obligation did not make transfer permanent"

        status = conn.execute(
            "SELECT status FROM loan_deals WHERE player_id=42").fetchone()[0]
        assert status == "completed_buy"

        hist = conn.execute(
            "SELECT fee, transfer_type FROM transfer_history "
            "WHERE player_id=42").fetchone()
        assert hist and hist[0] == 750000 and hist[1] == "loan_obligation"

        buyer_bal = conn.execute(
            "SELECT balance FROM clubs WHERE id=2").fetchone()[0]
        parent_bal = conn.execute(
            "SELECT balance FROM clubs WHERE id=1").fetchone()[0]
        assert buyer_bal == 5000000 - 750000
        assert parent_bal == 1000000 + 750000

        assert any("Obligation" in m for m in msgs)

    def test_broke_borrower_returns_player(self):
        conn = self._setup_db()
        conn.execute("INSERT INTO clubs (id, name, short_name, balance) "
                     "VALUES (1, 'Rich SC', 'RIC', 9000000)")
        conn.execute("INSERT INTO clubs (id, name, short_name, balance) "
                     "VALUES (2, 'Broke FC', 'BRK', 1000)")
        conn.execute(f"""
            INSERT INTO players ({self._PLAYER_COLS})
            VALUES (43, 'Star Man', 25, 'Egyptian', 'Cairo', 'CAM',
                    'Right', 130, 160, 2)
        """)
        yesterday = "2026-04-30"
        conn.execute("""
            INSERT INTO loan_deals (player_id, player_name, from_club_id,
                from_club_name, to_club_id, to_club_name, start_date,
                end_date, wage_split, buy_option, status)
            VALUES (43, 'Star Man', 1, 'Rich SC', 2, 'Broke FC',
                    '2025-09-01', ?, 50, 2000000, 'active')
        """, (yesterday,))
        conn.commit()

        gs = GameState(manager_name="Tester")
        gs.current_date = date(2026, 5, 1)
        process_loan_returns(conn, gs)

        club_id = conn.execute(
            "SELECT club_id FROM players WHERE id=43").fetchone()[0]
        assert club_id == 1, "broke borrower kept the player"
        status = conn.execute(
            "SELECT status FROM loan_deals WHERE player_id=43").fetchone()[0]
        assert status == "completed"


# ── 3. Scouting ─────────────────────────────────────────────────────────────

class TestScouting:
    def test_round_trip(self):
        tmp = Path(tempfile.mkdtemp())
        from src.data import database as db
        db._DEFAULT_DB_DIR = tmp
        conn = db.connect("scout_test")

        assert queries_is_scouted(conn, 77) is False
        queries_mark(conn, 77, date(2026, 3, 3))
        assert queries_is_scouted(conn, 77) is True
        assert queries_is_scouted(conn, 78) is False


def queries_is_scouted(conn, pid):
    from src.data import queries
    return queries.is_player_scouted(conn, pid)


def queries_mark(conn, pid, d):
    from src.data import queries
    queries.mark_player_scouted(conn, pid, d)


# ── 4. Development plans touch real stats (regression guard) ────────────────

class TestDevelopmentTouchesStats:
    def test_attributes_actually_grow(self):
        rng.seed(11)
        p = _player(9, "Prodigy", Position.LW, ca=110)
        p.age = 19
        p.dev_plan = "speedster"
        before = (p.attributes.pace, p.attributes.agility,
                  p.attributes.dribbling, p.current_ability)
        grew_notes = 0
        for _ in range(16):
            note = apply_weekly(p)
            if note and "improved" in note:
                grew_notes += 1
        after = (p.attributes.pace, p.attributes.agility,
                 p.attributes.dribbling, p.current_ability)
        assert after != before, "16 weeks of plan left attributes untouched"
        assert grew_notes >= 1
        assert p.current_ability > before[3]


def apply_weekly(p):
    from src.core.development import apply_weekly_development
    return apply_weekly_development(p)
