"""
Media pressure system — headlines, press conferences, narrative events.

Phase 3 module — stub with basic headline generation.
"""
from __future__ import annotations

from src.data.models import Club, MatchResult, InboxMessage
from src.utils import rng
from datetime import date


# Headline templates for different scenarios
HEADLINES = {
    "big_win": [
        "{club} demolish {opponent} in stunning display!",
        "Dominant {club} cruise past {opponent}!",
        "{club} send a statement with emphatic victory!",
    ],
    "narrow_win": [
        "{club} edge past {opponent} in tight affair",
        "Hard-fought victory for {club} against {opponent}",
        "{club} grab all three points against resilient {opponent}",
    ],
    "draw": [
        "Honours even as {club} and {opponent} share the spoils",
        "{club} held to a draw by determined {opponent}",
        "Neither side can find a winner in tense encounter",
    ],
    "loss": [
        "Disappointing day for {club} as {opponent} take the points",
        "{club} suffer defeat at the hands of {opponent}",
        "Questions for {club} manager after loss to {opponent}",
    ],
    "big_loss": [
        "Crisis at {club} after humiliating defeat to {opponent}!",
        "{club} capitulate in shocking loss to {opponent}!",
        "Manager under pressure after {club}'s dismal showing against {opponent}!",
    ],
}


def generate_match_headline(result: MatchResult, user_club_id: int) -> str:
    """Generate a media headline after a match involving the user's club."""
    is_home = result.home_club_id == user_club_id

    if is_home:
        user_goals = result.home_goals
        opp_goals = result.away_goals
        club_name = result.home_club_name
        opp_name = result.away_club_name
    else:
        user_goals = result.away_goals
        opp_goals = result.home_goals
        club_name = result.away_club_name
        opp_name = result.home_club_name

    diff = user_goals - opp_goals

    if diff >= 3:
        category = "big_win"
    elif diff > 0:
        category = "narrow_win"
    elif diff == 0:
        category = "draw"
    elif diff >= -2:
        category = "loss"
    else:
        category = "big_loss"

    template = rng.choice(HEADLINES[category])
    return template.format(club=club_name, opponent=opp_name)


def create_match_report_message(result: MatchResult, user_club_id: int,
                                  match_date: date) -> InboxMessage:
    """Create an inbox message with the match report."""
    headline = generate_match_headline(result, user_club_id)

    return InboxMessage(
        date=match_date,
        subject=headline,
        body=f"{result.score_display}\n\nThe media are watching closely...",
        category="media",
    )

