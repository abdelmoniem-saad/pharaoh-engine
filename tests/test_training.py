"""
Tests for the training system.
"""
import pytest
from src.data.models import Player, PlayerAttributes, Club, ClubFinances
from src.core.training import (
    process_weekly_training, TrainingIntensity,
    get_training_programs, get_recommended_focus,
)
from src.utils.config import Position, Foot
from src.utils import rng


def _make_player(age=20, ca=100, pa=160, position=Position.ST,
                 training_focus="Shooting", fitness=100):
    return Player(
        id=1, name="Test Player", age=age, position=position,
        preferred_foot=Foot.RIGHT,
        attributes=PlayerAttributes(
            finishing=10, passing=10, dribbling=10, first_touch=10,
            crossing=10, heading=10, long_shots=10, tackling=10,
            marking=10, free_kicks=10, pace=10, stamina=10,
            strength=10, agility=10, jumping=10, composure=10,
            vision=10, work_rate=10, leadership=10, aggression=10,
            positioning=10, decisions=10,
        ),
        current_ability=ca, potential_ability=pa,
        fitness=fitness, training_focus=training_focus,
    )


def _make_club(facilities=5):
    return Club(
        id=1, name="Test FC", short_name="TST",
        city="Cairo", governorate="Cairo",
        facilities_level=facilities, reputation=100,
        finances=ClubFinances(),
    )


class TestTraining:
    def test_training_programs_available(self):
        programs = get_training_programs()
        assert len(programs) >= 5
        assert "Shooting" in programs
        assert "Defending" in programs
        assert "Goalkeeping" in programs

    def test_recommended_focus_by_position(self):
        player_st = _make_player(position=Position.ST)
        assert get_recommended_focus(player_st) == "Shooting"

        player_cb = _make_player(position=Position.CB)
        assert get_recommended_focus(player_cb) == "Defending"

        player_gk = _make_player(position=Position.GK)
        assert get_recommended_focus(player_gk) == "Goalkeeping"

    def test_young_player_can_develop(self):
        rng.seed(42)
        player = _make_player(age=18, ca=80, pa=180)
        club = _make_club(facilities=8)

        total_improvements = 0
        for _ in range(100):
            msgs = process_weekly_training(player, club)
            total_improvements += len([m for m in msgs if "📈" in m])

        assert total_improvements > 0, "Young player should develop over 100 weeks"

    def test_old_player_can_decline(self):
        rng.seed(42)
        player = _make_player(age=34, ca=150, pa=150)
        club = _make_club()

        total_declines = 0
        for _ in range(200):
            msgs = process_weekly_training(player, club)
            total_declines += len([m for m in msgs if "📉" in m])

        assert total_declines > 0, "Old player should decline over 200 weeks"

    def test_intense_training_costs_fitness(self):
        player = _make_player(fitness=100)
        club = _make_club()
        process_weekly_training(player, club, TrainingIntensity.INTENSE)
        assert player.fitness < 100

    def test_light_training_no_fitness_cost(self):
        player = _make_player(fitness=100)
        club = _make_club()
        process_weekly_training(player, club, TrainingIntensity.LIGHT)
        assert player.fitness == 100

    def test_injured_player_no_development(self):
        player = _make_player(age=18, ca=80, pa=180)
        player.injury_days_remaining = 10
        club = _make_club()

        msgs = process_weekly_training(player, club)
        assert len(msgs) == 0

    def test_better_facilities_help(self):
        rng.seed(100)
        player_good = _make_player(age=18, ca=80, pa=180)
        club_good = _make_club(facilities=10)

        improvements_good = 0
        for _ in range(100):
            msgs = process_weekly_training(player_good, club_good)
            improvements_good += len([m for m in msgs if "📈" in m])

        rng.seed(100)
        player_bad = _make_player(age=18, ca=80, pa=180)
        club_bad = _make_club(facilities=1)

        improvements_bad = 0
        for _ in range(100):
            msgs = process_weekly_training(player_bad, club_bad)
            improvements_bad += len([m for m in msgs if "📈" in m])

        assert improvements_good >= improvements_bad



