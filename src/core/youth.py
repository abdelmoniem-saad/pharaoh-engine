"""
Youth development pipeline — academy system and player progression.

Phase 2 module — stub implementation for MVP with core growth logic.
"""
from __future__ import annotations

from src.data.models import Player, Club
from src.utils import rng
from src.utils.config import ATTR_MIN, ATTR_MAX


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
        # Pick a random attribute to improve
        attr_names = [
            "finishing", "passing", "dribbling", "first_touch", "crossing",
            "heading", "pace", "stamina", "strength", "agility",
            "composure", "vision", "work_rate", "positioning", "decisions",
        ]
        attr_to_grow = rng.choice(attr_names)
        current_val = getattr(player.attributes, attr_to_grow)

        if current_val < ATTR_MAX:
            setattr(player.attributes, attr_to_grow, current_val + 1)
            player.current_ability = min(player.potential_ability,
                                          player.current_ability + 1)
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


def generate_youth_player(club: Club) -> Player:
    """Generate a new youth academy player. Placeholder for Phase 2."""
    from src.data.seed import _generate_player
    from src.utils.config import Position

    positions = [Position.GK, Position.CB, Position.CM, Position.ST,
                 Position.LW, Position.RW, Position.LB, Position.RB]
    pos = rng.choice(positions)

    player = _generate_player(
        position=pos,
        club_rep=club.reputation,
        governorate=club.governorate,
        shirt_number=rng.randint(30, 99),
    )
    player.age = rng.randint(16, 18)
    player.club_id = club.id
    return player

