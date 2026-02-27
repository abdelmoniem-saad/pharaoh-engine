"""
Competition module — Cup and continental competition logic.

Phase 2/3 module — stub for Egypt Cup and CAF competitions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from src.data.models import Club, MatchResult
from src.utils.config import CompetitionType


@dataclass
class CupRound:
    """A single round of a cup competition."""
    name: str
    matches: list[tuple[int, int]] = field(default_factory=list)  # (home_id, away_id)
    results: list[MatchResult] = field(default_factory=list)
    winners: list[int] = field(default_factory=list)


@dataclass
class CupCompetition:
    """A knockout cup competition."""
    name: str
    competition_type: CompetitionType = CompetitionType.CUP
    rounds: list[CupRound] = field(default_factory=list)
    participating_clubs: list[int] = field(default_factory=list)
    champion_id: int | None = None
    is_complete: bool = False


def create_egypt_cup(club_ids: list[int]) -> CupCompetition:
    """Create the Egypt Cup competition. Placeholder for Phase 2."""
    return CupCompetition(
        name="Egypt Cup",
        participating_clubs=list(club_ids),
    )


def draw_cup_round(remaining_clubs: list[int]) -> list[tuple[int, int]]:
    """Draw matches for a cup round. Placeholder for Phase 2."""
    from src.utils import rng
    clubs = list(remaining_clubs)
    rng.shuffle(clubs)

    matches = []
    for i in range(0, len(clubs) - 1, 2):
        matches.append((clubs[i], clubs[i + 1]))

    return matches

