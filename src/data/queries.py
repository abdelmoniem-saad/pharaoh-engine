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
)
from src.utils.config import Position, Foot, Mentality


# ── Game State ───────────────────────────────────────────────────────────────

def save_game_state(conn: sqlite3.Connection, state: GameState) -> None:
    """Insert or update the game state."""
    conn.execute("""
        INSERT OR REPLACE INTO game_state (id, save_name, season_year, current_date,
            user_club_id, user_club_name, manager_name, rng_seed, day_count)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (state.save_name, state.season_year, state.current_date.isoformat(),
          state.user_club_id, state.user_club_name, state.manager_name,
          state.rng_seed, state.day_count))
    conn.commit()


def load_game_state(conn: sqlite3.Connection) -> GameState | None:
    """Load the game state from DB."""
    row = conn.execute("SELECT * FROM game_state WHERE id = 1").fetchone()
    if row is None:
        return None
    # Backward compat: manager_name may not exist in old saves
    manager_name = row["manager_name"] if "manager_name" in row.keys() else "Manager"
    return GameState(
        save_name=row["save_name"],
        season_year=row["season_year"],
        current_date=date.fromisoformat(row["current_date"]),
        user_club_id=row["user_club_id"],
        user_club_name=row["user_club_name"],
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
            board_confidence, fan_happiness, formation, mentality, is_user_controlled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (club.name, club.short_name, club.city, club.governorate, club.reputation,
          club.facilities_level, club.youth_rating, club.stadium_name, club.stadium_capacity,
          club.primary_color, club.secondary_color,
          club.finances.balance, club.finances.transfer_budget,
          club.finances.wage_budget_weekly, club.finances.wage_bill_weekly,
          club.finances.matchday_income, club.finances.sponsorship_income_yearly,
          club.finances.tv_revenue_yearly,
          club.board_confidence, club.fan_happiness, club.formation,
          int(club.mentality), int(club.is_user_controlled)))
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
            board_confidence=?, fan_happiness=?, is_user_controlled=?,
            balance=?, transfer_budget=?, wage_budget_weekly=?, wage_bill_weekly=?
        WHERE id=?
    """, (club.name, club.short_name, club.formation, int(club.mentality),
          club.board_confidence, club.fan_happiness, int(club.is_user_controlled),
          club.finances.balance, club.finances.transfer_budget,
          club.finances.wage_budget_weekly, club.finances.wage_bill_weekly,
          club.id))
    conn.commit()


def _row_to_club(row: sqlite3.Row) -> Club:
    """Convert a DB row to a Club model."""
    return Club(
        id=row["id"],
        name=row["name"],
        short_name=row["short_name"],
        city=row["city"],
        governorate=row["governorate"],
        reputation=row["reputation"],
        facilities_level=row["facilities_level"],
        youth_rating=row["youth_rating"],
        stadium_name=row["stadium_name"],
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
        formation=row["formation"],
        mentality=Mentality(row["mentality"]),
        is_user_controlled=bool(row["is_user_controlled"]),
    )


# ── Players ──────────────────────────────────────────────────────────────────

def insert_player(conn: sqlite3.Connection, player: Player) -> int:
    """Insert a player and return their ID."""
    a = player.attributes
    c = player.contract
    s = player.season_stats
    sec_pos = json.dumps([p.value for p in player.secondary_positions])

    cursor = conn.execute("""
        INSERT INTO players (name, age, nationality, governorate, position,
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (player.name, player.age, player.nationality, player.governorate,
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
    """Update a player's season stats, form, fitness, morale."""
    s = player.season_stats
    conn.execute("""
        UPDATE players SET appearances=?, goals=?, assists=?, clean_sheets=?,
            yellow_cards=?, red_cards=?, minutes_played=?, average_rating=?,
            man_of_the_match=?, form=?, fitness=?, morale=?
        WHERE id=?
    """, (s.appearances, s.goals, s.assists, s.clean_sheets,
          s.yellow_cards, s.red_cards, s.minutes_played, s.average_rating,
          s.man_of_the_match, player.form, player.fitness, player.morale,
          player.id))
    conn.commit()


def _row_to_player(row: sqlite3.Row) -> Player:
    """Convert a DB row to a Player model."""
    sec_pos_raw = json.loads(row["secondary_positions"]) if row["secondary_positions"] else []
    sec_positions = [Position(p) for p in sec_pos_raw]

    contract_expiry = None
    if row["contract_expiry"]:
        contract_expiry = date.fromisoformat(row["contract_expiry"])

    return Player(
        id=row["id"],
        name=row["name"],
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
            home_club_name, away_club_name, match_date, played, competition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (fixture.matchday, fixture.home_club_id, fixture.away_club_id,
          fixture.home_club_name, fixture.away_club_name,
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


def get_next_unplayed_matchday(conn: sqlite3.Connection) -> int | None:
    """Get the next matchday that has unplayed fixtures."""
    row = conn.execute(
        "SELECT MIN(matchday) as md FROM fixtures WHERE played = 0"
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

    conn.execute("""
        UPDATE fixtures SET played=1, home_goals=?, away_goals=?,
            events_json=?, home_stats_json=?, away_stats_json=?
        WHERE id=?
    """, (result.home_goals, result.away_goals,
          events_json, home_stats_json, away_stats_json, fixture_id))
    conn.commit()


def get_user_next_fixture(conn: sqlite3.Connection, user_club_id: int) -> Fixture | None:
    """Get the next unplayed fixture for the user's club."""
    row = conn.execute("""
        SELECT * FROM fixtures
        WHERE played = 0 AND (home_club_id = ? OR away_club_id = ?)
        ORDER BY matchday LIMIT 1
    """, (user_club_id, user_club_id)).fetchone()
    if row is None:
        return None
    return _row_to_fixture(row)


def _row_to_fixture(row: sqlite3.Row) -> Fixture:
    """Convert a DB row to a Fixture model."""
    result = None
    if row["played"]:
        events = []
        if row["events_json"]:
            raw_events = json.loads(row["events_json"])
            events = [MatchEvent(**e) for e in raw_events]
        home_stats = MatchStats(**json.loads(row["home_stats_json"])) if row["home_stats_json"] != '{}' else MatchStats()
        away_stats = MatchStats(**json.loads(row["away_stats_json"])) if row["away_stats_json"] != '{}' else MatchStats()

        result = MatchResult(
            match_id=row["id"],
            home_club_id=row["home_club_id"],
            away_club_id=row["away_club_id"],
            home_club_name=row["home_club_name"],
            away_club_name=row["away_club_name"],
            home_goals=row["home_goals"] or 0,
            away_goals=row["away_goals"] or 0,
            events=events,
            home_stats=home_stats,
            away_stats=away_stats,
        )

    return Fixture(
        fixture_id=row["id"],
        matchday=row["matchday"],
        home_club_id=row["home_club_id"],
        away_club_id=row["away_club_id"],
        home_club_name=row["home_club_name"],
        away_club_name=row["away_club_name"],
        date=date.fromisoformat(row["match_date"]) if row["match_date"] else None,
        played=bool(row["played"]),
        result=result,
        competition=row["competition"],
    )


# ── Standings ────────────────────────────────────────────────────────────────

def init_standings(conn: sqlite3.Connection, clubs: list[Club]) -> None:
    """Initialize league standings for all clubs."""
    for club in clubs:
        conn.execute("""
            INSERT OR IGNORE INTO standings (club_id, club_name)
            VALUES (?, ?)
        """, (club.id, club.name))
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
    return [LeagueStanding(
        club_id=row["club_id"],
        club_name=row["club_name"],
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
        "SELECT MIN(matchday) as md FROM fixtures WHERE played = 0"
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
                      fee: int, wage: int, contract_years: int = 3) -> None:
    """Execute a player transfer between clubs."""
    from datetime import date, timedelta
    expiry = date.today() + timedelta(days=365 * contract_years)

    # Move player
    conn.execute("""
        UPDATE players SET club_id = ?, wage_weekly = ?, contract_expiry = ?,
            transfer_listed = 0, morale = 60
        WHERE id = ?
    """, (to_club_id, wage, expiry.isoformat(), player_id))

    # Update selling club finances
    conn.execute("""
        UPDATE clubs SET transfer_budget = transfer_budget + ?,
            balance = balance + ? WHERE id = ?
    """, (fee, fee, from_club_id))

    # Update buying club finances
    conn.execute("""
        UPDATE clubs SET transfer_budget = transfer_budget - ?,
            balance = balance - ? WHERE id = ?
    """, (fee, fee, to_club_id))

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
                    years: int = 2, wage_increase_pct: int = 15) -> None:
    """Renew a player's contract with a wage increase."""
    from datetime import timedelta
    player = get_player(conn, player_id)
    if not player:
        return
    base_date = player.contract.contract_expiry or date.today()
    new_expiry = base_date + timedelta(days=365 * years)
    new_wage = int(player.contract.wage_weekly * (1 + wage_increase_pct / 100))
    conn.execute("""
        UPDATE players SET contract_expiry = ?, wage_weekly = ? WHERE id = ?
    """, (new_expiry.isoformat(), new_wage, player_id))
    conn.commit()


