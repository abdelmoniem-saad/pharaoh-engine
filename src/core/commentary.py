"""
Match commentary — varied, atmospheric text templates for match events.
"""
from __future__ import annotations

from src.utils.config import MatchEventType
from src.utils import rng


TEMPLATES: dict[MatchEventType, list[str]] = {
    MatchEventType.GOAL: [
        "GOAL! {player} scores for {club}! The stadium erupts!",
        "What a finish from {player}! {club} hit the net!",
        "{player} slots it home! That's another goal for {club}!",
        "He's done it! {player} finds the back of the net for {club}!",
        "Clinical finish from {player}! {club} celebrate!",
        "The ball ripples the net! {player} makes no mistake for {club}!",
        "{player} with an ice-cold finish! {club} take the lead!",
        "GOLAZO! {player} scores a beauty for {club}!",
    ],
    MatchEventType.SHOT_ON_TARGET: [
        "{player} forces a save from the goalkeeper!",
        "Good effort from {player}, but the keeper is equal to it.",
        "{player} tests the keeper with a powerful strike!",
        "A fine save denies {player}!",
        "{player} gets a shot away — saved!",
    ],
    MatchEventType.SHOT_OFF_TARGET: [
        "{player} fires wide! A chance goes begging.",
        "Off target from {player}. That should have been better.",
        "{player} blazes it over the crossbar!",
        "The shot from {player} drifts harmlessly wide.",
        "{player} pulls the trigger but it's off the mark.",
    ],
    MatchEventType.YELLOW_CARD: [
        "Yellow card for {player}. The referee reaches for his pocket.",
        "{player} goes into the book. A cynical challenge.",
        "The referee shows {player} a yellow card for that foul.",
        "A caution for {player}. He needs to be careful now.",
    ],
    MatchEventType.RED_CARD: [
        "RED CARD! {player} is sent off! {club} are down to 10 men!",
        "A straight red for {player}! That's a terrible challenge!",
        "{player} sees red! {club} will have to play the rest with 10!",
    ],
    MatchEventType.CORNER: [
        "Corner kick for {club}.",
        "{club} win a corner. The ball is swung in...",
        "Another corner for {club}. Can they make it count?",
    ],
    MatchEventType.INJURY: [
        "{player} goes down holding his leg! The physio is on the pitch.",
        "Bad news for {club} — {player} is injured and can't continue.",
        "{player} limps off in pain. That doesn't look good at all.",
        "Concern for {club} as {player} goes down clutching his {detail}.",
    ],
    MatchEventType.HALF_TIME: [
        "The referee blows for half time.",
    ],
    MatchEventType.FULL_TIME: [
        "Full time! {home} {home_goals} - {away_goals} {away}",
    ],
    MatchEventType.KICKOFF: [
        "The match kicks off!",
    ],
}


def generate(event_type: MatchEventType, **kwargs) -> str:
    """
    Generate a commentary line for a given event type.
    Accepts keyword args: player, club, detail, home, away, home_goals, away_goals.
    """
    templates = TEMPLATES.get(event_type, ["{player} — event."])
    template = rng.choice(templates)
    try:
        return template.format(**kwargs)
    except KeyError:
        return template

