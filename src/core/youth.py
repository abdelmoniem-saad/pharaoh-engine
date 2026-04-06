"""
Youth development pipeline — academy system and player progression.

Phase 2 module — stub implementation for MVP with core growth logic.
"""

from __future__ import annotations

from src.data.models import Club, Player
from src.utils import rng
from src.utils.config import ATTR_MAX, ATTR_MIN, TRAINING_FOCUSES


def develop_player(player: Player, club: Club) -> list[str]:
    """
    Process weekly development for a player.
    Young players can grow, older players may decline.
    Returns messages about attribute changes.
    """
    messages = []

    if player.age <= 23:
        messages.extend(_grow_young_player(player, club))
    elif player.age >= 31:
        messages.extend(_age_decline(player))

    return messages


def _grow_young_player(player: Player, club: Club) -> list[str]:
    """Young player attribute growth based on potential gap and facilities."""
    messages = []
    ca_gap = player.potential_ability - player.current_ability

    if ca_gap <= 0:
        return messages

    # Growth chance increases with better facilities and larger CA/PA gap
    growth_chance = min(0.3, ca_gap / 200.0 + club.facilities_level / 50.0)

    if rng.chance(growth_chance):
        # Pick a random attribute to improve — biased by training focus
        all_attr_names = [
            "finishing",
            "passing",
            "dribbling",
            "first_touch",
            "crossing",
            "heading",
            "pace",
            "stamina",
            "strength",
            "agility",
            "composure",
            "vision",
            "work_rate",
            "positioning",
            "decisions",
        ]
        focus_attrs = TRAINING_FOCUSES.get(player.training_focus, [])
        if focus_attrs and rng.chance(0.70):
            # 70% chance to improve a focus attribute
            attr_to_grow = rng.choice(focus_attrs)
        else:
            attr_to_grow = rng.choice(all_attr_names)
        current_val = getattr(player.attributes, attr_to_grow)

        if current_val < ATTR_MAX:
            setattr(player.attributes, attr_to_grow, current_val + 1)
            player.current_ability = min(
                player.potential_ability, player.current_ability + 1
            )
            messages.append(f"{player.name}'s {attr_to_grow} has improved!")

    return messages


def _age_decline(player: Player) -> list[str]:
    """Older player attribute decline."""
    messages = []
    decline_chance = 0.02 * (player.age - 30)  # Higher chance with age

    if rng.chance(decline_chance):
        # Physical attributes decline first
        physical_attrs = ["pace", "stamina", "agility", "jumping"]
        attr_to_decline = rng.choice(physical_attrs)
        current_val = getattr(player.attributes, attr_to_decline)

        if current_val > ATTR_MIN:
            setattr(player.attributes, attr_to_decline, current_val - 1)
            player.current_ability = max(1, player.current_ability - 1)
            messages.append(f"{player.name}'s {attr_to_decline} has declined.")

    return messages


def get_academy_description(tier: int) -> str:
    """Return descriptive name for an academy tier (1-4)."""
    tiers = {
        1: "Elite Academy (World Class)",
        2: "Professional Academy (National)",
        3: "Basic Youth Setup (Regional)",
        4: "Minimal Facilities (Local)",
    }
    return tiers.get(tier, "Unknown Setup")


def generate_scouting_report(player: Player) -> str:
    """Generate a high-level scouting summary for a youth prospect."""
    # Star rating based on potential (with some "scout noise")
    noise = rng.randint(-5, 5)
    effective_pa = player.potential_ability + noise

    if effective_pa >= 165:
        stars = "⭐⭐⭐⭐⭐"
    elif effective_pa >= 145:
        stars = "⭐⭐⭐⭐"
    elif effective_pa >= 125:
        stars = "⭐⭐⭐"
    else:
        stars = "⭐⭐"

    strengths = []
    # Identify attributes > 12 as strengths for a youth player
    for attr in ["pace", "stamina", "finishing", "passing", "dribbling", "vision"]:
        if hasattr(player.attributes, attr) and getattr(player.attributes, attr) >= 13:
            strengths.append(attr.title())

    report = f"{player.name} ({player.position.name})\n"
    report += f"Estimated Potential: {stars}\n"
    if strengths:
        report += f"Key Strengths: {', '.join(strengths[:3])}"
    else:
        report += "General prospect with no standout skills yet."
    return report


def generate_youth_player(club: Club) -> Player:
    """Generate a new youth academy player based on club's academy tier."""
    from src.data.seed import _generate_player
    from src.utils.config import Position

    # Academy tier impact (Tier 1 = bonus, Tier 4 = penalty)
    tier_bonus = (4 - club.academy_tier) * 10

    positions = [
        Position.GK,
        Position.CB,
        Position.CM,
        Position.ST,
        Position.LW,
        Position.RW,
        Position.LB,
        Position.RB,
    ]
    pos = rng.choice(positions)

    player = _generate_player(
        position=pos,
        club_rep=club.reputation + tier_bonus,
        governorate=club.governorate,
        shirt_number=rng.randint(30, 99),
    )

    # Force age to be youth (16-18)
    player.age = rng.randint(16, 18)
    player.club_id = club.id

    # Academy tier also boosts PA floor
    pa_floor = 100 + (4 - club.academy_tier) * 15
    player.potential_ability = max(player.potential_ability, pa_floor)
    player.current_ability = min(player.current_ability, player.potential_ability - 10)

    return player
