"""
Player logic — overall rating calculation, position suitability, form tracking.
"""
from __future__ import annotations

from src.data.models import Player, PlayerAttributes
from src.utils.config import Position, PositionGroup, POSITION_GROUP_MAP
from src.utils.rng import weighted_average, clamp


def calculate_overall_rating(player: Player) -> int:
    """Calculate a player's overall rating (1-99) from attributes and CA, weighted by position."""
    a = player.attributes
    pos = player.position

    if pos == Position.GK:
        attr_score = weighted_average(
            [a.gk_reflexes, a.gk_handling, a.gk_positioning, a.gk_one_on_ones, a.gk_kicking, a.composure, a.strength],
            [25, 20, 20, 15, 5, 10, 5]
        )
    elif pos == Position.CB:
        attr_score = weighted_average(
            [a.tackling, a.marking, a.heading, a.strength, a.positioning, a.composure, a.jumping, a.pace],
            [20, 15, 15, 12, 12, 10, 10, 6]
        )
    elif pos in (Position.LB, Position.RB):
        attr_score = weighted_average(
            [a.tackling, a.crossing, a.pace, a.stamina, a.marking, a.passing, a.work_rate, a.agility],
            [18, 15, 15, 12, 12, 10, 10, 8]
        )
    elif pos == Position.CDM:
        attr_score = weighted_average(
            [a.tackling, a.passing, a.positioning, a.stamina, a.work_rate, a.strength, a.vision, a.composure],
            [20, 15, 15, 12, 12, 10, 8, 8]
        )
    elif pos == Position.CM:
        attr_score = weighted_average(
            [a.passing, a.vision, a.stamina, a.first_touch, a.work_rate, a.composure, a.tackling, a.dribbling],
            [20, 15, 12, 12, 10, 10, 10, 11]
        )
    elif pos == Position.CAM:
        attr_score = weighted_average(
            [a.vision, a.passing, a.dribbling, a.first_touch, a.finishing, a.composure, a.long_shots, a.agility],
            [18, 16, 14, 12, 12, 10, 10, 8]
        )
    elif pos in (Position.LW, Position.RW, Position.LM, Position.RM):
        attr_score = weighted_average(
            [a.pace, a.dribbling, a.crossing, a.agility, a.finishing, a.first_touch, a.stamina, a.passing],
            [18, 16, 14, 12, 12, 10, 10, 8]
        )
    elif pos == Position.ST:
        attr_score = weighted_average(
            [a.finishing, a.composure, a.positioning, a.heading, a.dribbling, a.pace, a.first_touch, a.strength],
            [22, 15, 14, 10, 10, 10, 10, 9]
        )
    else:
        all_attrs = [a.finishing, a.passing, a.dribbling, a.first_touch, a.crossing, a.heading,
                     a.pace, a.stamina, a.strength, a.composure, a.vision, a.work_rate]
        attr_score = sum(all_attrs) / len(all_attrs)

    attr_ovr = (attr_score / 20.0) * 99.0
    ca_ovr = (player.current_ability / 200.0) * 99.0
    overall = (attr_ovr * 0.6 + ca_ovr * 0.4)
    return int(clamp(round(overall), 1, 99))


def position_suitability(player: Player, target_position: Position) -> float:
    """Calculate how well a player can play in a target position (0.0 to 1.0)."""
    if player.position == target_position:
        return 1.0
    if target_position in player.secondary_positions:
        return 0.85
    player_group = POSITION_GROUP_MAP.get(player.position)
    target_group = POSITION_GROUP_MAP.get(target_position)
    if player_group == target_group:
        return 0.65
    adjacent = {
        PositionGroup.DEFENDER: {PositionGroup.MIDFIELDER: 0.4},
        PositionGroup.MIDFIELDER: {PositionGroup.DEFENDER: 0.4, PositionGroup.ATTACKER: 0.4},
        PositionGroup.ATTACKER: {PositionGroup.MIDFIELDER: 0.4},
        PositionGroup.GOALKEEPER: {},
    }
    if target_group in adjacent.get(player_group, {}):
        return adjacent[player_group][target_group]
    return 0.2


def effective_ability(player: Player, target_position: Position) -> int:
    """Get a player's effective ability for a target position."""
    suit = position_suitability(player, target_position)
    return int(player.current_ability * suit)


def update_form(player: Player, match_rating: float) -> None:
    """Update a player's rolling form after a match (EMA alpha=0.3)."""
    alpha = 0.3
    player.form = round(alpha * match_rating + (1 - alpha) * player.form, 1)
    player.form = clamp(player.form, 0.0, 10.0)


def update_fitness_after_match(player: Player, minutes_played: int) -> None:
    """Reduce fitness based on minutes played."""
    fatigue = (minutes_played / 90.0) * (8 + (20 - player.attributes.stamina) * 0.3)
    player.fitness = int(clamp(player.fitness - fatigue, 0, 100))


def rest_recovery(player: Player, days: int = 1) -> None:
    """Recover fitness over rest days."""
    recovery_per_day = 5 + (player.attributes.stamina / 10.0)
    player.fitness = int(clamp(player.fitness + recovery_per_day * days, 0, 100))


def get_match_readiness(player: Player) -> float:
    """Get overall match readiness (0.0 to 1.0) from fitness, morale, form."""
    fitness_factor = player.fitness / 100.0
    morale_factor = player.morale / 100.0
    form_factor = player.form / 10.0
    return fitness_factor * 0.5 + morale_factor * 0.25 + form_factor * 0.25


def update_morale(player: Player, result_type: str, rating: float = 6.5,
                   played: bool = True, was_dropped: bool = False) -> None:
    """
    Update player morale after a match.

    result_type: 'win', 'draw', 'loss'
    rating: individual match rating (1-10)
    played: whether the player was in the starting XI
    was_dropped: True if player started last game but is benched this game
    """
    change = 0

    # Team result
    if result_type == "win":
        change += 3
    elif result_type == "draw":
        change += 0
    else:
        change -= 3

    if played:
        # Good personal rating boost
        if rating >= 7.5:
            change += 2
        elif rating >= 7.0:
            change += 1
        elif rating < 5.5:
            change -= 2
        # Reset bench streak
        player.matches_benched_streak = 0
        # Captain gets extra morale lift from wins
        if player.is_captain and result_type == "win":
            change += 1
    else:
        # Not selected
        change -= 1
        player.matches_benched_streak += 1
        # Dropped from last game's XI is extra painful
        if was_dropped:
            change -= 2
        # Prolonged benchwarming makes players unhappy
        if player.matches_benched_streak >= 3:
            change -= 1
        if player.matches_benched_streak >= 5:
            change -= 1

    player.morale = int(clamp(player.morale + change, 0, 100))


def get_morale_description(player: Player) -> str:
    """Get a human-readable morale description with reason."""
    m = player.morale
    if m >= 85:
        desc = "Ecstatic"
    elif m >= 70:
        desc = "Happy"
    elif m >= 55:
        desc = "Content"
    elif m >= 40:
        desc = "Unsettled"
    elif m >= 25:
        desc = "Unhappy"
    else:
        desc = "Furious"

    reasons = []
    if player.matches_benched_streak >= 5:
        reasons.append("wants to leave — no playing time")
    elif player.matches_benched_streak >= 3:
        reasons.append("wants more playing time")
    if player.injury_days_remaining > 0:
        reasons.append(f"injured ({player.injury_type})")
    if player.suspension_matches > 0:
        reasons.append("suspended")

    if reasons:
        return f"{desc} — {', '.join(reasons)}"
    return desc


