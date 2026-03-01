"""
Training system — structured weekly training with intensity, focus areas,
and real impact on player development.
"""
from __future__ import annotations

from enum import Enum

from src.data.models import Player, Club
from src.utils import rng
from src.utils.config import ATTR_MIN, ATTR_MAX


class TrainingIntensity(str, Enum):
    LIGHT = "Light"
    NORMAL = "Normal"
    INTENSE = "Intense"
    DOUBLE = "Double Sessions"


# Intensity → (growth_mult, fitness_cost, injury_risk_mult)
INTENSITY_EFFECTS: dict[TrainingIntensity, tuple[float, int, float]] = {
    TrainingIntensity.LIGHT:  (0.5,  0, 0.002),
    TrainingIntensity.NORMAL: (1.0,  0, 0.005),
    TrainingIntensity.INTENSE: (1.6, -3, 0.012),
    TrainingIntensity.DOUBLE: (2.2, -5, 0.020),
}

# Training focus → list of attributes it improves
TRAINING_PROGRAMS = {
    "Shooting":    ["finishing", "long_shots", "composure"],
    "Defending":   ["tackling", "marking", "positioning"],
    "Physical":    ["pace", "stamina", "strength", "agility"],
    "Playmaking":  ["passing", "vision", "first_touch", "crossing"],
    "Mental":      ["decisions", "composure", "work_rate", "leadership"],
    "Goalkeeping": ["gk_reflexes", "gk_handling", "gk_positioning", "gk_one_on_ones"],
    "Set Pieces":  ["free_kicks", "crossing", "heading"],
    "Balanced":    ["finishing", "passing", "tackling", "pace", "composure"],
}


def process_weekly_training(player: Player, club: Club,
                            intensity: TrainingIntensity = TrainingIntensity.NORMAL
                            ) -> list[str]:
    """
    Process one week of training for a player.

    Returns messages about what happened (attribute gains, injuries, etc.).
    """
    messages: list[str] = []
    focus = player.training_focus or "Balanced"
    growth_mult, fitness_cost, injury_risk = INTENSITY_EFFECTS[intensity]

    # Apply fitness cost from intense training
    if fitness_cost:
        player.fitness = max(0, player.fitness + fitness_cost)

    # Injury risk from training
    if rng.chance(injury_risk):
        inj_type = rng.choice(["Hamstring", "Calf", "Ankle", "Knee"])
        inj_days = rng.randint(3, 14)
        player.injury_days_remaining = inj_days
        player.injury_type = inj_type
        player.fitness = max(0, player.fitness - 20)
        messages.append(
            f"🏥 {player.name} picked up a {inj_type.lower()} injury in training! "
            f"Out for {inj_days} days."
        )
        return messages  # No development this week if injured

    # Skip development if injured
    if player.injury_days_remaining > 0:
        return messages

    # ── Growth calculation ──────────────────────────────────────────
    ca_gap = player.potential_ability - player.current_ability

    # Young players grow faster
    if player.age <= 20:
        age_mult = 1.8
    elif player.age <= 23:
        age_mult = 1.3
    elif player.age <= 27:
        age_mult = 0.8
    elif player.age <= 30:
        age_mult = 0.4
    else:
        age_mult = 0.1

    # Facility bonus
    facility_mult = 0.5 + (club.facilities_level / 10.0) * 0.8

    # Base growth chance
    base_chance = max(0.02, min(0.40, ca_gap / 150.0))
    growth_chance = base_chance * age_mult * facility_mult * growth_mult

    if rng.chance(growth_chance):
        # Pick attribute to improve
        focus_attrs = TRAINING_PROGRAMS.get(focus, TRAINING_PROGRAMS["Balanced"])

        if rng.chance(0.75):
            # 75% chance to improve a focused attribute
            attr_name = rng.choice(focus_attrs)
        else:
            # 25% chance for a random attribute
            all_attrs = [
                "finishing", "passing", "dribbling", "first_touch", "crossing",
                "heading", "pace", "stamina", "strength", "agility",
                "composure", "vision", "work_rate", "positioning", "decisions",
            ]
            attr_name = rng.choice(all_attrs)

        current_val = getattr(player.attributes, attr_name, ATTR_MAX)
        if current_val < ATTR_MAX:
            setattr(player.attributes, attr_name, current_val + 1)
            player.current_ability = min(player.potential_ability,
                                         player.current_ability + 1)
            messages.append(f"📈 {player.name}: {attr_name} +1 (now {current_val + 1})")

    # ── Older player decline ────────────────────────────────────────
    if player.age >= 32:
        decline_chance = 0.03 * (player.age - 31)
        if rng.chance(decline_chance):
            physical_attrs = ["pace", "stamina", "agility", "jumping"]
            attr_name = rng.choice(physical_attrs)
            current_val = getattr(player.attributes, attr_name, ATTR_MIN)
            if current_val > ATTR_MIN:
                setattr(player.attributes, attr_name, current_val - 1)
                player.current_ability = max(1, player.current_ability - 1)
                messages.append(f"📉 {player.name}: {attr_name} -1 (age decline)")

    return messages


def get_training_programs() -> list[str]:
    """Return available training focus areas."""
    return list(TRAINING_PROGRAMS.keys())


def get_recommended_focus(player: Player) -> str:
    """Recommend a training focus based on the player's position."""
    from src.utils.config import Position
    recommendations = {
        Position.GK: "Goalkeeping",
        Position.CB: "Defending",
        Position.LB: "Physical",
        Position.RB: "Physical",
        Position.CDM: "Defending",
        Position.CM: "Playmaking",
        Position.CAM: "Playmaking",
        Position.LW: "Shooting",
        Position.RW: "Shooting",
        Position.LM: "Playmaking",
        Position.RM: "Playmaking",
        Position.ST: "Shooting",
    }
    return recommendations.get(player.position, "Balanced")



