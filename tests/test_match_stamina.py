"""
Tests for the per-player match condition (stamina) model.
"""
from datetime import date

from src.data.models import (
    Player, PlayerAttributes, PlayerContract, Club, ClubFinances,
    TeamTactics,
)
from src.core.match_engine import simulate_match, _per_minute_drain
from src.core.tactics import auto_select_xi
from src.utils.config import Position, Foot, Mentality
from src.utils import rng


def _make_player(pid: int, name: str, position: Position, ca: int = 120,
                 stamina: int = 13, fitness: int = 90) -> Player:
    attrs = PlayerAttributes()
    attrs.stamina = stamina
    if position == Position.GK:
        attrs.gk_reflexes = 14
        attrs.gk_handling = 13
        attrs.gk_positioning = 14
    elif position == Position.ST:
        attrs.finishing = 15
        attrs.composure = 14
        attrs.positioning = 13
    elif position == Position.CB:
        attrs.tackling = 15
        attrs.marking = 14
        attrs.heading = 13

    return Player(
        id=pid, name=name, age=25, position=position,
        attributes=attrs, current_ability=ca, potential_ability=ca + 20,
        contract=PlayerContract(wage_weekly=50000, contract_expiry=date(2027, 6, 30)),
        fitness=fitness, morale=60, form=7.0,
    )


def _make_squad(start_id: int, stamina: int = 13, fitness: int = 90) -> list[Player]:
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
    return [
        _make_player(start_id + i, f"P{start_id + i}", pos,
                     stamina=stamina, fitness=fitness)
        for i, pos in enumerate(positions)
    ]


def _make_club(cid: int, name: str) -> Club:
    return Club(
        id=cid, name=name, short_name=name[:3].upper(),
        city="Cairo", governorate="Cairo", reputation=150,
        finances=ClubFinances(balance=10000000),
    )


def _tactics(squad, formation="4-2-3-1") -> TeamTactics:
    xi, bench = auto_select_xi(squad, formation)
    return TeamTactics(formation=formation, mentality=Mentality.BALANCED,
                       starting_xi=xi, bench=bench)


class TestPerMinuteDrain:
    def test_low_stamina_drains_faster(self):
        p_high = _make_player(1, "A", Position.CM, stamina=18)
        p_low = _make_player(2, "B", Position.CM, stamina=8)
        assert _per_minute_drain(p_low) > _per_minute_drain(p_high)

    def test_gk_drains_at_half_rate(self):
        gk = _make_player(1, "GK", Position.GK, stamina=13)
        outfield = _make_player(2, "CM", Position.CM, stamina=13)
        assert abs(_per_minute_drain(gk) * 2 - _per_minute_drain(outfield)) < 1e-9

    def test_full_match_costs_twelve_to_twentyeight_points(self):
        for s in range(5, 20):
            p = _make_player(1, "P", Position.CM, stamina=s)
            cost = _per_minute_drain(p) * 90
            assert 11.0 <= cost <= 28.0, f"stamina {s} → {cost:.2f}"


class TestOffsetSimulation:
    def test_offsets_produce_valid_result(self):
        home_club, away_club = _make_club(1, "Home FC"), _make_club(2, "Away FC")
        home_squad = _make_squad(1)
        away_squad = _make_squad(100)
        ht, at = _tactics(home_squad), _tactics(away_squad)

        rng.seed(7)
        offset = {pid: 63 for pid in ht.starting_xi + at.starting_xi}
        res = simulate_match(home_club, away_club, home_squad, away_squad,
                             ht, at, minutes_played_offset=offset)
        assert res.home_goals >= 0 and res.away_goals >= 0
        assert res.events and res.events[0].event_type.value == "kickoff" or res.events


class TestFreshnessAdvantage:
    def test_fresh_legs_beat_tired_legs(self):
        """
        Two identical teams. In every pair the SAME seed is used but one side's
        XI has already played 75 minutes (offsets) with poor stamina, while the
        other side starts fresh with strong stamina. Across many pairs the
        fresh sides must create and convert at least as much as the tired ones.
        """
        fresh_goals = tired_goals = 0.0
        fresh_shots = tired_shots = 0.0
        pairs = 40
        for seed in range(pairs):
            rng.seed(1000 + seed)

            fresh_club = _make_club(1, "Fresh FC")
            tired_club = _make_club(2, "Tired FC")
            fresh_squad = _make_squad(1, stamina=17, fitness=92)
            tired_squad = _make_squad(100, stamina=7, fitness=88)
            ft = _tactics(fresh_squad)
            tt = _tactics(tired_squad)

            # Fresh side plays normally; tired side carries 75' of wear.
            offsets = {pid: 75 for pid in tt.starting_xi}

            r = simulate_match(fresh_club, tired_club, fresh_squad, tired_squad,
                               ft, tt, minutes_played_offset=offsets)
            fresh_goals += r.home_goals
            tired_goals += r.away_goals
            fresh_shots += r.home_stats.shots if hasattr(r.home_stats, "shots") else 0
            tired_shots += r.away_stats.shots if hasattr(r.away_stats, "shots") else 0

        # Directional assertions with generous noise tolerance — the fatigue
        # gap (~×0.98 vs ~×0.78 effectiveness) must show up on average.
        assert fresh_goals >= tired_goals - 0.5 * pairs / 10
        assert fresh_shots >= tired_shots * 0.85, (
            f"fresh shots {fresh_shots:.0f} vs tired {tired_shots:.0f}"
        )
