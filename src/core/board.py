"""
Board politics — objectives, confidence, and pressure system.

Each club has a `season_expectation` derived from its reputation at the start
of each season.  The board judges performance against that expectation.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.data.models import Club, BoardObjective
from src.utils.config import (
    BoardConfidence,
    SEASON_EXPECTATIONS,
    expectation_display,
    expectation_target_position,
)
from src.utils.rng import clamp


@dataclass
class ObjectiveProgressSnapshot:
    """Live objective status used for mid-season board briefings."""
    description: str
    status: str
    detail: str


def evaluate_objective_progress(
    club: Club,
    position: int,
    total_teams: int = 18,
    goals_for: int = 0,
    goal_difference: int = 0,
    season_progress: float = 0.0,
) -> list[ObjectiveProgressSnapshot]:
    """Evaluate objective trajectory during the season (without changing confidence)."""
    snapshots: list[ObjectiveProgressSnapshot] = []
    progress = clamp(season_progress, 0.0, 1.0)
    # Early season allows more table volatility before flagging a target as off-track.
    table_slack = max(1, int((1.0 - progress) * 4) + 1)

    for obj in club.board_objectives:
        if obj.target in SEASON_EXPECTATIONS:
            required_pos = expectation_target_position(obj.target)
            if position <= required_pos:
                snapshots.append(ObjectiveProgressSnapshot(
                    description=obj.description,
                    status="on_track",
                    detail=f"League position {position} (target: top {required_pos}).",
                ))
            elif position <= required_pos + table_slack:
                snapshots.append(ObjectiveProgressSnapshot(
                    description=obj.description,
                    status="at_risk",
                    detail=(
                        f"League position {position}; need top {required_pos}. "
                        "Within reach with a short run of results."
                    ),
                ))
            else:
                snapshots.append(ObjectiveProgressSnapshot(
                    description=obj.description,
                    status="off_track",
                    detail=f"League position {position}; currently below target of top {required_pos}.",
                ))
            continue

        if obj.target == "score_50_goals":
            projected = goals_for / progress if progress > 0 else goals_for
            if goals_for >= 50:
                status = "achieved"
                detail = f"{goals_for} goals scored already."
            elif projected >= 50:
                status = "on_track"
                detail = f"{goals_for} goals scored; projected pace is {int(projected)}."
            elif projected >= 42:
                status = "at_risk"
                detail = f"{goals_for} goals scored; attacking output needs a lift."
            else:
                status = "off_track"
                detail = f"{goals_for} goals scored; far below 50-goal pace."
            snapshots.append(ObjectiveProgressSnapshot(obj.description, status, detail))
            continue

        if obj.target == "positive_gd":
            if goal_difference > 0:
                status = "on_track"
                detail = f"Goal difference is +{goal_difference}."
            elif goal_difference == 0:
                status = "at_risk"
                detail = "Goal difference is level; one poor run could flip it negative."
            else:
                status = "off_track"
                detail = f"Goal difference is {goal_difference}; defensive record needs improving."
            snapshots.append(ObjectiveProgressSnapshot(obj.description, status, detail))
            continue

        if obj.target == "develop_youth":
            promoted = getattr(club, "youth_promoted_count", 0)
            if promoted >= 1:
                status = "achieved"
                detail = f"{promoted} youth player(s) have already broken through."
            elif progress < 0.6:
                status = "at_risk"
                detail = "No youth breakthrough yet, but there is still time to integrate prospects."
            else:
                status = "off_track"
                detail = "No youth breakthrough yet late in the season."
            snapshots.append(ObjectiveProgressSnapshot(obj.description, status, detail))

    return snapshots


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
    Adjust board confidence post-match.
    result_type: 'win', 'draw', 'loss'

    The change is scaled by the club's expectation. A title contender
    losing hurts more than a relegation-threatened team losing.
    """
    exp = club.season_expectation

    changes = {
        "win": {"win_league": 1, "top_4": 2, "mid_table": 2, "avoid_relegation": 3},
        "draw": {"win_league": -2, "top_4": -1, "mid_table": 0, "avoid_relegation": 1},
        "loss": {"win_league": -4, "top_4": -3, "mid_table": -2, "avoid_relegation": -1},
    }

    base = changes[result_type].get(exp, 0)
    club.board_confidence = int(clamp(club.board_confidence + base, 0, 100))


def update_promises_after_match(club: Club, result_type: str, current_matchday: int) -> list[str]:
    """
    Update progress on active promises after a match and evaluate them.
    Returns a list of inbox message bodies for completed/failed promises.
    """
    messages = []
    for promise in club.promises:
        if promise.status != "active":
            continue

        # Update progress based on target type
        if promise.target_type == "win_next" and result_type == "win":
            promise.progress += 1
        elif promise.target_type == "unbeaten_run":
            if result_type in ("win", "draw"):
                promise.progress += 1
            else:
                # Lost the unbeaten run
                promise.progress = -1

        # Evaluate status
        if promise.progress >= promise.target_value:
            promise.status = "fulfilled"
            club.board_confidence = min(100, club.board_confidence + 5)
            club.fan_happiness = min(100, club.fan_happiness + 5)
            messages.append(f"✅ Promise Fulfilled: {promise.description}")
        elif promise.progress == -1 or current_matchday >= promise.deadline_matchday:
            promise.status = "failed"
            club.board_confidence = max(0, club.board_confidence - 10)
            club.fan_happiness = max(0, club.fan_happiness - 10)
            messages.append(f"❌ Promise Failed: {promise.description}")

    return messages


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
            description="Score 50+ league goals",
            target="score_50_goals",
            priority="medium",
        ))
    elif exp in ("top_4", "top_half"):
        objectives.append(BoardObjective(
            description="Develop at least one youth player",
            target="develop_youth",
            priority="low",
        ))
    elif exp in ("mid_table", "avoid_relegation"):
        objectives.append(BoardObjective(
            description="Keep a positive goal difference",
            target="positive_gd",
            priority="low",
        ))

    return objectives


def evaluate_objectives(club: Club, position: int,
                         total_teams: int = 18,
                         goals_for: int = 0,
                         goal_difference: int = 0) -> list[str]:
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
                bonus = {
                    "win_league": 20, "title_challenge": 15,
                    "top_4": 10, "top_half": 5,
                    "mid_table": 5, "avoid_relegation": 5,
                }.get(obj.target, 5)
                club.board_confidence = min(100, club.board_confidence + bonus)
            else:
                overshoot = position - required_pos
                penalty = min(25, 5 + overshoot * 2)
                club.board_confidence = max(0, club.board_confidence - penalty)
        elif obj.target == "score_50_goals":
            achieved = goals_for >= 50
        elif obj.target == "positive_gd":
            achieved = goal_difference > 0
        elif obj.target == "develop_youth":
            achieved = getattr(club, "youth_promoted_count", 0) >= 1

        obj.achieved = achieved
        if achieved:
            messages.append(f"✅ {obj.description}")
        else:
            messages.append(f"❌ {obj.description}")

    return messages

