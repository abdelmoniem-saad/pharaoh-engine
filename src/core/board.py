"""
Board politics — objectives, confidence, and pressure system.

Each club has a `season_expectation` derived from its reputation at the start
of each season.  The board judges performance against that expectation.
"""
from __future__ import annotations

from src.data.models import Club, BoardObjective
from src.utils.config import (
    BoardConfidence,
    SEASON_EXPECTATIONS,
    expectation_display,
    expectation_description,
    expectation_target_position,
)
from src.utils.rng import clamp


def get_confidence_level(confidence: int) -> BoardConfidence:
    """Convert numeric confidence (0-100) to a named level."""
    if confidence >= 90:
        return BoardConfidence.UNTOUCHABLE
    elif confidence >= 75:
        return BoardConfidence.SECURE
    elif confidence >= 55:
        return BoardConfidence.STABLE
    elif confidence >= 35:
        return BoardConfidence.UNCERTAIN
    elif confidence >= 15:
        return BoardConfidence.UNDER_PRESSURE
    else:
        return BoardConfidence.ON_THE_BRINK


def update_confidence_after_match(club: Club, result_type: str) -> None:
    """
    Update board confidence after a match result.
    result_type: 'win', 'draw', 'loss'
    """
    change = {"win": 2, "draw": 0, "loss": -3}.get(result_type, 0)

    # Higher-expectation clubs have less patience with losses
    if club.season_expectation in ("win_league", "title_challenge") and result_type == "loss":
        change -= 2
    elif club.season_expectation == "avoid_relegation" and result_type == "win":
        change += 1   # extra boost for underdogs winning

    club.board_confidence = int(clamp(club.board_confidence + change, 0, 100))


def generate_season_objectives(club: Club) -> list[BoardObjective]:
    """
    Generate board objectives from the club's season_expectation.

    The primary objective always matches the expectation.  Bigger clubs
    get an additional secondary objective.
    """
    exp = club.season_expectation
    objectives = [
        BoardObjective(
            description=expectation_display(exp),
            target=exp,
            priority="critical" if exp in ("win_league", "avoid_relegation") else "high",
        )
    ]

    # Secondary objectives for ambitious clubs
    if exp in ("win_league", "title_challenge"):
        objectives.append(BoardObjective(
            description="Reach the Egypt Cup Semi-Finals",
            target="cup_semis",
            priority="medium",
        ))
    elif exp in ("top_4", "top_half"):
        objectives.append(BoardObjective(
            description="Develop at least one youth player",
            target="develop_youth",
            priority="low",
        ))

    return objectives


def evaluate_objectives(club: Club, position: int,
                         total_teams: int = 18) -> list[str]:
    """
    Evaluate board objectives at season end.

    Uses each objective's *target* key to look up the required finishing
    position from the SEASON_EXPECTATIONS table, so every club is judged
    against its own expectation.

    Returns feedback messages.
    """
    messages = []

    for obj in club.board_objectives:
        achieved = False

        # Primary league-position objectives
        required_pos = expectation_target_position(obj.target)
        if obj.target in SEASON_EXPECTATIONS:
            achieved = position <= required_pos
            if achieved:
                # Scale reward by how hard the objective was
                bonus = {
                    "win_league": 20,
                    "title_challenge": 15,
                    "top_4": 10,
                    "top_half": 5,
                    "mid_table": 5,
                    "avoid_relegation": 5,
                }.get(obj.target, 5)
                club.board_confidence = min(100, club.board_confidence + bonus)
            else:
                # Scale penalty by how badly we missed
                overshoot = position - required_pos
                penalty = min(25, 5 + overshoot * 2)
                club.board_confidence = max(0, club.board_confidence - penalty)
        elif obj.target == "cup_semis":
            # Cup not implemented yet — auto-pass
            achieved = True
        elif obj.target == "develop_youth":
            # Youth development not tracked yet — auto-pass
            achieved = True

        obj.achieved = achieved
        if achieved:
            messages.append(f"✅ {obj.description}")
        else:
            messages.append(f"❌ {obj.description}")

    return messages

