"""
Fan influence system — ultras culture, attendance, supporter morale.

Phase 3 module — stub with core attendance and happiness mechanics.
"""
from __future__ import annotations

from src.data.models import Club, MatchResult
from src.utils import rng
from src.utils.rng import clamp


def calculate_attendance(club: Club, is_home: bool,
                          opponent_reputation: int) -> int:
    """
    Calculate expected match attendance.

    Factors: stadium capacity, fan happiness, opponent reputation (big games draw more),
    recent form, weather (not yet implemented).
    """
    if not is_home:
        return 0  # Away attendance handled separately

    base = club.stadium_capacity * 0.5  # Base 50% fill

    # Fan happiness modifier (0-100 → 0.5x to 1.2x)
    happiness_mod = 0.5 + (club.fan_happiness / 100.0) * 0.7

    # Big game modifier (top clubs attract more fans)
    opponent_draw = min(1.5, opponent_reputation / 150.0)

    attendance = base * happiness_mod * opponent_draw

    # Add some randomness
    attendance *= rng.uniform(0.9, 1.1)

    return int(clamp(attendance, 500, club.stadium_capacity))


def update_fan_happiness(club: Club, result_type: str) -> None:
    """
    Update fan happiness after a match result.
    result_type: 'win', 'draw', 'loss'
    """
    changes = {"win": 3, "draw": -1, "loss": -5}
    change = changes.get(result_type, 0)

    # Fans of bigger clubs are more demanding
    if club.reputation >= 170 and result_type == "loss":
        change -= 3

    # Winning streak bonus
    if result_type == "win" and club.fan_happiness >= 70:
        change += 1

    club.fan_happiness = int(clamp(club.fan_happiness + change, 0, 100))


def get_atmosphere_description(fan_happiness: int) -> str:
    """Get a text description of the stadium atmosphere."""
    if fan_happiness >= 80:
        return "The fans are electric! The stadium is rocking!"
    elif fan_happiness >= 60:
        return "A positive atmosphere from the supporters."
    elif fan_happiness >= 40:
        return "The fans are cautiously optimistic."
    elif fan_happiness >= 20:
        return "Frustration is brewing among the supporters."
    else:
        return "The ultras are furious. Protests are expected."


def get_fan_happiness_level(happiness: int) -> str:
    """Convert numeric happiness to a named level."""
    if happiness >= 80:
        return "Ecstatic"
    elif happiness >= 60:
        return "Happy"
    elif happiness >= 40:
        return "Content"
    elif happiness >= 20:
        return "Unhappy"
    else:
        return "Furious"

