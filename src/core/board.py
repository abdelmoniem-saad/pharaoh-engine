"""
Board politics — objectives, confidence, and pressure system.

Phase 2 module — stub with core mechanics.
"""
from __future__ import annotations

from src.data.models import Club, BoardObjective, LeagueStanding
from src.utils.config import BoardConfidence
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

    # Bigger clubs have less patience with losses
    if club.reputation >= 170 and result_type == "loss":
        change -= 2

    club.board_confidence = int(clamp(club.board_confidence + change, 0, 100))


def generate_season_objectives(club: Club) -> list[BoardObjective]:
    """Generate board objectives based on club reputation."""
    objectives = []

    if club.reputation >= 170:
        objectives.append(BoardObjective(
            description="Win the Egyptian Premier League",
            target="win_league",
            priority="critical",
        ))
        objectives.append(BoardObjective(
            description="Reach the Egypt Cup Semi-Finals",
            target="cup_semis",
            priority="medium",
        ))
    elif club.reputation >= 140:
        objectives.append(BoardObjective(
            description="Finish in the top 4",
            target="finish_top_4",
            priority="high",
        ))
    elif club.reputation >= 110:
        objectives.append(BoardObjective(
            description="Finish in the top half",
            target="finish_top_half",
            priority="high",
        ))
    else:
        objectives.append(BoardObjective(
            description="Avoid relegation",
            target="avoid_relegation",
            priority="critical",
        ))

    return objectives


def evaluate_objectives(club: Club, standing: LeagueStanding,
                         total_teams: int = 18) -> list[str]:
    """Evaluate board objectives at season end. Returns feedback messages."""
    messages = []
    standings_pos = 0  # Would need actual position

    for obj in club.board_objectives:
        if obj.target == "win_league" and standings_pos == 1:
            obj.achieved = True
            messages.append("✅ Board objective achieved: Win the league!")
            club.board_confidence = min(100, club.board_confidence + 20)
        elif obj.target == "finish_top_4" and standings_pos <= 4:
            obj.achieved = True
            messages.append("✅ Board objective achieved: Top 4 finish!")
            club.board_confidence = min(100, club.board_confidence + 10)
        elif obj.target == "avoid_relegation" and standings_pos <= total_teams - 3:
            obj.achieved = True
            messages.append("✅ Board objective achieved: Survived relegation!")
            club.board_confidence = min(100, club.board_confidence + 5)
        else:
            messages.append(f"❌ Board objective missed: {obj.description}")
            club.board_confidence = max(0, club.board_confidence - 15)

    return messages

