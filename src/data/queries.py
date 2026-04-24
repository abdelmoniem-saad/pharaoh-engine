"""
Reusable database queries for Pharaoh Engine.

All SQL queries go through here to keep the data layer centralized.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date

from src.data.models import (
    Player, PlayerAttributes, PlayerContract, PlayerSeasonStats,
    Club, ClubFinances, LeagueStanding, Fixture, MatchResult,
    MatchEvent, MatchStats, GameState, InboxMessage,
    SeasonHistory, PlayerSeasonArchive, ClubSeasonArchive,
)
from src.utils.config import Position, Foot, Mentality


# ── Game State ───────────────────────────────────────────────────────────────

def save_game_state(conn: sqlite3.Connection, state: GameState) -> None:
    """Insert or update the game state."""
    conn.execute("""
        INSERT OR REPLACE INTO game_state (id, save_name, season_year, current_date,
            user_club_id, user_club_name, user_club_name_ar, manager_name, rng_seed, day_count)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (state.save_name, state.season_year, state.current_date.isoformat(),
          state.user_club_id, state.user_club_name, state.user_club_name_ar,
          state.manager_name, state.rng_seed, state.day_count))
    conn.commit()


def load_game_state(conn: sqlite3.Connection) -> GameState | None:
    """Load the game state from DB."""
    row = conn.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    if row is None:
        return None
    # Backward compat: manager_name may not exist in old saves
    manager_name = row["manager_name"] if "manager_name" in row.keys() else "Manager"
    def _safe_str(col, default=""):
        try:
            val = row[col]
            return val if val is not None else default
        except (IndexError, KeyError):
            return default

    return GameState(
        save_name=row["save_name"],
        season_year=row["season_year"],
        current_date=date.fromisoformat(row["current_date"]),
        user_club_id=row["user_club_id"],
        user_club_name=row["user_club_name"],
        user_club_name_ar=_safe_str("user_club_name_ar"),
        manager_name=manager_name,
        rng_seed=row["rng_seed"],
        day_count=row["day_count"],
    )


# ── Clubs ────────────────────────────────────────────────────────────────────

def insert_club(conn: sqlite3.Connection, club: Club) -> int:
    """Insert a club and return its ID."""
    cursor = conn.execute("""
        INSERT INTO clubs (name, short_name, city, governorate, reputation,
            facilities_level, youth_rating, stadium_name, stadium_capacity,
            primary_color, secondary_color, balance, transfer_budget,
            wage_budget_weekly, wage_bill_weekly, matchday_income,
            sponsorship_income_yearly, tv_revenue_yearly,
            board_confidence, fan_happiness, 
            ultras_trust, choreo_momentum, protest_risk,
            promises_json,
            formation, mentality,
            pressing_intensity, tempo, width, defensive_line,
            is_user_controlled, season_expectation,
            name_ar, short_name_ar, city_ar, stadium_name_ar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (club.name, club.short_name, club.city, club.governorate, club.reputation,
          club.facilities_level, club.youth_rating, club.stadium_name, club.stadium_capacity,
          club.primary_color, club.secondary_color,
          club.finances.balance, club.finances.transfer_budget,
          club.finances.wage_budget_weekly, club.finances.wage_bill_weekly,
          club.finances.matchday_income, club.finances.sponsorship_income_yearly,
          club.finances.tv_revenue_yearly,
          club.board_confidence, club.fan_happiness, 
          club.ultras_trust, club.choreo_momentum, club.protest_risk,
          json.dumps([p.model_dump() for p in club.promises]),
          club.formation,
          int(club.mentality),
          club.pressing_intensity, club.tempo, club.width, club.defensive_line,
          int(club.is_user_controlled),
          club.season_expectation,
          club.name_ar, club.short_name_ar, club.city_ar, club.stadium_name_ar))
    conn.commit()
    return cursor.lastrowid


def get_all_clubs(conn: sqlite3.Connection) -> list[Club]:
    """Load all clubs from the database."""
    rows = conn.execute("SELECT * FROM clubs ORDER BY reputation DESC").fetchall()
    return [_row_to_club(row) for row in rows]


def get_club(conn: sqlite3.Connection, club_id: int) -> Club | None:
    """Load a single club by ID."""
    row = conn.execute("SELECT * FROM clubs WHERE id = ?", (club_id,)).fetchone()
    if row is None:
        return None
    return _row_to_club(row)


def update_club(conn: sqlite3.Connection, club: Club) -> None:
    """Update a club record."""
    conn.execute("""
        UPDATE clubs SET name=?, short_name=?, formation=?, mentality=?,
            pressing_intensity=?, tempo=?, width=?, defensive_line=?,
            board_confidence=?, fan_happiness=?, 
            ultras_trust=?, choreo_momentum=?, protest_risk=?,
            promises_json=?,
            is_user_controlled=?,
            balance=?, transfer_budget=?, wage_budget_weekly=?, wage_bill_weekly=?,
            season_expectation=?, matchday_income=?,
            name_ar=?, short_name_ar=?, city_ar=?, stadium_name_ar=?
        WHERE id=?
    """, (club.name, club.short_name, club.formation, int(club.mentality),
          club.pressing_intensity, club.tempo, club.width, club.defensive_line,
          club.board_confidence, club.fan_happiness,
          club.ultras_trust, club.choreo_momentum, club.protest_risk,
          json.dumps([p.model_dump() for p in club.promises]),
          int(club.is_user_controlled),
          club.finances.balance, club.finances.transfer_budget,
          club.finances.wage_budget_weekly, club.finances.wage_bill_weekly,
          club.season_expectation, club.finances.matchday_income,
          club.name_ar, club.short_name_ar, club.city_ar, club.stadium_name_ar,
          club.id))
    conn.commit()


def _row_to_club(row: sqlite3.Row) -> Club:
    """Convert a DB row to a Club model."""
    # Handle older saves that may lack columns
    try:
        expectation = row["season_expectation"]
    except (IndexError, KeyError):
        expectation = "mid_table"

    def _safe_int(col, default):
        try:
            return row[col]
        except (IndexError, KeyError):
            return default

    def _safe_str(col, default=""):
        try:
            val = row[col]
            return val if val is not None else default
        except (IndexError, KeyError):
            return default

    from src.data.models import ManagerPromise
    promises = []
    try:
        raw_promises = row["promises_json"]
        if raw_promises:
            promises = [ManagerPromise(**p) for p in json.loads(raw_promises)]
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        pass

    return Club(
        id=row["id"],
        name=row["name"],
        name_ar=_safe_str("name_ar"),
        short_name=row["short_name"],
        short_name_ar=_safe_str("short_name_ar"),
        city=row["city"],
        city_ar=_safe_str("city_ar"),
        governorate=row["governorate"],
        reputation=row["reputation"],
        facilities_level=row["facilities_level"],
        youth_rating=row["youth_rating"],
        stadium_name=row["stadium_name"],
        stadium_name_ar=_safe_str("stadium_name_ar"),
        stadium_capacity=row["stadium_capacity"],
        primary_color=row["primary_color"],
        secondary_color=row["secondary_color"],
        finances=ClubFinances(
            balance=row["balance"],
            transfer_budget=row["transfer_budget"],
            wage_budget_weekly=row["wage_budget_weekly"],
            wage_bill_weekly=row["wage_bill_weekly"],
            matchday_income=row["matchday_income"],
            sponsorship_income_yearly=row["sponsorship_income_yearly"],
            tv_revenue_yearly=row["tv_revenue_yearly"],
        ),
        board_confidence=row["board_confidence"],
        fan_happiness=row["fan_happiness"],
        ultras_trust=_safe_int("ultras_trust", 50),
        choreo_momentum=_safe_int("choreo_momentum", 0),
        protest_risk=_safe_int("protest_risk", 0),
        promises=promises,
        formation=row["formation"],
        mentality=Mentality(row["mentality"]),
        pressing_intensity=_safe_int("pressing_intensity", 5),
        tempo=_safe_int("tempo", 5),
        width=_safe_int("width", 5),
        defensive_line=_safe_int("defensive_line", 5),
        is_user_controlled=bool(row["is_user_controlled"]),
        season_expectation=expectation,
    )


# ── Players ──────────────────────────────────────────────────────────────────

def insert_player(conn: sqlite3.Connection, player: Player) -> int:
    """Insert a player and return their ID."""
    a = player.attributes
    c = player.contract
    s = player.season_stats
    sec_pos = json.dumps([p.value for p in player.secondary_positions])

    cursor = conn.execute("""
        INSERT INTO players (name, name_ar, age, nationality, governorate, position,
            secondary_positions, preferred_foot, current_ability, potential_ability,
            club_id, morale, fitness, form, is_captain, shirt_number, transfer_listed,
            finishing, passing, dribbling, first_touch, crossing, heading,
            long_shots, tackling, marking, free_kicks,
            pace, stamina, strength, agility, jumping,
            composure, vision, work_rate, leadership, aggression, positioning, decisions,
            gk_reflexes, gk_handling, gk_positioning, gk_one_on_ones, gk_kicking,
            wage_weekly, contract_expiry, release_clause,
            appearances, goals, assists, clean_sheets, yellow_cards, red_cards,
            minutes_played, average_rating, man_of_the_match)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (player.name, player.name_ar, player.age, player.nationality, player.governorate,
          player.position.value, sec_pos, player.preferred_foot.value,
          player.current_ability, player.potential_ability,
          player.club_id, player.morale, player.fitness, player.form,
          int(player.is_captain), player.shirt_number, int(player.transfer_listed),
          a.finishing, a.passing, a.dribbling, a.first_touch, a.crossing, a.heading,
          a.long_shots, a.tackling, a.marking, a.free_kicks,
          a.pace, a.stamina, a.strength, a.agility, a.jumping,
          a.composure, a.vision, a.work_rate, a.leadership, a.aggression,
          a.positioning, a.decisions,
          a.gk_reflexes, a.gk_handling, a.gk_positioning, a.gk_one_on_ones, a.gk_kicking,
          c.wage_weekly, c.contract_expiry.isoformat() if c.contract_expiry else None,
          c.release_clause,
          s.appearances, s.goals, s.assists, s.clean_sheets, s.yellow_cards, s.red_cards,
          s.minutes_played, s.average_rating, s.man_of_the_match))
    conn.commit()
    return cursor.lastrowid


def get_players_by_club(conn: sqlite3.Connection, club_id: int) -> list[Player]:
    """Get all players for a club."""
    rows = conn.execute(
        "SELECT * FROM players WHERE club_id = ? ORDER BY position, current_ability DESC",
        (club_id,)
    ).fetchall()
    return [_row_to_player(row) for row in rows]


def get_player(conn: sqlite3.Connection, player_id: int) -> Player | None:
    """Get a single player by ID."""
    row = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    if row is None:
        return None
    return _row_to_player(row)


def update_player_stats(conn: sqlite3.Connection, player: Player) -> None:
    """Update a player's season stats, form, fitness, morale, injury, suspension,
    training, current_ability, and all individual attributes."""
    s = player.season_stats
    a = player.attributes
    conn.execute("""
        UPDATE players SET appearances=?, goals=?, assists=?, clean_sheets=?,
            yellow_cards=?, red_cards=?, minutes_played=?, average_rating=?,
            man_of_the_match=?, form=?, fitness=?, morale=?,
            injury_days_remaining=?, injury_type=?, suspension_matches=?,
            training_focus=?, matches_benched_streak=?,
            current_ability=?,
            finishing=?, passing=?, dribbling=?, first_touch=?, crossing=?,
            heading=?, long_shots=?, tackling=?, marking=?, free_kicks=?,
            pace=?, stamina=?, strength=?, agility=?, jumping=?,
            composure=?, vision=?, work_rate=?, leadership=?, aggression=?,
            positioning=?, decisions=?,
            gk_reflexes=?, gk_handling=?, gk_positioning=?, gk_one_on_ones=?, gk_kicking=?
        WHERE id=?
    """, (s.appearances, s.goals, s.assists, s.clean_sheets,
          s.yellow_cards, s.red_cards, s.minutes_played, s.average_rating,
          s.man_of_the_match, player.form, player.fitness, player.morale,
          player.injury_days_remaining, player.injury_type,
          player.suspension_matches, player.training_focus,
          player.matches_benched_streak,
          player.current_ability,
          a.finishing, a.passing, a.dribbling, a.first_touch, a.crossing,
          a.heading, a.long_shots, a.tackling, a.marking, a.free_kicks,
          a.pace, a.stamina, a.strength, a.agility, a.jumping,
          a.composure, a.vision, a.work_rate, a.leadership, a.aggression,
          a.positioning, a.decisions,
          a.gk_reflexes, a.gk_handling, a.gk_positioning, a.gk_one_on_ones, a.gk_kicking,
          player.id))
    conn.commit()


def _row_to_player(row: sqlite3.Row) -> Player:
    """Convert a DB row to a Player model."""
    sec_pos_raw = json.loads(row["secondary_positions"]) if row["secondary_positions"] else []
    sec_positions = [Position(p) for p in sec_pos_raw]

    contract_expiry = None
    if row["contract_expiry"]:
        contract_expiry = date.fromisoformat(row["contract_expiry"])

    # Arabic name (may not exist in older saves)
    try:
        name_ar = row["name_ar"] if row["name_ar"] else ""
    except (IndexError, KeyError):
        name_ar = ""

    return Player(
        id=row["id"],
        name=row["name"],
        name_ar=name_ar,
        age=row["age"],
        nationality=row["nationality"],
        governorate=row["governorate"],
        position=Position(row["position"]),
        secondary_positions=sec_positions,
        preferred_foot=Foot(row["preferred_foot"]),
        current_ability=row["current_ability"],
        potential_ability=row["potential_ability"],
        club_id=row["club_id"],
        morale=row["morale"],
        fitness=row["fitness"],
        form=row["form"],
        is_captain=bool(row["is_captain"]),
        shirt_number=row["shirt_number"],
        transfer_listed=bool(row["transfer_listed"]) if "transfer_listed" in row.keys() else False,
        injury_days_remaining=row["injury_days_remaining"] if "injury_days_remaining" in row.keys() else 0,
        injury_type=row["injury_type"] if "injury_type" in row.keys() else "",
        suspension_matches=row["suspension_matches"] if "suspension_matches" in row.keys() else 0,
        training_focus=row["training_focus"] if "training_focus" in row.keys() else "",
        matches_benched_streak=row["matches_benched_streak"] if "matches_benched_streak" in row.keys() else 0,
        attributes=PlayerAttributes(
            finishing=row["finishing"], passing=row["passing"],
            dribbling=row["dribbling"], first_touch=row["first_touch"],
            crossing=row["crossing"], heading=row["heading"],
            long_shots=row["long_shots"], tackling=row["tackling"],
            marking=row["marking"], free_kicks=row["free_kicks"],
            pace=row["pace"], stamina=row["stamina"],
            strength=row["strength"], agility=row["agility"],
            jumping=row["jumping"],
            composure=row["composure"], vision=row["vision"],
            work_rate=row["work_rate"], leadership=row["leadership"],
            aggression=row["aggression"], positioning=row["positioning"],
            decisions=row["decisions"],
            gk_reflexes=row["gk_reflexes"], gk_handling=row["gk_handling"],
            gk_positioning=row["gk_positioning"],
            gk_one_on_ones=row["gk_one_on_ones"], gk_kicking=row["gk_kicking"],
        ),
        contract=PlayerContract(
            wage_weekly=row["wage_weekly"],
            contract_expiry=contract_expiry,
            release_clause=row["release_clause"],
        ),
        season_stats=PlayerSeasonStats(
            appearances=row["appearances"], goals=row["goals"],
            assists=row["assists"], clean_sheets=row["clean_sheets"],
            yellow_cards=row["yellow_cards"], red_cards=row["red_cards"],
            minutes_played=row["minutes_played"],
            average_rating=row["average_rating"],
            man_of_the_match=row["man_of_the_match"],
        ),
    )


# ── Fixtures ─────────────────────────────────────────────────────────────────

def insert_fixture(conn: sqlite3.Connection, fixture: Fixture) -> int:
    """Insert a fixture and return its ID."""
    cursor = conn.execute("""
        INSERT INTO fixtures (matchday, home_club_id, away_club_id,
            home_club_name, away_club_name, home_club_name_ar, away_club_name_ar,
            match_date, played, competition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (fixture.matchday, fixture.home_club_id, fixture.away_club_id,
          fixture.home_club_name, fixture.away_club_name,
          fixture.home_club_name_ar, fixture.away_club_name_ar,
          fixture.date.isoformat() if fixture.date else None,
          int(fixture.played), fixture.competition))
    conn.commit()
    return cursor.lastrowid


def get_fixtures_by_matchday(conn: sqlite3.Connection, matchday: int) -> list[Fixture]:
    """Get all fixtures for a specific matchday."""
    rows = conn.execute(
        "SELECT * FROM fixtures WHERE matchday = ? ORDER BY id", (matchday,)
    ).fetchall()
    return [_row_to_fixture(row) for row in rows]


def get_fixture_by_id(conn: sqlite3.Connection, fixture_id: int) -> Fixture | None:
    """Get a fixture by its ID regardless of played state."""
    row = conn.execute("SELECT * FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
    if row is None:
        return None
    return _row_to_fixture(row)


def get_unplayed_fixture_by_id(conn: sqlite3.Connection, fixture_id: int) -> Fixture | None:
    """Get a fixture by ID only if it is still unplayed."""
    row = conn.execute(
        "SELECT * FROM fixtures WHERE id = ? AND played = 0",
        (fixture_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_fixture(row)


def get_next_unplayed_matchday(conn: sqlite3.Connection) -> int | None:
    """Get the next league matchday that has unplayed fixtures (cup excluded)."""
    row = conn.execute(
        "SELECT MIN(matchday) as md FROM fixtures WHERE played = 0 AND matchday > 0"
    ).fetchone()
    if row and row["md"] is not None:
        return row["md"]
    return None


def mark_fixture_played(conn: sqlite3.Connection, fixture_id: int,
                         result: MatchResult) -> None:
    """Update a fixture with its result."""
    events_json = json.dumps([e.model_dump() for e in result.events], default=str)
    home_stats_json = json.dumps(result.home_stats.model_dump())
    away_stats_json = json.dumps(result.away_stats.model_dump())
    ratings_json = json.dumps(
        {str(k): v for k, v in result.player_ratings.items()}
    ) if result.player_ratings else '{}'

    conn.execute("""
        UPDATE fixtures SET played=1, home_goals=?, away_goals=?,
            events_json=?, home_stats_json=?, away_stats_json=?,
            player_ratings_json=?
        WHERE id=?
    """, (result.home_goals, result.away_goals,
          events_json, home_stats_json, away_stats_json,
          ratings_json, fixture_id))
    conn.commit()


def save_submitted_lineup(conn: sqlite3.Connection, fixture_id: int,
                          starting_xi: list[int], bench: list[int]) -> None:
    """Persist the user's submitted lineup for a specific upcoming fixture."""
    try:
        conn.execute(
            """
            UPDATE fixtures
            SET submitted_starting_xi_json = ?, submitted_bench_json = ?
            WHERE id = ?
            """,
            (json.dumps(starting_xi), json.dumps(bench), fixture_id),
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        # Graceful fallback for legacy saves until schema self-heal runs.
        if "submitted_starting_xi_json" not in str(e) and "submitted_bench_json" not in str(e):
            raise


def clear_submitted_lineup(conn: sqlite3.Connection, fixture_id: int) -> None:
    """Clear persisted submitted lineup for a fixture (usually after match is played)."""
    try:
        conn.execute(
            """
            UPDATE fixtures
            SET submitted_starting_xi_json = '[]', submitted_bench_json = '[]'
            WHERE id = ?
            """,
            (fixture_id,),
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        if "submitted_starting_xi_json" not in str(e) and "submitted_bench_json" not in str(e):
            raise


def get_user_next_fixture(conn: sqlite3.Connection, user_club_id: int) -> Fixture | None:
    """Get the next unplayed fixture for the user's club."""
    row = conn.execute("""
        SELECT * FROM fixtures
        WHERE played = 0 AND (home_club_id = ? OR away_club_id = ?)
        ORDER BY match_date ASC LIMIT 1
    """, (user_club_id, user_club_id)).fetchone()
    if row is None:
        return None
    return _row_to_fixture(row)


def _row_to_fixture(row: sqlite3.Row) -> Fixture:
    """Convert a DB row to a Fixture model."""
    result = None
    def _safe_str(col, default=""):
        try:
            val = row[col]
            return val if val is not None else default
        except (IndexError, KeyError):
            return default

    if row["played"]:
        events = []
        if row["events_json"]:
            raw_events = json.loads(row["events_json"])
            events = [MatchEvent(**e) for e in raw_events]
        home_stats = MatchStats(**json.loads(row["home_stats_json"])) if row["home_stats_json"] != '{}' else MatchStats()
        away_stats = MatchStats(**json.loads(row["away_stats_json"])) if row["away_stats_json"] != '{}' else MatchStats()

        # Restore per-player ratings
        player_ratings = {}
        try:
            pr_col = row["player_ratings_json"]
            if pr_col and pr_col != '{}':
                raw = json.loads(pr_col)
                player_ratings = {int(k): float(v) for k, v in raw.items()}
        except (KeyError, IndexError):
            pass

        result = MatchResult(
            match_id=row["id"],
            home_club_id=row["home_club_id"],
            away_club_id=row["away_club_id"],
            home_club_name=row["home_club_name"],
            away_club_name=row["away_club_name"],
            home_club_name_ar=_safe_str("home_club_name_ar"),
            away_club_name_ar=_safe_str("away_club_name_ar"),
            home_goals=row["home_goals"] or 0,
            away_goals=row["away_goals"] or 0,
            events=events,
            home_stats=home_stats,
            away_stats=away_stats,
            player_ratings=player_ratings,
        )

    submitted_starting_xi: list[int] = []
    submitted_bench: list[int] = []
    try:
        raw_xi = row["submitted_starting_xi_json"]
        if raw_xi:
            submitted_starting_xi = [int(pid) for pid in json.loads(raw_xi)]
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        submitted_starting_xi = []
    try:
        raw_bench = row["submitted_bench_json"]
        if raw_bench:
            submitted_bench = [int(pid) for pid in json.loads(raw_bench)]
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        submitted_bench = []

    return Fixture(
        fixture_id=row["id"],
        matchday=row["matchday"],
        home_club_id=row["home_club_id"],
        away_club_id=row["away_club_id"],
        home_club_name=row["home_club_name"],
        away_club_name=row["away_club_name"],
        home_club_name_ar=_safe_str("home_club_name_ar"),
        away_club_name_ar=_safe_str("away_club_name_ar"),
        date=date.fromisoformat(row["match_date"]) if row["match_date"] else None,
        played=bool(row["played"]),
        result=result,
        competition=row["competition"],
        submitted_starting_xi=submitted_starting_xi,
        submitted_bench=submitted_bench,
    )


# ── Standings ────────────────────────────────────────────────────────────────

def init_standings(conn: sqlite3.Connection, clubs: list[Club]) -> None:
    """Initialize league standings for all clubs."""
    for club in clubs:
        conn.execute("""
            INSERT OR IGNORE INTO standings (club_id, club_name, club_name_ar)
            VALUES (?, ?, ?)
        """, (club.id, club.name, club.name_ar))
    conn.commit()


def get_standings(conn: sqlite3.Connection) -> list[LeagueStanding]:
    """Get current league standings sorted by points, GD, GF."""
    rows = conn.execute("""
        SELECT * FROM standings
        ORDER BY
            (won * 3 + drawn) DESC,
            (goals_for - goals_against) DESC,
            goals_for DESC,
            club_name ASC
    """).fetchall()

    def _safe_str(row, col, default=""):
        try:
            val = row[col]
            return val if val is not None else default
        except (IndexError, KeyError):
            return default

    return [LeagueStanding(
        club_id=row["club_id"],
        club_name=row["club_name"],
        club_name_ar=_safe_str(row, "club_name_ar"),
        played=row["played"],
        won=row["won"],
        drawn=row["drawn"],
        lost=row["lost"],
        goals_for=row["goals_for"],
        goals_against=row["goals_against"],
    ) for row in rows]


def update_standings_for_result(conn: sqlite3.Connection, result: MatchResult) -> None:
    """Update standings after a match result."""
    # Home team
    if result.home_goals > result.away_goals:
        _update_standing(conn, result.home_club_id, won=1, gf=result.home_goals, ga=result.away_goals)
        _update_standing(conn, result.away_club_id, lost=1, gf=result.away_goals, ga=result.home_goals)
    elif result.home_goals < result.away_goals:
        _update_standing(conn, result.home_club_id, lost=1, gf=result.home_goals, ga=result.away_goals)
        _update_standing(conn, result.away_club_id, won=1, gf=result.away_goals, ga=result.home_goals)
    else:
        _update_standing(conn, result.home_club_id, drawn=1, gf=result.home_goals, ga=result.away_goals)
        _update_standing(conn, result.away_club_id, drawn=1, gf=result.away_goals, ga=result.home_goals)


def _update_standing(conn: sqlite3.Connection, club_id: int,
                      won: int = 0, drawn: int = 0, lost: int = 0,
                      gf: int = 0, ga: int = 0) -> None:
    """Increment standing counters for a club."""
    conn.execute("""
        UPDATE standings SET
            played = played + 1,
            won = won + ?,
            drawn = drawn + ?,
            lost = lost + ?,
            goals_for = goals_for + ?,
            goals_against = goals_against + ?
        WHERE club_id = ?
    """, (won, drawn, lost, gf, ga, club_id))


# ── Inbox ────────────────────────────────────────────────────────────────────

def insert_message(conn: sqlite3.Connection, msg: InboxMessage) -> int:
    """Insert an inbox message."""
    cursor = conn.execute("""
        INSERT INTO inbox (message_date, subject, body, category, is_read)
        VALUES (?, ?, ?, ?, ?)
    """, (msg.date.isoformat(), msg.subject, msg.body, msg.category, int(msg.is_read)))
    conn.commit()
    return cursor.lastrowid


def get_inbox(conn: sqlite3.Connection, limit: int = 50) -> list[InboxMessage]:
    """Get recent inbox messages."""
    rows = conn.execute(
        "SELECT * FROM inbox ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [InboxMessage(
        id=row["id"],
        date=date.fromisoformat(row["message_date"]),
        subject=row["subject"],
        body=row["body"],
        category=row["category"],
        is_read=bool(row["is_read"]),
    ) for row in rows]


def mark_message_read(conn: sqlite3.Connection, msg_id: int) -> None:
    """Mark a message as read."""
    conn.execute("UPDATE inbox SET is_read = 1 WHERE id = ?", (msg_id,))
    conn.commit()


def mark_all_messages_read(conn: sqlite3.Connection) -> int:
    """Mark all unread messages as read. Returns the number of messages marked."""
    cursor = conn.execute("UPDATE inbox SET is_read = 1 WHERE is_read = 0")
    conn.commit()
    return cursor.rowcount


def get_unread_count(conn: sqlite3.Connection) -> int:
    """Get the number of unread inbox messages."""
    row = conn.execute("SELECT COUNT(*) as cnt FROM inbox WHERE is_read = 0").fetchone()
    return row["cnt"] if row else 0


def get_user_recent_fixtures(conn: sqlite3.Connection, user_club_id: int,
                              limit: int = 5) -> list[Fixture]:
    """Get the most recent played fixtures for the user's club."""
    rows = conn.execute("""
        SELECT * FROM fixtures
        WHERE played = 1 AND (home_club_id = ? OR away_club_id = ?)
        ORDER BY matchday DESC LIMIT ?
    """, (user_club_id, user_club_id, limit)).fetchall()
    return [_row_to_fixture(row) for row in reversed(rows)]


def get_current_matchday(conn: sqlite3.Connection) -> int:
    """Get the current (next unplayed) matchday number."""
    row = conn.execute(
        "SELECT MIN(matchday) as md FROM fixtures WHERE played = 0 AND matchday > 0"
    ).fetchone()
    if row and row["md"] is not None:
        return row["md"]
    # All played — return last matchday
    row2 = conn.execute("SELECT MAX(matchday) as md FROM fixtures").fetchone()
    return row2["md"] if row2 and row2["md"] else 1


def get_top_scorers(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    """Get top scorers across the league."""
    rows = conn.execute("""
        SELECT p.name, p.goals, p.assists, p.appearances, p.position,
               c.name as club_name, c.short_name as club_short
        FROM players p
        JOIN clubs c ON p.club_id = c.id
        WHERE p.goals > 0
        ORDER BY p.goals DESC, p.assists DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_matchday_results(conn: sqlite3.Connection, matchday: int) -> list[Fixture]:
    """Get all played fixtures for a specific matchday."""
    rows = conn.execute(
        "SELECT * FROM fixtures WHERE matchday = ? AND played = 1 ORDER BY id",
        (matchday,)
    ).fetchall()
    return [_row_to_fixture(row) for row in rows]


def get_all_matchdays_played(conn: sqlite3.Connection) -> list[int]:
    """Get all matchday numbers that have at least one played fixture."""
    rows = conn.execute(
        "SELECT DISTINCT matchday FROM fixtures WHERE played = 1 ORDER BY matchday DESC"
    ).fetchall()
    return [row["matchday"] for row in rows]


def get_all_matchdays(conn: sqlite3.Connection) -> list[int]:
    """Get all matchday numbers that exist in fixtures."""
    rows = conn.execute(
        "SELECT DISTINCT matchday FROM fixtures ORDER BY matchday DESC"
    ).fetchall()
    return [row["matchday"] for row in rows]


# ── Player Search & Actions ─────────────────────────────────────────────────

def search_players(conn: sqlite3.Connection, name: str = "",
                    position: str = "", max_age: int = 99,
                    min_ability: int = 0, exclude_club_id: int = 0,
                    limit: int = 50) -> list[Player]:
    """Search players across all clubs with filters."""
    sql = "SELECT * FROM players WHERE 1=1"
    params: list = []
    if name:
        sql += " AND name LIKE ?"
        params.append(f"%{name}%")
    if position:
        sql += " AND position = ?"
        params.append(position)
    if max_age < 99:
        sql += " AND age <= ?"
        params.append(max_age)
    if min_ability > 0:
        sql += " AND current_ability >= ?"
        params.append(min_ability)
    if exclude_club_id:
        sql += " AND club_id != ?"
        params.append(exclude_club_id)
    sql += " ORDER BY current_ability DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_player(row) for row in rows]


def set_captain(conn: sqlite3.Connection, club_id: int, player_id: int) -> None:
    """Set a player as captain, clearing any existing captain on the team."""
    conn.execute("UPDATE players SET is_captain = 0 WHERE club_id = ?", (club_id,))
    conn.execute("UPDATE players SET is_captain = 1 WHERE id = ?", (player_id,))
    conn.commit()


def update_player_shirt(conn: sqlite3.Connection, player_id: int,
                         shirt_number: int) -> None:
    """Update a player's shirt number."""
    conn.execute("UPDATE players SET shirt_number = ? WHERE id = ?",
                 (shirt_number, player_id))
    conn.commit()


def set_transfer_listed(conn: sqlite3.Connection, player_id: int,
                         listed: bool = True) -> None:
    """Mark or unmark a player as transfer listed."""
    conn.execute("UPDATE players SET transfer_listed = ? WHERE id = ?",
                 (int(listed), player_id))
    conn.commit()


def transfer_player(conn: sqlite3.Connection, player_id: int,
                      from_club_id: int, to_club_id: int,
                      fee: int, wage: int, contract_years: int = 3,
                      current_date: date | None = None) -> None:
    """Execute a player transfer between clubs."""
    from datetime import timedelta
    game_date = current_date or date.today()
    expiry = game_date + timedelta(days=365 * contract_years)

    # Look up the player's current wage so we can adjust wage bills
    row = conn.execute("SELECT wage_weekly FROM players WHERE id = ?",
                       (player_id,)).fetchone()
    old_wage = row["wage_weekly"] if row else 0

    # Move player
    conn.execute("""
        UPDATE players SET club_id = ?, wage_weekly = ?, contract_expiry = ?,
            transfer_listed = 0, morale = 60
        WHERE id = ?
    """, (to_club_id, wage, expiry.isoformat(), player_id))

    # Update selling club finances: +fee, -wage from wage bill
    conn.execute("""
        UPDATE clubs SET transfer_budget = transfer_budget + ?,
            balance = balance + ?,
            wage_bill_weekly = MAX(0, wage_bill_weekly - ?)
        WHERE id = ?
    """, (fee, fee, old_wage, from_club_id))

    # Update buying club finances: -fee, +wage to wage bill
    conn.execute("""
        UPDATE clubs SET transfer_budget = transfer_budget - ?,
            balance = balance - ?,
            wage_bill_weekly = wage_bill_weekly + ?
        WHERE id = ?
    """, (fee, fee, wage, to_club_id))

    conn.commit()


# ── Season Management ────────────────────────────────────────────────────────

def reset_all_season_stats(conn: sqlite3.Connection) -> None:
    """Reset all player season stats for a new season."""
    conn.execute("""
        UPDATE players SET appearances=0, goals=0, assists=0, clean_sheets=0,
            yellow_cards=0, red_cards=0, minutes_played=0, average_rating=0.0,
            man_of_the_match=0
    """)
    conn.commit()


def age_all_players(conn: sqlite3.Connection) -> None:
    """Age all players by 1 year."""
    conn.execute("UPDATE players SET age = age + 1")
    conn.commit()


def delete_all_fixtures(conn: sqlite3.Connection) -> None:
    """Delete all fixtures for a fresh season."""
    conn.execute("DELETE FROM fixtures")
    conn.commit()


def reset_standings(conn: sqlite3.Connection) -> None:
    """Reset all standings to zero."""
    conn.execute("""
        UPDATE standings SET played=0, won=0, drawn=0, lost=0,
            goals_for=0, goals_against=0
    """)
    conn.commit()


def get_list_save_files() -> list[str]:
    """List all save file names (without .db extension)."""
    from src.data.database import _DEFAULT_DB_DIR
    saves_dir = _DEFAULT_DB_DIR
    if not saves_dir.exists():
        return []
    return [f.stem for f in saves_dir.glob("*.db")]


def renew_contract(conn: sqlite3.Connection, player_id: int,
                    years: int = 2, wage_increase_pct: int = 15,
                    current_date: date | None = None) -> None:
    """Renew a player's contract with a wage increase."""
    from datetime import timedelta
    player = get_player(conn, player_id)
    if not player:
        return
    game_date = current_date or date.today()
    base_date = player.contract.contract_expiry or game_date
    new_expiry = base_date + timedelta(days=365 * years)
    new_wage = int(player.contract.wage_weekly * (1 + wage_increase_pct / 100))
    wage_diff = new_wage - player.contract.wage_weekly
    conn.execute("""
        UPDATE players SET contract_expiry = ?, wage_weekly = ? WHERE id = ?
    """, (new_expiry.isoformat(), new_wage, player_id))
    # Update the club's wage bill to reflect the new wage
    if player.club_id and wage_diff != 0:
        conn.execute("""
            UPDATE clubs SET wage_bill_weekly = wage_bill_weekly + ? WHERE id = ?
        """, (wage_diff, player.club_id))
    conn.commit()


# ── Head-to-Head ─────────────────────────────────────────────────────────────

def update_head_to_head(conn: sqlite3.Connection, club_a_id: int,
                         club_b_id: int, a_goals: int, b_goals: int) -> None:
    """Update head-to-head record after a match. Always store with smaller ID as club_a."""
    if club_a_id > club_b_id:
        club_a_id, club_b_id = club_b_id, club_a_id
        a_goals, b_goals = b_goals, a_goals

    row = conn.execute(
        "SELECT * FROM head_to_head WHERE club_a_id = ? AND club_b_id = ?",
        (club_a_id, club_b_id)
    ).fetchone()

    if row:
        if a_goals > b_goals:
            conn.execute("""
                UPDATE head_to_head SET club_a_wins = club_a_wins + 1,
                    club_a_goals = club_a_goals + ?, club_b_goals = club_b_goals + ?
                WHERE club_a_id = ? AND club_b_id = ?
            """, (a_goals, b_goals, club_a_id, club_b_id))
        elif b_goals > a_goals:
            conn.execute("""
                UPDATE head_to_head SET club_b_wins = club_b_wins + 1,
                    club_a_goals = club_a_goals + ?, club_b_goals = club_b_goals + ?
                WHERE club_a_id = ? AND club_b_id = ?
            """, (a_goals, b_goals, club_a_id, club_b_id))
        else:
            conn.execute("""
                UPDATE head_to_head SET draws = draws + 1,
                    club_a_goals = club_a_goals + ?, club_b_goals = club_b_goals + ?
                WHERE club_a_id = ? AND club_b_id = ?
            """, (a_goals, b_goals, club_a_id, club_b_id))
    else:
        a_wins = 1 if a_goals > b_goals else 0
        b_wins = 1 if b_goals > a_goals else 0
        draws = 1 if a_goals == b_goals else 0
        conn.execute("""
            INSERT INTO head_to_head (club_a_id, club_b_id, club_a_wins, club_b_wins,
                draws, club_a_goals, club_b_goals)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (club_a_id, club_b_id, a_wins, b_wins, draws, a_goals, b_goals))
    conn.commit()


def get_head_to_head(conn: sqlite3.Connection, club_a_id: int,
                      club_b_id: int) -> dict:
    """Get head-to-head record between two clubs."""
    # Always query with smaller ID as club_a
    swapped = club_a_id > club_b_id
    if swapped:
        club_a_id, club_b_id = club_b_id, club_a_id

    row = conn.execute(
        "SELECT * FROM head_to_head WHERE club_a_id = ? AND club_b_id = ?",
        (club_a_id, club_b_id)
    ).fetchone()

    if not row:
        return {"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0, "total": 0}

    if swapped:
        return {
            "wins": row["club_b_wins"],
            "draws": row["draws"],
            "losses": row["club_a_wins"],
            "goals_for": row["club_b_goals"],
            "goals_against": row["club_a_goals"],
            "total": row["club_a_wins"] + row["club_b_wins"] + row["draws"],
        }
    else:
        return {
            "wins": row["club_a_wins"],
            "draws": row["draws"],
            "losses": row["club_b_wins"],
            "goals_for": row["club_a_goals"],
            "goals_against": row["club_b_goals"],
            "total": row["club_a_wins"] + row["club_b_wins"] + row["draws"],
        }


# ── Transfer History ─────────────────────────────────────────────────────────

def log_transfer(conn: sqlite3.Connection, player_id: int, player_name: str,
                  from_club_id: int, from_club_name: str,
                  to_club_id: int, to_club_name: str,
                  fee: int, wage: int, transfer_date: date,
                  transfer_type: str = "permanent") -> None:
    """Log a completed transfer to the history table."""
    conn.execute("""
        INSERT INTO transfer_history
        (player_id, player_name, from_club_id, from_club_name,
         to_club_id, to_club_name, fee, wage, transfer_date, transfer_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (player_id, player_name, from_club_id, from_club_name,
          to_club_id, to_club_name, fee, wage,
          transfer_date.isoformat(), transfer_type))
    conn.commit()


def get_transfer_history(conn: sqlite3.Connection, limit: int = 30) -> list[dict]:
    """Get recent transfer history."""
    rows = conn.execute("""
        SELECT * FROM transfer_history ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_club_transfer_history(conn: sqlite3.Connection,
                               club_id: int, limit: int = 20) -> list[dict]:
    """Get transfer history for a specific club."""
    rows = conn.execute("""
        SELECT * FROM transfer_history
        WHERE from_club_id = ? OR to_club_id = ?
        ORDER BY id DESC LIMIT ?
    """, (club_id, club_id, limit)).fetchall()
    return [dict(row) for row in rows]


# ── Player Milestones ────────────────────────────────────────────────────────

def check_player_milestones(conn: sqlite3.Connection, player: "Player",
                             current_date: date) -> list[InboxMessage]:
    """Check for player milestone achievements and return inbox messages."""
    messages = []
    s = player.season_stats

    # Appearance milestones
    app_milestones = [50, 100, 150, 200, 250, 300]
    for milestone in app_milestones:
        if s.appearances == milestone:
            messages.append(InboxMessage(
                date=current_date,
                subject=f"🎉 {player.name} — {milestone} Appearances!",
                body=(f"Congratulations! {player.name} has made {milestone} appearances. "
                      f"A magnificent achievement for the club."),
                category="general",
            ))
            break

    # Goal milestones
    goal_milestones = [10, 25, 50, 75, 100]
    for milestone in goal_milestones:
        if s.goals == milestone:
            messages.append(InboxMessage(
                date=current_date,
                subject=f"⚽ {player.name} — {milestone} Goals!",
                body=(f"What a scorer! {player.name} has reached {milestone} career goals. "
                      f"The fans are ecstatic!"),
                category="general",
            ))
            break

    # Assist milestones
    assist_milestones = [10, 25, 50]
    for milestone in assist_milestones:
        if s.assists == milestone:
            messages.append(InboxMessage(
                date=current_date,
                subject=f"🅰️ {player.name} — {milestone} Assists!",
                body=f"{player.name} has provided {milestone} assists this season. Creative genius!",
                category="general",
            ))
            break

    return messages



# ── Historical Stats Archive ────────────────────────────────────────────────

def archive_season_history(conn: sqlite3.Connection, season_year: int,
                            awards: dict, user_club_id: int) -> None:
    """Archive the completed season summary into season_history."""
    champion = awards.get("champion")
    golden_boot = awards.get("golden_boot")
    golden_glove = awards.get("golden_glove")
    young_player = awards.get("young_player")
    most_assists = awards.get("most_assists")

    row = conn.execute("""
        SELECT COUNT(*) as matches,
               COALESCE(SUM(home_goals), 0) + COALESCE(SUM(away_goals), 0) as goals
        FROM fixtures WHERE played = 1
    """).fetchone()
    total_matches = row["matches"] if row else 0
    total_goals = row["goals"] if row else 0

    conn.execute("""
        INSERT OR REPLACE INTO season_history
        (season_year, champion_club_id, champion_club_name, user_club_id, user_position,
         total_goals, total_matches,
         golden_boot_player, golden_boot_goals,
         golden_glove_player, golden_glove_clean_sheets,
         young_player_name, most_assists_player, most_assists_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        season_year,
        champion.club_id if champion else None,
        champion.club_name if champion else "",
        user_club_id,
        awards.get("user_position", 0),
        total_goals, total_matches,
        golden_boot["name"] if golden_boot else "",
        golden_boot["goals"] if golden_boot else 0,
        golden_glove["name"] if golden_glove else "",
        golden_glove["clean_sheets"] if golden_glove else 0,
        young_player["name"] if young_player else "",
        most_assists["name"] if most_assists else "",
        most_assists["assists"] if most_assists else 0,
    ))
    conn.commit()


def archive_all_player_stats(conn: sqlite3.Connection, season_year: int) -> None:
    """Archive every player's current season stats before they get reset."""
    conn.execute("""
        INSERT OR REPLACE INTO player_season_archive
        (season_year, player_id, player_name, player_name_ar, club_id, club_name, club_name_ar,
         position, age, appearances, goals, assists, clean_sheets, yellow_cards, red_cards,
         minutes_played, average_rating, man_of_the_match)
        SELECT ?, p.id, p.name, p.name_ar, p.club_id, COALESCE(c.name, ''), COALESCE(c.name_ar, ''),
               p.position, p.age, p.appearances, p.goals, p.assists, p.clean_sheets,
               p.yellow_cards, p.red_cards, p.minutes_played,
               p.average_rating, p.man_of_the_match
        FROM players p
        LEFT JOIN clubs c ON p.club_id = c.id
        WHERE p.appearances > 0
    """, (season_year,))
    conn.commit()


def archive_all_club_standings(conn: sqlite3.Connection, season_year: int) -> None:
    """Archive every club's final standings before they get reset."""
    conn.execute("""
        INSERT OR REPLACE INTO club_season_archive
        (season_year, club_id, club_name, club_name_ar, position_finish, played, won, drawn, lost,
         goals_for, goals_against, points)
        SELECT ?, s.club_id, s.club_name, s.club_name_ar,
               ROW_NUMBER() OVER (ORDER BY (s.won * 3 + s.drawn) DESC,
                                  (s.goals_for - s.goals_against) DESC,
                                  s.goals_for DESC),
               s.played, s.won, s.drawn, s.lost,
               s.goals_for, s.goals_against,
               (s.won * 3 + s.drawn)
        FROM standings s
        WHERE s.played > 0
    """, (season_year,))
    conn.commit()


# ── Historical Stats Retrieval ──────────────────────────────────────────────

def get_season_history(conn: sqlite3.Connection) -> list[SeasonHistory]:
    """Get all archived season records ordered by year descending."""
    rows = conn.execute(
        "SELECT * FROM season_history ORDER BY season_year DESC"
    ).fetchall()
    return [SeasonHistory(
        id=row["id"],
        season_year=row["season_year"],
        champion_club_id=row["champion_club_id"],
        champion_club_name=row["champion_club_name"],
        user_club_id=row["user_club_id"],
        user_position=row["user_position"],
        total_goals=row["total_goals"],
        total_matches=row["total_matches"],
        golden_boot_player=row["golden_boot_player"],
        golden_boot_goals=row["golden_boot_goals"],
        golden_glove_player=row["golden_glove_player"],
        golden_glove_clean_sheets=row["golden_glove_clean_sheets"],
        young_player_name=row["young_player_name"],
        most_assists_player=row["most_assists_player"],
        most_assists_count=row["most_assists_count"],
    ) for row in rows]


def get_player_career_stats(conn: sqlite3.Connection,
                             player_id: int) -> list[PlayerSeasonArchive]:
    """Get all archived season stats for a single player."""
    rows = conn.execute("""
        SELECT * FROM player_season_archive
        WHERE player_id = ? ORDER BY season_year DESC
    """, (player_id,)).fetchall()
    return [_row_to_player_archive(row) for row in rows]


def get_all_time_top_scorers(conn: sqlite3.Connection,
                              limit: int = 20) -> list[dict]:
    """Get all-time top scorers aggregated across all archived seasons."""
    rows = conn.execute("""
        SELECT player_id, player_name,
               SUM(goals) as total_goals,
               SUM(assists) as total_assists,
               SUM(appearances) as total_appearances,
               ROUND(AVG(average_rating), 1) as avg_rating,
               COUNT(season_year) as seasons_played,
               MAX(club_name) as last_club
        FROM player_season_archive
        GROUP BY player_id
        HAVING total_goals > 0
        ORDER BY total_goals DESC, total_assists DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_all_time_top_assists(conn: sqlite3.Connection,
                              limit: int = 20) -> list[dict]:
    """Get all-time top assist providers aggregated across all archived seasons."""
    rows = conn.execute("""
        SELECT player_id, player_name,
               SUM(assists) as total_assists,
               SUM(goals) as total_goals,
               SUM(appearances) as total_appearances,
               ROUND(AVG(average_rating), 1) as avg_rating,
               COUNT(season_year) as seasons_played,
               MAX(club_name) as last_club
        FROM player_season_archive
        GROUP BY player_id
        HAVING total_assists > 0
        ORDER BY total_assists DESC, total_goals DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [dict(row) for row in rows]


def get_all_time_top_rated(conn: sqlite3.Connection,
                            limit: int = 20, min_appearances: int = 10) -> list[dict]:
    """Get all-time highest rated players (min appearances threshold)."""
    rows = conn.execute("""
        SELECT player_id, player_name,
               ROUND(AVG(average_rating), 2) as avg_rating,
               SUM(goals) as total_goals,
               SUM(assists) as total_assists,
               SUM(appearances) as total_appearances,
               SUM(man_of_the_match) as total_motm,
               COUNT(season_year) as seasons_played,
               MAX(club_name) as last_club
        FROM player_season_archive
        GROUP BY player_id
        HAVING total_appearances >= ?
        ORDER BY avg_rating DESC
        LIMIT ?
    """, (min_appearances, limit)).fetchall()
    return [dict(row) for row in rows]


def get_club_history(conn: sqlite3.Connection,
                      club_id: int) -> list[ClubSeasonArchive]:
    """Get all archived season standings for a specific club."""
    rows = conn.execute("""
        SELECT * FROM club_season_archive
        WHERE club_id = ? ORDER BY season_year DESC
    """, (club_id,)).fetchall()
    return [ClubSeasonArchive(
        id=row["id"],
        season_year=row["season_year"],
        club_id=row["club_id"],
        club_name=row["club_name"],
        position_finish=row["position_finish"],
        played=row["played"],
        won=row["won"],
        drawn=row["drawn"],
        lost=row["lost"],
        goals_for=row["goals_for"],
        goals_against=row["goals_against"],
        points=row["points"],
    ) for row in rows]


def get_season_player_stats(conn: sqlite3.Connection,
                             season_year: int,
                             limit: int = 50) -> list[PlayerSeasonArchive]:
    """Get all player stats for a specific archived season."""
    rows = conn.execute("""
        SELECT * FROM player_season_archive
        WHERE season_year = ? ORDER BY goals DESC, assists DESC
        LIMIT ?
    """, (season_year, limit)).fetchall()
    return [_row_to_player_archive(row) for row in rows]


def _row_to_player_archive(row: sqlite3.Row) -> PlayerSeasonArchive:
    """Convert a DB row to a PlayerSeasonArchive model."""
    def _safe_str(col, default=""):
        try:
            val = row[col]
            return val if val is not None else default
        except (IndexError, KeyError):
            return default

    return PlayerSeasonArchive(
        id=row["id"],
        season_year=row["season_year"],
        player_id=row["player_id"],
        player_name=row["player_name"],
        player_name_ar=_safe_str("player_name_ar"),
        club_id=row["club_id"],
        club_name=row["club_name"],
        club_name_ar=_safe_str("club_name_ar"),
        position=row["position"],
        age=row["age"],
        appearances=row["appearances"],
        goals=row["goals"],
        assists=row["assists"],
        clean_sheets=row["clean_sheets"],
        yellow_cards=row["yellow_cards"],
        red_cards=row["red_cards"],
        minutes_played=row["minutes_played"],
        average_rating=row["average_rating"],
        man_of_the_match=row["man_of_the_match"],
    )
# END OF FILE - chart queries moved to src/data/chart_queries.py
