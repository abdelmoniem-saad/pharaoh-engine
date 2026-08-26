"""
Tests for long-term player development plans.
"""
from datetime import date

from src.data.models import (
    Player, PlayerAttributes, PlayerContract,
)
from src.core.development import apply_weekly_development, PLANS
from src.utils.config import Position
from src.utils import rng


def _player(pid=1, age=21, position=Position.LW, ca=110, pa=150):
    return Player(
        id=pid, name=f"P{pid}", age=age, position=position,
        attributes=PlayerAttributes(), current_ability=ca,
        potential_ability=pa,
        contract=PlayerContract(wage_weekly=50000,
                                contract_expiry=date(2027, 6, 30)),
    )


class TestWeeklyDevelopment:
    def test_no_plan_is_noop(self):
        p = _player()
        assert apply_weekly_development(p) is None
        assert p.dev_progress == 0

    def test_progress_advances_and_caps(self):
        rng.seed(3)
        p = _player()
        p.dev_plan = "engine"
        completed = False
        for _ in range(60):
            apply_weekly_development(p)
            assert 0 <= p.dev_progress <= 100
            if p.dev_plan == "":
                completed = True
                break
        assert completed, "engine plan should complete within 60 weeks"

    def test_conversion_changes_position_and_clears_plan(self):
        p = _player(position=Position.RW)
        p.dev_plan = "conv_st"
        p.dev_progress = 99  # one good week finishes it
        note = apply_weekly_development(p)
        assert p.position == Position.ST
        assert p.dev_plan == "" and p.dev_progress == 0
        assert note and ("Striker" in note or "retraining" in note)

    def test_attribute_plan_completion_clears(self):
        p = _player(position=Position.ST)
        p.dev_plan = "finisher"
        p.dev_progress = 100
        note = apply_weekly_development(p)
        assert p.dev_plan == ""
        assert note and "mastered" in note

    def test_youngsters_complete_plans_faster_than_veterans(self):
        """Cumulative weeks-to-completion: youth must beat veterans overall."""
        def weeks_to_complete(age: int) -> int:
            p = _player(pid=age, age=age)
            p.dev_plan = "speedster"
            for week in range(1, 61):
                apply_weekly_development(p)
                if p.dev_plan == "":
                    return week
            return 60

        young_weeks = sum(weeks_to_complete(a) for a in (17, 19, 21))
        vet_weeks = sum(weeks_to_complete(a) for a in (33, 35, 38))
        assert young_weeks < vet_weeks, (
            f"young {young_weeks}w should finish faster than veterans {vet_weeks}w"
        )

    def test_unknown_plan_key_is_safe(self):
        p = _player()
        p.dev_plan = "nonexistent"
        assert apply_weekly_development(p) is None

    def test_catalog_integrity(self):
        for key, spec in PLANS.items():
            assert "label" in spec and "focus" in spec
            conv = spec.get("conversion")
            if conv:
                from_set, target = conv
                assert isinstance(from_set, set) and len(from_set) > 0
                assert isinstance(target, Position)
