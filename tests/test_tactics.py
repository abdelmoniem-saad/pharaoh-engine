"""
Tests for the tactics module.
"""
from datetime import date
from src.data.models import Player, PlayerAttributes, PlayerContract, TeamTactics
from src.core.tactics import (
    auto_select_xi, get_available_formations, get_formation_positions,
    get_preset, preset_to_tactics, PRESETS, calculate_team_strength,
)
from src.utils.config import Position, Mentality
from src.utils import rng


def _make_squad() -> list[Player]:
    """Create a 25-player test squad."""
    positions = [
        Position.GK, Position.GK, Position.GK,
        Position.CB, Position.CB, Position.CB, Position.CB,
        Position.LB, Position.LB,
        Position.RB, Position.RB,
        Position.CDM, Position.CDM,
        Position.CM, Position.CM, Position.CM,
        Position.CAM, Position.CAM,
        Position.LW, Position.RW,
        Position.ST, Position.ST, Position.ST,
        Position.LW, Position.RW,
    ]
    squad = []
    for i, pos in enumerate(positions):
        squad.append(Player(
            id=i + 1, name=f"Player {i + 1}", age=25,
            position=pos, current_ability=100 + i,
            potential_ability=120 + i,
            attributes=PlayerAttributes(
                finishing=10 + (i % 5), passing=10 + (i % 4),
                dribbling=10 + (i % 3), tackling=10 + (i % 5),
                pace=10 + (i % 4), stamina=12,
                gk_reflexes=14 if pos == Position.GK else 3,
                gk_handling=13 if pos == Position.GK else 3,
                gk_positioning=13 if pos == Position.GK else 3,
                gk_one_on_ones=12 if pos == Position.GK else 3,
            ),
            fitness=95, morale=60, form=7.0,
            contract=PlayerContract(wage_weekly=50000),
        ))
    return squad


class TestTactics:
    def setup_method(self):
        rng.seed(42)

    def test_available_formations(self):
        formations = get_available_formations()
        assert len(formations) >= 5
        assert "4-2-3-1" in formations
        assert "4-4-2" in formations
        assert "4-3-3" in formations

    def test_formation_positions_correct_length(self):
        for formation in get_available_formations():
            positions = get_formation_positions(formation)
            assert len(positions) == 11, f"{formation} has {len(positions)} positions"

    def test_all_formations_start_with_gk(self):
        for formation in get_available_formations():
            positions = get_formation_positions(formation)
            assert positions[0] == Position.GK

    def test_auto_select_xi_returns_11(self):
        squad = _make_squad()
        xi, bench = auto_select_xi(squad, "4-2-3-1")
        assert len(xi) == 11

    def test_auto_select_xi_no_duplicates(self):
        squad = _make_squad()
        xi, bench = auto_select_xi(squad, "4-2-3-1")
        assert len(set(xi)) == len(xi)

    def test_bench_does_not_overlap_xi(self):
        squad = _make_squad()
        xi, bench = auto_select_xi(squad, "4-2-3-1")
        assert not set(xi) & set(bench)

    def test_presets_exist(self):
        assert len(PRESETS) >= 4
        for key, preset in PRESETS.items():
            assert preset.name
            assert preset.formation in get_available_formations()

    def test_preset_to_tactics(self):
        preset = get_preset("balanced")
        tactics = preset_to_tactics(preset)
        assert isinstance(tactics, TeamTactics)
        assert tactics.formation == preset.formation
        assert tactics.mentality == preset.mentality

    def test_team_strength_calculation(self):
        squad = _make_squad()
        xi, bench = auto_select_xi(squad, "4-2-3-1")
        tactics = TeamTactics(
            formation="4-2-3-1", mentality=Mentality.BALANCED,
            starting_xi=xi, bench=bench,
        )
        strength = calculate_team_strength(squad, tactics)
        assert "attack" in strength
        assert "midfield" in strength
        assert "defense" in strength
        assert "overall" in strength
        assert all(v >= 0 for v in strength.values())

