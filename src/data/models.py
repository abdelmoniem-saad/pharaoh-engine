"""
Pydantic data models for all core game entities.

These models serve as the single source of truth for data structures
throughout the simulation engine, database layer, and UI.
"""

import datetime as _dt

from pydantic import BaseModel, Field

from src.utils.config import (
    ABILITY_MAX,
    ABILITY_MIN,
    ATTR_MAX,
    ATTR_MIN,
    CompetitionType,
    Foot,
    MatchEventType,
    Mentality,
    Position,
)

# ── Player Models ────────────────────────────────────────────────────────────


class PlayerAttributes(BaseModel):
    """Player skill attributes (1-20 scale)."""

    # Technical
    finishing: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    passing: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    dribbling: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    first_touch: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    crossing: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    heading: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    long_shots: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    tackling: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    marking: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    free_kicks: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)

    # Physical
    pace: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    stamina: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    strength: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    agility: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    jumping: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)

    # Mental
    composure: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    vision: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    work_rate: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    leadership: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    aggression: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    positioning: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)
    decisions: int = Field(default=10, ge=ATTR_MIN, le=ATTR_MAX)

    # Goalkeeper-specific
    gk_reflexes: int = Field(default=5, ge=ATTR_MIN, le=ATTR_MAX)
    gk_handling: int = Field(default=5, ge=ATTR_MIN, le=ATTR_MAX)
    gk_positioning: int = Field(default=5, ge=ATTR_MIN, le=ATTR_MAX)
    gk_one_on_ones: int = Field(default=5, ge=ATTR_MIN, le=ATTR_MAX)
    gk_kicking: int = Field(default=5, ge=ATTR_MIN, le=ATTR_MAX)


class PlayerContract(BaseModel):
    """Player contract details."""

    wage_weekly: int = 0  # EGP per week
    contract_expiry: _dt.date | None = None
    release_clause: int | None = None
    signing_bonus: int = 0


class PlayerSeasonStats(BaseModel):
    """Per-season statistics for a player."""

    appearances: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0
    average_rating: float = 0.0
    man_of_the_match: int = 0


class Player(BaseModel):
    """Complete player model."""

    id: int = 0
    name: str
    name_ar: str = ""
    age: int = Field(ge=15, le=45)
    nationality: str = "Egyptian"
    governorate: str = "Cairo"
    position: Position
    secondary_positions: list[Position] = Field(default_factory=list)
    preferred_foot: Foot = Foot.RIGHT

    attributes: PlayerAttributes = Field(default_factory=PlayerAttributes)
    current_ability: int = Field(default=100, ge=ABILITY_MIN, le=ABILITY_MAX)
    potential_ability: int = Field(default=120, ge=ABILITY_MIN, le=ABILITY_MAX)

    contract: PlayerContract = Field(default_factory=PlayerContract)
    season_stats: PlayerSeasonStats = Field(default_factory=PlayerSeasonStats)

    morale: int = Field(default=50, ge=0, le=100)  # 0=terrible, 100=ecstatic
    fitness: int = Field(default=100, ge=0, le=100)  # 0=injured, 100=peak
    form: float = Field(default=7.0, ge=0.0, le=10.0)  # rolling match rating average

    club_id: int | None = None
    is_captain: bool = False
    shirt_number: int | None = None
    transfer_listed: bool = False

    # Injury & suspension
    injury_days_remaining: int = 0
    injury_type: str = ""  # e.g., "Hamstring", "Ankle", "Knee"
    suspension_matches: int = 0  # matches left on ban

    # Training
    training_focus: str = ""  # e.g., "Shooting", "Defending", "Physical", "Playmaking"

    # Morale tracking
    matches_benched_streak: int = 0  # consecutive matches benched (not in XI)


# ── Club Models ──────────────────────────────────────────────────────────────


class ClubFinances(BaseModel):
    """Club financial state."""

    balance: int = 0  # Current cash (EGP)
    transfer_budget: int = 0  # Available for transfers
    wage_budget_weekly: int = 0  # Max weekly wage spend
    wage_bill_weekly: int = 0  # Current weekly wage bill
    matchday_income: int = 0  # Revenue per home match (calculated in core/finance.py)
    ticket_price: int = 150  # Average ticket price (EGP)
    season_tickets: int = 0  # Number of season ticket holders
    sponsorship_income_yearly: int = 0
    tv_revenue_yearly: int = 0
    prize_money: int = 0


class BoardObjective(BaseModel):
    """A board-set objective for the season."""

    description: str
    target: str  # e.g., "finish_top_4", "win_cup"
    priority: str = "medium"  # low, medium, high, critical
    achieved: bool = False


class ManagerPromise(BaseModel):
    """A promise made by the manager to the board or media."""

    description: str
    target_type: str  # e.g., "win_next", "unbeaten_run", "youth_minutes"
    target_value: int = 1
    deadline_matchday: int
    progress: int = 0
    status: str = "active"  # active, fulfilled, failed


class Club(BaseModel):
    """Complete club model."""

    id: int = 0
    name: str
    short_name: str
    short_name_ar: str = ""
    city_ar: str = ""
    name_ar: str = ""
    city: str
    governorate: str
    reputation: int = Field(default=100, ge=1, le=200)
    stadium_name_ar: str = ""
    facilities_level: int = Field(default=5, ge=1, le=10)
    youth_rating: int = Field(default=5, ge=1, le=10)
    academy_tier: int = Field(default=4, ge=1, le=4)  # 1=Top, 4=Basic
    stadium_name: str = ""
    stadium_capacity: int = 10000

    primary_color: str = "#FFFFFF"
    secondary_color: str = "#000000"

    finances: ClubFinances = Field(default_factory=ClubFinances)
    board_objectives: list[BoardObjective] = Field(default_factory=list)
    promises: list[ManagerPromise] = Field(default_factory=list)
    board_confidence: int = Field(default=60, ge=0, le=100)
    fan_happiness: int = Field(default=50, ge=0, le=100)

    ultras_trust: int = Field(default=50, ge=0, le=100)
    choreo_momentum: int = Field(default=0, ge=0, le=100)
    protest_risk: int = Field(default=0, ge=0, le=100)

    formation: str = "4-2-3-1"
    mentality: Mentality = Mentality.BALANCED

    # Tactical sliders (1-10) — persisted so user's choices carry into matches
    pressing_intensity: int = Field(default=5, ge=1, le=10)
    tempo: int = Field(default=5, ge=1, le=10)
    width: int = Field(default=5, ge=1, le=10)
    defensive_line: int = Field(default=5, ge=1, le=10)

    is_user_controlled: bool = False

    # Season expectation — set per-club at season start based on reputation
    season_expectation: str = (
        "mid_table"  # win_league, top_4, top_half, mid_table, avoid_relegation
    )

    # Youth tracking
    youth_promoted_count: int = (
        0  # number of U21 players with ≥5 appearances this season
    )


# ── Match Models ─────────────────────────────────────────────────────────────


class MatchEvent(BaseModel):
    """A single event during a match."""

    minute: int
    event_type: MatchEventType
    player_id: int | None = None
    player_name: str = ""
    player_name_ar: str = ""
    second_player_id: int | None = None  # e.g., assist provider
    second_player_name: str = ""
    second_player_name_ar: str = ""
    club_id: int | None = None
    description: str = ""
    description_ar: str = ""


class MatchStats(BaseModel):
    """Aggregate match statistics for one team."""

    possession: float = 50.0
    shots: int = 0
    shots_on_target: int = 0
    corners: int = 0
    fouls: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    passes: int = 0
    pass_accuracy: float = 0.0
    saves: int = 0


class MatchResult(BaseModel):
    """Complete result of a simulated match."""

    match_id: int = 0
    home_club_id: int
    away_club_id: int
    home_club_name: str = ""
    away_club_name: str = ""
    home_club_name_ar: str = ""
    away_club_name_ar: str = ""
    home_goals: int = 0
    away_goals: int = 0
    events: list[MatchEvent] = Field(default_factory=list)
    home_stats: MatchStats = Field(default_factory=MatchStats)
    away_stats: MatchStats = Field(default_factory=MatchStats)
    player_ratings: dict[int, float] = Field(
        default_factory=dict
    )  # player_id → 1-10 rating
    competition: str = ""
    matchday: int = 0
    date: _dt.date | None = None

    @property
    def score_display(self) -> str:
        return f"{self.home_club_name} {self.home_goals} - {self.away_goals} {self.away_club_name}"


# ── League Models ────────────────────────────────────────────────────────────


class LeagueStanding(BaseModel):
    """A single row in the league table."""

    club_id: int
    club_name: str
    club_name_ar: str = ""
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    @property
    def points(self) -> int:
        return (self.won * 3) + self.drawn


class Fixture(BaseModel):
    """A scheduled match."""

    fixture_id: int = 0
    matchday: int
    home_club_id: int
    away_club_id: int
    home_club_name: str = ""
    away_club_name: str = ""
    home_club_name_ar: str = ""
    away_club_name_ar: str = ""
    date: _dt.date | None = None
    played: bool = False
    result: MatchResult | None = None
    competition: str = "Egyptian Premier League"
    submitted_starting_xi: list[int] = Field(default_factory=list)
    submitted_bench: list[int] = Field(default_factory=list)


class LeagueSeason(BaseModel):
    """Complete state of a league season."""

    season_year: int  # e.g., 2025 for 2025/26 season
    competition_name: str = "Egyptian Premier League"
    competition_type: CompetitionType = CompetitionType.LEAGUE
    standings: list[LeagueStanding] = Field(default_factory=list)
    fixtures: list[Fixture] = Field(default_factory=list)
    current_matchday: int = 1
    is_complete: bool = False


# ── Tactics Models ───────────────────────────────────────────────────────────


class TacticalPreset(BaseModel):
    """A named tactical preset for casual players."""

    name: str
    formation: str
    mentality: Mentality
    pressing_intensity: int = Field(default=5, ge=1, le=10)
    tempo: int = Field(default=5, ge=1, le=10)
    width: int = Field(default=5, ge=1, le=10)
    defensive_line: int = Field(default=5, ge=1, le=10)
    description: str = ""


class TeamTactics(BaseModel):
    """Active tactics for a match."""

    formation: str = "4-2-3-1"
    mentality: Mentality = Mentality.BALANCED
    pressing_intensity: int = Field(default=5, ge=1, le=10)
    tempo: int = Field(default=5, ge=1, le=10)
    width: int = Field(default=5, ge=1, le=10)
    defensive_line: int = Field(default=5, ge=1, le=10)
    starting_xi: list[int] = Field(default_factory=list)  # player IDs
    bench: list[int] = Field(default_factory=list)  # player IDs


# ── Game State ───────────────────────────────────────────────────────────────


class GameState(BaseModel):
    """Top-level game state model."""

    save_name: str = ""
    season_year: int = 2025
    current_date: _dt.date = Field(default_factory=lambda: _dt.date(2025, 8, 15))
    user_club_id: int = 0
    user_club_name: str = ""
    user_club_name_ar: str = ""
    manager_name: str = "Manager"
    rng_seed: int = 42
    day_count: int = 0


# ── Inbox / Messages ────────────────────────────────────────────────────────


class InboxMessage(BaseModel):
    """An in-game message for the user."""

    id: int = 0
    date: _dt.date
    subject: str
    body: str
    category: str = "general"  # general, match, transfer, board, media
    is_read: bool = False


class MatchdayOutcome(BaseModel):
    """Result of simulating a full matchday (user match + all others)."""

    fixture_id: int = 0
    user_result: MatchResult
    other_results: list[MatchResult] = Field(default_factory=list)
    matchday: int = 0
    position_before: int = 0  # league position before this matchday
    position_after: int = 0  # league position after this matchday
    attendance: int = 0  # match attendance
    newly_unlocked: list[str] = Field(default_factory=list)  # achievement keys
    home_starting_xi: list[int] = Field(default_factory=list)
    away_starting_xi: list[int] = Field(default_factory=list)


# ── Historical Stats Archive ────────────────────────────────────────────────


class SeasonHistory(BaseModel):
    """Record of a completed season."""

    id: int = 0
    season_year: int
    champion_club_id: int | None = None
    champion_club_name: str = ""
    user_club_id: int | None = None
    user_position: int = 0
    total_goals: int = 0
    total_matches: int = 0
    golden_boot_player: str = ""
    golden_boot_goals: int = 0
    golden_glove_player: str = ""
    golden_glove_clean_sheets: int = 0
    young_player_name: str = ""
    most_assists_player: str = ""
    most_assists_count: int = 0

    @property
    def season_display(self) -> str:
        return f"{self.season_year}/{self.season_year + 1}"


class PlayerSeasonArchive(BaseModel):
    """Archived player stats for a single completed season."""

    id: int = 0
    season_year: int
    player_id: int
    player_name: str = ""
    player_name_ar: str = ""
    club_id: int | None = None
    club_name: str = ""
    club_name_ar: str = ""
    position: str = ""
    age: int = 0
    appearances: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0
    average_rating: float = 0.0
    man_of_the_match: int = 0


class ClubSeasonArchive(BaseModel):
    """Archived club standings for a single completed season."""

    id: int = 0
    season_year: int
    club_id: int
    club_name: str = ""
    club_name_ar: str = ""
    position_finish: int = 0
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against
