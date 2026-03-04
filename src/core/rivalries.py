"""
Derby rivalries system — defines historical rivalries between clubs.

Rivalries affect attendance, fan reactions, media coverage, and morale.
Specific to Egyptian football culture.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "seed"


@dataclass
class Rivalry:
    """A rivalry between two clubs."""
    club_a_id: int
    club_b_id: int
    rivalry_name: str
    rivalry_name_ar: str
    intensity: int  # 1-5 (5 = fiercest)
    description: str
    description_ar: str


# In-memory cache
_rivalries: list[Rivalry] = []


def load_rivalries(conn: sqlite3.Connection) -> list[Rivalry]:
    """Load rivalries from the database."""
    global _rivalries
    if _rivalries:
        return _rivalries

    rows = conn.execute("SELECT * FROM rivalries").fetchall()
    for row in rows:
        _rivalries.append(Rivalry(
            club_a_id=row["club_a_id"],
            club_b_id=row["club_b_id"],
            rivalry_name=row["rivalry_name"],
            rivalry_name_ar=row["rivalry_name_ar"],
            intensity=row["intensity"],
            description=row["description"],
            description_ar=row["description_ar"],
        ))
    return _rivalries


def seed_rivalries(conn: sqlite3.Connection) -> None:
    """Seed rivalry data from JSON into the database."""
    filepath = DATA_DIR / "rivalries.json"
    if not filepath.exists():
        return

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    for r in data.get("rivalries", []):
        try:
            conn.execute(
                """INSERT OR IGNORE INTO rivalries
                   (club_a_id, club_b_id, rivalry_name, rivalry_name_ar,
                    intensity, description, description_ar)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    r["club_a_id"], r["club_b_id"],
                    r["rivalry_name"], r.get("rivalry_name_ar", ""),
                    r.get("intensity", 3),
                    r.get("description", ""),
                    r.get("description_ar", ""),
                ),
            )
        except Exception:
            pass  # Skip invalid entries

    conn.commit()


def get_rivalry(
    conn: sqlite3.Connection, club_a_id: int, club_b_id: int
) -> Rivalry | None:
    """Check if two clubs have a rivalry. Returns the Rivalry or None."""
    rivalries = load_rivalries(conn)
    for r in rivalries:
        if (r.club_a_id == club_a_id and r.club_b_id == club_b_id) or \
           (r.club_a_id == club_b_id and r.club_b_id == club_a_id):
            return r
    return None


def is_derby(conn: sqlite3.Connection, club_a_id: int, club_b_id: int) -> bool:
    """Check if a match between two clubs is a derby."""
    return get_rivalry(conn, club_a_id, club_b_id) is not None


def derby_attendance_multiplier(rivalry: Rivalry) -> float:
    """Get the attendance multiplier for a derby match."""
    # Intensity 1-5 maps to 1.1x-1.5x
    return 1.0 + (rivalry.intensity * 0.1)


def derby_happiness_multiplier(rivalry: Rivalry) -> float:
    """Get the fan happiness swing multiplier for a derby."""
    return 1.0 + (rivalry.intensity * 0.3)


# Derby-specific headline templates
DERBY_HEADLINES = {
    "derby_win": [
        "🔥 {club} triumph in the {rivalry}!",
        "Bragging rights to {club} in fiery {rivalry}!",
        "Fans celebrate as {club} dominate the {rivalry}!",
        "{club} reign supreme in the {rivalry} derby!",
    ],
    "derby_loss": [
        "Heartbreak for {club} in the {rivalry}!",
        "{club} fall to bitter rivals in the {rivalry}!",
        "Dark day for {club} as rivals take the {rivalry}!",
        "Fans devastated as {club} lose the {rivalry}!",
    ],
    "derby_draw": [
        "Honours even in an intense {rivalry} clash!",
        "Neither side blinks in the {rivalry}!",
        "Passionate {rivalry} ends all square!",
    ],
}


def get_derby_headline(
    club_name: str, rivalry_name: str, result: str
) -> str:
    """Get a derby-specific headline."""
    from src.utils import rng
    key = f"derby_{result}"
    templates = DERBY_HEADLINES.get(key, DERBY_HEADLINES["derby_draw"])
    template = rng.choice(templates)
    return template.format(club=club_name, rivalry=rivalry_name)

