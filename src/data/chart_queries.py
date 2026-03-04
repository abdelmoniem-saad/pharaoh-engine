"""
Chart data queries for Pharaoh Engine.

Provides data for player form charts, league position history,
and club form trend lines.
"""
from __future__ import annotations

import json
import sqlite3


def get_player_match_ratings(conn: sqlite3.Connection,
                              player_id: int,
                              limit: int = 10) -> list[tuple[int, float]]:
    """
    Get a player's match-by-match ratings from fixtures.

    Returns list of (matchday, rating) tuples, oldest first for charting.
    """
    rows = conn.execute(
        "SELECT matchday, player_ratings_json FROM fixtures"
        " WHERE played = 1 AND player_ratings_json IS NOT NULL"
        " AND player_ratings_json != '{}'"
        " ORDER BY matchday DESC"
    ).fetchall()

    results: list[tuple[int, float]] = []
    pid_str = str(player_id)
    for row in rows:
        try:
            ratings = json.loads(row["player_ratings_json"])
            if pid_str in ratings:
                results.append((row["matchday"], float(ratings[pid_str])))
        except (json.JSONDecodeError, KeyError):
            pass
        if len(results) >= limit:
            break

    results.reverse()  # oldest first for chart
    return results


def get_user_position_history(conn: sqlite3.Connection,
                               user_club_id: int) -> list[tuple[int, int]]:
    """
    Compute the user's league position after each played matchday.

    Returns list of (matchday, position) tuples, ordered by matchday.
    """
    matchdays_rows = conn.execute(
        "SELECT DISTINCT matchday FROM fixtures WHERE played = 1 ORDER BY matchday"
    ).fetchall()
    if not matchdays_rows:
        return []

    clubs_rows = conn.execute("SELECT id FROM clubs").fetchall()
    club_ids = [r["id"] for r in clubs_rows]

    tally: dict[int, dict] = {
        cid: {"pts": 0, "gd": 0, "gf": 0} for cid in club_ids
    }
    positions: list[tuple[int, int]] = []

    for md_row in matchdays_rows:
        md = md_row["matchday"]
        fixtures = conn.execute(
            "SELECT home_club_id, away_club_id, home_goals, away_goals"
            " FROM fixtures WHERE matchday = ? AND played = 1",
            (md,),
        ).fetchall()

        for f in fixtures:
            hid, aid = f["home_club_id"], f["away_club_id"]
            hg, ag = f["home_goals"] or 0, f["away_goals"] or 0
            if hid in tally:
                tally[hid]["gf"] += hg
                tally[hid]["gd"] += hg - ag
                tally[hid]["pts"] += 3 if hg > ag else 1 if hg == ag else 0
            if aid in tally:
                tally[aid]["gf"] += ag
                tally[aid]["gd"] += ag - hg
                tally[aid]["pts"] += 3 if ag > hg else 1 if ag == hg else 0

        sorted_clubs = sorted(
            tally.items(),
            key=lambda x: (x[1]["pts"], x[1]["gd"], x[1]["gf"]),
            reverse=True,
        )
        for rank, (cid, _) in enumerate(sorted_clubs, 1):
            if cid == user_club_id:
                positions.append((md, rank))
                break

    return positions


def get_club_form_results(conn: sqlite3.Connection,
                           club_id: int,
                           limit: int = 10) -> list[str]:
    """Get a club's recent form as W/D/L strings, most recent first."""
    rows = conn.execute(
        "SELECT home_club_id, home_goals, away_goals FROM fixtures"
        " WHERE played = 1 AND (home_club_id = ? OR away_club_id = ?)"
        " ORDER BY matchday DESC LIMIT ?",
        (club_id, club_id, limit),
    ).fetchall()

    results: list[str] = []
    for r in rows:
        hg, ag = r["home_goals"] or 0, r["away_goals"] or 0
        is_home = r["home_club_id"] == club_id
        own_goals = hg if is_home else ag
        opp_goals = ag if is_home else hg
        if own_goals > opp_goals:
            results.append("W")
        elif own_goals < opp_goals:
            results.append("L")
        else:
            results.append("D")
    return results

