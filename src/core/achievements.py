"""
Achievement / Milestone system — tracks career milestones and
awards for memorable moments.
"""
from __future__ import annotations

import sqlite3
from datetime import date


# ── Achievement definitions ─────────────────────────────────────────────────
# (key, title, description, icon)
ACHIEVEMENTS = [
    ("first_win",         "🏆 First Victory",        "Win your first match",                   "🏆"),
    ("first_clean_sheet", "🧤 Clean Sheet",           "Keep a clean sheet",                     "🧤"),
    ("win_streak_3",      "🔥 On Fire",               "Win 3 matches in a row",                 "🔥"),
    ("win_streak_5",      "⚡ Unstoppable",           "Win 5 matches in a row",                 "⚡"),
    ("win_streak_10",     "👑 Invincible Run",        "Win 10 matches in a row",                "👑"),
    ("unbeaten_5",        "🛡️ Resilient",             "Go 5 games unbeaten",                    "🛡️"),
    ("unbeaten_10",       "🏰 Fortress",              "Go 10 games unbeaten",                   "🏰"),
    ("match_10",          "📋 Getting Started",       "Manage 10 matches",                      "📋"),
    ("match_50",          "📋 Half Century",          "Manage 50 matches",                      "📋"),
    ("match_100",         "🎖️ The Centurion",         "Manage 100 matches",                     "🎖️"),
    ("goals_50",          "⚽ Goal Machine",          "Your team scores 50 goals",              "⚽"),
    ("goals_100",         "⚽ Century of Goals",      "Your team scores 100 goals",             "⚽"),
    ("win_league",        "🏆 Champion!",             "Win the league title",                   "🏆"),
    ("top_4",             "🥇 Top Four Finish",       "Finish in the top 4",                    "🥇"),
    ("avoid_relegation",  "😅 Great Escape",          "Avoid relegation (finish 16th or above)","😅"),
    ("youth_goal",        "🌟 Academy Graduate",      "A player aged 21 or under scores",       "🌟"),
    ("comeback_win",      "💪 The Comeback",          "Win after being behind at half-time",    "💪"),
    ("big_win",           "🎯 Demolition",            "Win a match by 4+ goals",                "🎯"),
    ("transfer_profit",   "💰 Smart Business",        "Make a profit on a player sale",         "💰"),
    ("press_master",      "🎤 Media Darling",         "Complete 10 press conferences",          "🎤"),
]


def seed_achievements(conn: sqlite3.Connection) -> None:
    """Insert all achievement definitions into the DB (idempotent)."""
    for key, title, desc, icon in ACHIEVEMENTS:
        try:
            conn.execute("""
                INSERT OR IGNORE INTO achievements (key, title, description, icon)
                VALUES (?, ?, ?, ?)
            """, (key, title, desc, icon))
        except Exception:
            pass
    # Also ensure manager_career row exists
    conn.execute("""
        INSERT OR IGNORE INTO manager_career (id) VALUES (1)
    """)
    conn.commit()


def get_achievements(conn: sqlite3.Connection) -> list[dict]:
    """Get all achievements with their unlock status."""
    rows = conn.execute("""
        SELECT key, title, description, icon, unlocked, unlock_date
        FROM achievements ORDER BY unlocked DESC, id ASC
    """).fetchall()
    return [
        {
            "key": r[0], "title": r[1], "description": r[2],
            "icon": r[3], "unlocked": bool(r[4]), "unlock_date": r[5],
        }
        for r in rows
    ]


def unlock_achievement(conn: sqlite3.Connection, key: str,
                        unlock_date: date) -> bool:
    """
    Unlock an achievement by key. Returns True if newly unlocked.
    """
    row = conn.execute(
        "SELECT unlocked FROM achievements WHERE key = ?", (key,)
    ).fetchone()
    if not row:
        return False
    if row[0]:
        return False  # Already unlocked

    conn.execute("""
        UPDATE achievements SET unlocked = 1, unlock_date = ? WHERE key = ?
    """, (unlock_date.isoformat(), key))
    conn.commit()
    return True


# ── Career stats ────────────────────────────────────────────────────────────

def load_career(conn: sqlite3.Connection) -> dict:
    """Load manager career stats."""
    row = conn.execute("SELECT * FROM manager_career WHERE id = 1").fetchone()
    if not row:
        conn.execute("INSERT OR IGNORE INTO manager_career (id) VALUES (1)")
        conn.commit()
        row = conn.execute("SELECT * FROM manager_career WHERE id = 1").fetchone()
    return {
        "total_wins": row[1], "total_draws": row[2], "total_losses": row[3],
        "trophies": row[4],
        "longest_win_streak": row[5], "current_win_streak": row[6],
        "current_unbeaten": row[7], "longest_unbeaten": row[8],
        "clean_sheets": row[9],
        "total_goals_scored": row[10], "total_goals_conceded": row[11],
        "best_signing_name": row[12], "best_signing_fee": row[13],
        "manager_rating": row[14],
    }


def update_career_after_match(conn: sqlite3.Connection, result_type: str,
                                user_goals: int, opp_goals: int,
                                board_confidence: int, fan_happiness: int,
                                current_date: date) -> list[str]:
    """
    Update career stats after a user match. Returns list of newly unlocked achievement keys.
    """
    career = load_career(conn)
    newly_unlocked = []

    # Update W/D/L
    if result_type == "win":
        career["total_wins"] += 1
        career["current_win_streak"] += 1
        career["current_unbeaten"] += 1
    elif result_type == "draw":
        career["total_draws"] += 1
        career["current_win_streak"] = 0
        career["current_unbeaten"] += 1
    else:
        career["total_losses"] += 1
        career["current_win_streak"] = 0
        career["current_unbeaten"] = 0

    # Update streaks
    if career["current_win_streak"] > career["longest_win_streak"]:
        career["longest_win_streak"] = career["current_win_streak"]
    if career["current_unbeaten"] > career["longest_unbeaten"]:
        career["longest_unbeaten"] = career["current_unbeaten"]

    # Goals
    career["total_goals_scored"] += user_goals
    career["total_goals_conceded"] += opp_goals

    # Clean sheets
    if opp_goals == 0:
        career["clean_sheets"] += 1

    # Manager rating
    total_matches = career["total_wins"] + career["total_draws"] + career["total_losses"]
    win_pct = career["total_wins"] / max(total_matches, 1) * 100
    career["manager_rating"] = round(win_pct * 0.4 + board_confidence * 0.3 + fan_happiness * 0.3, 1)

    # Save
    conn.execute("""
        UPDATE manager_career SET
            total_wins=?, total_draws=?, total_losses=?, trophies=?,
            longest_win_streak=?, current_win_streak=?,
            current_unbeaten=?, longest_unbeaten=?,
            clean_sheets=?, total_goals_scored=?, total_goals_conceded=?,
            best_signing_name=?, best_signing_fee=?, manager_rating=?
        WHERE id=1
    """, (
        career["total_wins"], career["total_draws"], career["total_losses"],
        career["trophies"],
        career["longest_win_streak"], career["current_win_streak"],
        career["current_unbeaten"], career["longest_unbeaten"],
        career["clean_sheets"], career["total_goals_scored"], career["total_goals_conceded"],
        career["best_signing_name"], career["best_signing_fee"],
        career["manager_rating"],
    ))
    conn.commit()

    # ── Check achievements ──────────────────────────────────────────
    if result_type == "win":
        if unlock_achievement(conn, "first_win", current_date):
            newly_unlocked.append("first_win")
    if opp_goals == 0:
        if unlock_achievement(conn, "first_clean_sheet", current_date):
            newly_unlocked.append("first_clean_sheet")
    if career["current_win_streak"] >= 3:
        if unlock_achievement(conn, "win_streak_3", current_date):
            newly_unlocked.append("win_streak_3")
    if career["current_win_streak"] >= 5:
        if unlock_achievement(conn, "win_streak_5", current_date):
            newly_unlocked.append("win_streak_5")
    if career["current_win_streak"] >= 10:
        if unlock_achievement(conn, "win_streak_10", current_date):
            newly_unlocked.append("win_streak_10")
    if career["current_unbeaten"] >= 5:
        if unlock_achievement(conn, "unbeaten_5", current_date):
            newly_unlocked.append("unbeaten_5")
    if career["current_unbeaten"] >= 10:
        if unlock_achievement(conn, "unbeaten_10", current_date):
            newly_unlocked.append("unbeaten_10")
    if total_matches >= 10:
        if unlock_achievement(conn, "match_10", current_date):
            newly_unlocked.append("match_10")
    if total_matches >= 50:
        if unlock_achievement(conn, "match_50", current_date):
            newly_unlocked.append("match_50")
    if total_matches >= 100:
        if unlock_achievement(conn, "match_100", current_date):
            newly_unlocked.append("match_100")
    if career["total_goals_scored"] >= 50:
        if unlock_achievement(conn, "goals_50", current_date):
            newly_unlocked.append("goals_50")
    if career["total_goals_scored"] >= 100:
        if unlock_achievement(conn, "goals_100", current_date):
            newly_unlocked.append("goals_100")
    if user_goals - opp_goals >= 4:
        if unlock_achievement(conn, "big_win", current_date):
            newly_unlocked.append("big_win")

    return newly_unlocked

