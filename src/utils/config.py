"""
Game configuration constants and settings for Pharaoh Engine.
"""
from enum import Enum, IntEnum
from dataclasses import dataclass


# ── Version ──────────────────────────────────────────────────────────────────
APP_NAME = "Pharaoh Engine"
APP_VERSION = "0.3.0"

# ── League Structure ─────────────────────────────────────────────────────────
LEAGUE_TEAM_COUNT = 18
MATCHES_PER_SEASON = (LEAGUE_TEAM_COUNT - 1) * 2  # 34 matchdays (double round-robin)
SQUAD_MIN_SIZE = 18
SQUAD_MAX_SIZE = 35

# ── Attribute System ─────────────────────────────────────────────────────────
ATTR_MIN = 1
ATTR_MAX = 20
ABILITY_MIN = 1
ABILITY_MAX = 200

# ── Match Engine ─────────────────────────────────────────────────────────────
MATCH_DURATION_MINUTES = 90
HALF_TIME_MINUTE = 45
INJURY_TIME_MAX_FIRST_HALF = 4
INJURY_TIME_MAX_SECOND_HALF = 7
HOME_ADVANTAGE_BONUS = 1.08  # 8% boost to home team ratings

# ── Finance ──────────────────────────────────────────────────────────────────
CURRENCY_SYMBOL = "EGP"
CURRENCY_NAME = "Egyptian Pound"

# ── Season Calendar ──────────────────────────────────────────────────────────
SEASON_START_MONTH = 8   # August
SEASON_START_DAY = 15
SEASON_END_MONTH = 5     # May

# ── Transfer Windows ────────────────────────────────────────────────────────
SUMMER_WINDOW_START = (6, 1)   # June 1
SUMMER_WINDOW_END = (8, 31)    # August 31
WINTER_WINDOW_START = (1, 1)   # January 1
WINTER_WINDOW_END = (1, 31)    # January 31


class Position(str, Enum):
    """Player positions."""
    GK = "GK"
    CB = "CB"
    LB = "LB"
    RB = "RB"
    CDM = "CDM"
    CM = "CM"
    CAM = "CAM"
    LW = "LW"
    RW = "RW"
    LM = "LM"
    RM = "RM"
    ST = "ST"


class PositionGroup(str, Enum):
    """High-level position groupings."""
    GOALKEEPER = "GK"
    DEFENDER = "DEF"
    MIDFIELDER = "MID"
    ATTACKER = "ATT"


POSITION_GROUP_MAP = {
    Position.GK: PositionGroup.GOALKEEPER,
    Position.CB: PositionGroup.DEFENDER,
    Position.LB: PositionGroup.DEFENDER,
    Position.RB: PositionGroup.DEFENDER,
    Position.CDM: PositionGroup.MIDFIELDER,
    Position.CM: PositionGroup.MIDFIELDER,
    Position.CAM: PositionGroup.MIDFIELDER,
    Position.LW: PositionGroup.ATTACKER,
    Position.RW: PositionGroup.ATTACKER,
    Position.LM: PositionGroup.MIDFIELDER,
    Position.RM: PositionGroup.MIDFIELDER,
    Position.ST: PositionGroup.ATTACKER,
}


class Mentality(IntEnum):
    """Tactical mentality levels."""
    ULTRA_DEFENSIVE = 1
    DEFENSIVE = 2
    CAUTIOUS = 3
    BALANCED = 4
    POSITIVE = 5
    ATTACKING = 6
    ULTRA_ATTACKING = 7


class Foot(str, Enum):
    """Preferred foot."""
    LEFT = "Left"
    RIGHT = "Right"
    BOTH = "Both"


class MatchEventType(str, Enum):
    """Types of events that can occur during a match."""
    GOAL = "goal"
    ASSIST = "assist"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    SUBSTITUTION = "substitution"
    INJURY = "injury"
    PENALTY = "penalty"
    PENALTY_MISS = "penalty_miss"
    SHOT_ON_TARGET = "shot_on_target"
    SHOT_OFF_TARGET = "shot_off_target"
    SAVE = "save"
    CORNER = "corner"
    FREE_KICK = "free_kick"
    HALF_TIME = "half_time"
    FULL_TIME = "full_time"
    KICKOFF = "kickoff"


class CompetitionType(str, Enum):
    """Types of competitions."""
    LEAGUE = "league"
    CUP = "cup"
    SUPER_CUP = "super_cup"
    CONTINENTAL = "continental"


class BoardConfidence(str, Enum):
    """Board confidence levels."""
    UNTOUCHABLE = "Untouchable"
    SECURE = "Secure"
    STABLE = "Stable"
    UNCERTAIN = "Uncertain"
    UNDER_PRESSURE = "Under Pressure"
    ON_THE_BRINK = "On the Brink"


# ── Formation Templates ─────────────────────────────────────────────────────
# Maps formation name → list of positions for 11 players (GK always first)
FORMATION_TEMPLATES: dict[str, list[Position]] = {
    "4-4-2": [
        Position.GK,
        Position.RB, Position.CB, Position.CB, Position.LB,
        Position.RM, Position.CM, Position.CM, Position.LM,
        Position.ST, Position.ST,
    ],
    "4-3-3": [
        Position.GK,
        Position.RB, Position.CB, Position.CB, Position.LB,
        Position.CM, Position.CM, Position.CM,
        Position.RW, Position.ST, Position.LW,
    ],
    "4-2-3-1": [
        Position.GK,
        Position.RB, Position.CB, Position.CB, Position.LB,
        Position.CDM, Position.CDM,
        Position.RW, Position.CAM, Position.LW,
        Position.ST,
    ],
    "3-5-2": [
        Position.GK,
        Position.CB, Position.CB, Position.CB,
        Position.RM, Position.CM, Position.CDM, Position.CM, Position.LM,
        Position.ST, Position.ST,
    ],
    "4-1-4-1": [
        Position.GK,
        Position.RB, Position.CB, Position.CB, Position.LB,
        Position.CDM,
        Position.RM, Position.CM, Position.CM, Position.LM,
        Position.ST,
    ],
    "5-3-2": [
        Position.GK,
        Position.RB, Position.CB, Position.CB, Position.CB, Position.LB,
        Position.CM, Position.CM, Position.CM,
        Position.ST, Position.ST,
    ],
    "4-3-1-2": [
        Position.GK,
        Position.RB, Position.CB, Position.CB, Position.LB,
        Position.CM, Position.CDM, Position.CM,
        Position.CAM,
        Position.ST, Position.ST,
    ],
}

# ── Governorates & Regional Talent Profiles ──────────────────────────────────
EGYPTIAN_GOVERNORATES = [
    "Cairo", "Giza", "Alexandria", "Port Said", "Suez",
    "Ismailia", "Dakahlia", "Sharqia", "Gharbia", "Monufia",
    "Beheira", "Qalyubia", "Kafr El Sheikh", "Damietta",
    "Fayoum", "Beni Suef", "Minya", "Asyut", "Sohag",
    "Qena", "Luxor", "Aswan", "Red Sea", "New Valley",
    "Matrouh", "North Sinai", "South Sinai",
]

# ── Training Focus Categories ────────────────────────────────────────────────
TRAINING_FOCUSES: dict[str, list[str]] = {
    "Shooting": ["finishing", "long_shots", "composure"],
    "Defending": ["tackling", "marking", "positioning"],
    "Physical": ["pace", "stamina", "strength", "agility"],
    "Playmaking": ["passing", "vision", "first_touch", "crossing"],
    "Mental": ["decisions", "composure", "work_rate", "leadership"],
}

INJURY_TYPES = [
    "Hamstring", "Ankle", "Knee", "Groin", "Calf",
    "Thigh", "Shoulder", "Back", "Concussion",
]

# ── Season Expectations ──────────────────────────────────────────────────────
# Maps expectation key → (display name, description, min_position to satisfy)
# min_position: board considers it "met" if the club finishes at or above this
SEASON_EXPECTATIONS: dict[str, tuple[str, str, int]] = {
    "win_league":       ("Win the League",        "The board demands the title.",              1),
    "title_challenge":  ("Title Challenge",       "A serious push for the championship.",      2),
    "top_4":            ("Top 4 Finish",          "Qualify for continental competition.",       4),
    "top_half":         ("Top Half Finish",       "Consolidate in the upper half.",            9),
    "mid_table":        ("Mid-Table Finish",      "Steady progress — stay competitive.",      12),
    "avoid_relegation": ("Avoid Relegation",      "Survival is the priority this season.",    15),
}


def derive_season_expectation(reputation: int) -> str:
    """Determine a club's season expectation based on its reputation."""
    if reputation >= 175:
        return "win_league"
    elif reputation >= 160:
        return "title_challenge"
    elif reputation >= 140:
        return "top_4"
    elif reputation >= 115:
        return "top_half"
    elif reputation >= 100:
        return "mid_table"
    else:
        return "avoid_relegation"


def expectation_display(key: str) -> str:
    """Human-readable name for an expectation key."""
    entry = SEASON_EXPECTATIONS.get(key)
    return entry[0] if entry else key.replace("_", " ").title()


def expectation_description(key: str) -> str:
    """Short description for an expectation."""
    entry = SEASON_EXPECTATIONS.get(key)
    return entry[1] if entry else ""


def expectation_target_position(key: str) -> int:
    """Maximum finishing position to satisfy the expectation."""
    entry = SEASON_EXPECTATIONS.get(key)
    return entry[2] if entry else 18

# ── UI / Display ─────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = ["en", "ar"]
DEFAULT_LANGUAGE = "en"


@dataclass
class GameSettings:
    """Runtime game settings (saved per game)."""
    language: str = DEFAULT_LANGUAGE
    match_speed: int = 3          # 1 (slow) to 5 (instant)
    auto_save: bool = True
    auto_save_interval: int = 7   # every N game days
    currency_display: str = CURRENCY_SYMBOL
    half_time_team_talk: bool = True
    detailed_match_events: bool = True
    difficulty: str = "normal"    # easy, normal, hard

