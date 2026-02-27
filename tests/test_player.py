"""
Tests for player module — ratings, suitability, form, fitness.
"""
from datetime import date
from src.data.models import Player, PlayerAttributes, PlayerContract
from src.core.player import (
    calculate_overall_rating, position_suitability, effective_ability,
    update_form, update_fitness_after_match, rest_recovery, get_match_readiness,
)
from src.utils.config import Position


def _make_striker(ca: int = 140) -> Player:
    return Player(
        id=1, name="Test Striker", age=26,
        position=Position.ST,
        attributes=PlayerAttributes(
            finishing=17, composure=15, positioning=14,
            heading=12, dribbling=13, pace=14,
            first_touch=13, strength=12,
        ),
        current_ability=ca, potential_ability=ca + 20,
        contract=PlayerContract(wage_weekly=100000, contract_expiry=date(2028, 6, 30)),
        fitness=100, morale=70, form=7.5,
    )


def _make_goalkeeper(ca: int = 130) -> Player:
    return Player(
        id=2, name="Test GK", age=28,
        position=Position.GK,
        attributes=PlayerAttributes(
            gk_reflexes=16, gk_handling=15,
            gk_positioning=14, gk_one_on_ones=13, gk_kicking=11,
            composure=13, strength=12,
        ),
        current_ability=ca, potential_ability=ca + 10,
        fitness=100, morale=60, form=7.0,
    )


class TestPlayerRating:
    def test_striker_overall_is_reasonable(self):
        player = _make_striker(140)
        ovr = calculate_overall_rating(player)
        assert 40 <= ovr <= 99

    def test_goalkeeper_overall_is_reasonable(self):
        player = _make_goalkeeper(130)
        ovr = calculate_overall_rating(player)
        assert 40 <= ovr <= 99

    def test_higher_ca_gives_higher_rating(self):
        low = _make_striker(80)
        high = _make_striker(180)
        assert calculate_overall_rating(high) > calculate_overall_rating(low)


class TestPositionSuitability:
    def test_natural_position_is_1(self):
        player = _make_striker()
        assert position_suitability(player, Position.ST) == 1.0

    def test_same_group_partial(self):
        player = _make_striker()
        suit = position_suitability(player, Position.LW)
        assert 0.5 <= suit <= 0.9

    def test_goalkeeper_out_of_position(self):
        player = _make_goalkeeper()
        suit = position_suitability(player, Position.ST)
        assert suit <= 0.3

    def test_effective_ability_scales(self):
        player = _make_striker(100)
        natural = effective_ability(player, Position.ST)
        out_of_pos = effective_ability(player, Position.GK)
        assert natural > out_of_pos


class TestFormAndFitness:
    def test_form_updates_with_ema(self):
        player = _make_striker()
        original_form = player.form
        update_form(player, 9.0)
        assert player.form > original_form

    def test_form_decreases_after_bad_match(self):
        player = _make_striker()
        player.form = 7.5
        update_form(player, 4.0)
        assert player.form < 7.5

    def test_fitness_decreases_after_match(self):
        player = _make_striker()
        player.fitness = 100
        update_fitness_after_match(player, 90)
        assert player.fitness < 100

    def test_rest_recovery(self):
        player = _make_striker()
        player.fitness = 70
        rest_recovery(player, days=2)
        assert player.fitness > 70

    def test_match_readiness(self):
        player = _make_striker()
        player.fitness = 100
        player.morale = 80
        player.form = 8.0
        readiness = get_match_readiness(player)
        assert 0.5 <= readiness <= 1.0

