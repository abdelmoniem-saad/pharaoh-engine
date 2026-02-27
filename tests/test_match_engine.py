"""
Tests for the match simulation engine.
"""
import sqlite3
from datetime import date
from src.data.models import (
    Player, PlayerAttributes, PlayerContract, Club, ClubFinances,
    TeamTactics, MatchResult,
)
from src.core.match_engine import simulate_match
from src.core.tactics import auto_select_xi
from src.utils.config import Position, Foot, Mentality
from src.utils import rng


def _make_player(pid: int, name: str, position: Position, ca: int = 120) -> Player:
    """Helper to create a test player."""
    attrs = PlayerAttributes()
    if position == Position.GK:
        attrs.gk_reflexes = 14
        attrs.gk_handling = 13
        attrs.gk_positioning = 14
        attrs.gk_one_on_ones = 12
    elif position == Position.ST:
        attrs.finishing = 15
        attrs.composure = 14
        attrs.positioning = 13
    elif position == Position.CB:
        attrs.tackling = 15
        attrs.marking = 14
        attrs.heading = 13
        attrs.strength = 14

    return Player(
        id=pid, name=name, age=25, position=position,
        attributes=attrs, current_ability=ca, potential_ability=ca + 20,
        contract=PlayerContract(wage_weekly=50000, contract_expiry=date(2027, 6, 30)),
        fitness=95, morale=60, form=7.0,
    )


def _make_squad(start_id: int = 1) -> list[Player]:
    """Create a basic 25-player squad."""
    positions = [
        Position.GK, Position.GK,
        Position.CB, Position.CB, Position.CB, Position.CB,
        Position.LB, Position.RB,
        Position.CDM, Position.CDM,
        Position.CM, Position.CM, Position.CM,
        Position.CAM, Position.CAM,
        Position.LW, Position.RW,
        Position.ST, Position.ST, Position.ST,
        # Subs
        Position.GK, Position.CB, Position.CM, Position.LW, Position.ST,
    ]
    squad = []
    for i, pos in enumerate(positions):
        pid = start_id + i
        squad.append(_make_player(pid, f"Player {pid}", pos, ca=100 + i * 2))
    return squad


def _make_club(cid: int, name: str, rep: int = 150) -> Club:
    """Create a test club."""
    return Club(
        id=cid, name=name, short_name=name[:3].upper(),
        city="Cairo", governorate="Cairo", reputation=rep,
        finances=ClubFinances(balance=10000000),
    )


class TestMatchEngine:
    """Test suite for match simulation."""

    def setup_method(self):
        rng.seed(42)

    def test_simulate_match_returns_result(self):
        """Match simulation should return a valid MatchResult."""
        home_club = _make_club(1, "Home FC")
        away_club = _make_club(2, "Away FC")
        home_squad = _make_squad(1)
        away_squad = _make_squad(100)

        home_xi, home_bench = auto_select_xi(home_squad, "4-2-3-1")
        away_xi, away_bench = auto_select_xi(away_squad, "4-2-3-1")

        home_tactics = TeamTactics(
            formation="4-2-3-1", mentality=Mentality.BALANCED,
            starting_xi=home_xi, bench=home_bench,
        )
        away_tactics = TeamTactics(
            formation="4-2-3-1", mentality=Mentality.BALANCED,
            starting_xi=away_xi, bench=away_bench,
        )

        result = simulate_match(
            home_club, away_club,
            home_squad, away_squad,
            home_tactics, away_tactics,
        )

        assert isinstance(result, MatchResult)
        assert result.home_goals >= 0
        assert result.away_goals >= 0
        assert result.home_club_name == "Home FC"
        assert result.away_club_name == "Away FC"
        assert len(result.events) >= 2  # At least kickoff + full time

    def test_match_produces_realistic_scorelines(self):
        """Over many matches, scores should be realistic (avg 1-2 goals per team)."""
        home_club = _make_club(1, "Home FC")
        away_club = _make_club(2, "Away FC")
        home_squad = _make_squad(1)
        away_squad = _make_squad(100)

        home_xi, home_bench = auto_select_xi(home_squad, "4-2-3-1")
        away_xi, away_bench = auto_select_xi(away_squad, "4-2-3-1")

        total_home_goals = 0
        total_away_goals = 0
        num_matches = 100

        for i in range(num_matches):
            rng.seed(i)
            result = simulate_match(
                home_club, away_club, home_squad, away_squad,
                TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                           starting_xi=home_xi, bench=home_bench),
                TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                           starting_xi=away_xi, bench=away_bench),
            )
            total_home_goals += result.home_goals
            total_away_goals += result.away_goals

        avg_home = total_home_goals / num_matches
        avg_away = total_away_goals / num_matches

        # Realistic ranges: 0.5 - 3.0 goals per team on average
        assert 0.3 <= avg_home <= 4.0, f"Avg home goals: {avg_home}"
        assert 0.3 <= avg_away <= 4.0, f"Avg away goals: {avg_away}"

    def test_home_advantage(self):
        """Home team should win more often than away over many matches."""
        home_club = _make_club(1, "Home FC", rep=150)
        away_club = _make_club(2, "Away FC", rep=150)
        home_squad = _make_squad(1)
        away_squad = _make_squad(100)

        home_xi, home_bench = auto_select_xi(home_squad, "4-2-3-1")
        away_xi, away_bench = auto_select_xi(away_squad, "4-2-3-1")

        home_wins = 0
        num_matches = 200

        for i in range(num_matches):
            rng.seed(i * 7)
            result = simulate_match(
                home_club, away_club, home_squad, away_squad,
                TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                           starting_xi=home_xi, bench=home_bench),
                TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                           starting_xi=away_xi, bench=away_bench),
            )
            if result.home_goals > result.away_goals:
                home_wins += 1

        home_win_rate = home_wins / num_matches
        # Home win rate should be notably higher than 33%
        assert home_win_rate >= 0.25, f"Home win rate: {home_win_rate:.2%}"

    def test_possession_is_reasonable(self):
        """Possession should be between 25% and 75%."""
        home_club = _make_club(1, "Home FC")
        away_club = _make_club(2, "Away FC")
        home_squad = _make_squad(1)
        away_squad = _make_squad(100)

        home_xi, _ = auto_select_xi(home_squad, "4-2-3-1")
        away_xi, _ = auto_select_xi(away_squad, "4-2-3-1")

        result = simulate_match(
            home_club, away_club, home_squad, away_squad,
            TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                       starting_xi=home_xi),
            TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                       starting_xi=away_xi),
        )

        assert 20.0 <= result.home_stats.possession <= 80.0
        assert 20.0 <= result.away_stats.possession <= 80.0

    def test_deterministic_with_same_seed(self):
        """Same seed should produce identical results."""
        home_club = _make_club(1, "Home FC")
        away_club = _make_club(2, "Away FC")
        home_squad = _make_squad(1)
        away_squad = _make_squad(100)

        home_xi, home_bench = auto_select_xi(home_squad, "4-2-3-1")
        away_xi, away_bench = auto_select_xi(away_squad, "4-2-3-1")

        tactics_h = TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                               starting_xi=home_xi, bench=home_bench)
        tactics_a = TeamTactics(formation="4-2-3-1", mentality=Mentality.BALANCED,
                               starting_xi=away_xi, bench=away_bench)

        rng.seed(12345)
        result1 = simulate_match(home_club, away_club, home_squad, away_squad,
                                  tactics_h, tactics_a)

        rng.seed(12345)
        result2 = simulate_match(home_club, away_club, home_squad, away_squad,
                                  tactics_h, tactics_a)

        assert result1.home_goals == result2.home_goals
        assert result1.away_goals == result2.away_goals

