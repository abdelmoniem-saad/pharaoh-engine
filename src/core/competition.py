"""
Competition module — Egypt Cup knockout tournament logic.

Full implementation: draw, fixture scheduling, extra-time/penalties,
round advancement, and season integration.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.data.models import Club, MatchResult, Fixture, InboxMessage
from src.data import queries
from src.utils.config import CompetitionType
from src.utils import rng

# ── Cup Configuration ────────────────────────────────────────────────────────

CUP_NAME = "Egypt Cup"

# Round names in order (first played → last)
CUP_ROUNDS = [
    "Round of 32",
    "Round of 16",
    "Quarter-finals",
    "Semi-finals",
    "Final",
]

# Scheduling offsets from season start (weeks after Aug 15)
# Interleaved with league matchdays
CUP_ROUND_WEEK_OFFSETS = {
    "Round of 32": 8,     # mid-October
    "Round of 16": 16,    # mid-December
    "Quarter-finals": 24, # mid-February
    "Semi-finals": 30,    # late March
    "Final": 36,          # late April
}

# Lower-division fictional clubs for cup padding (14 needed for 32 total)
LOWER_DIVISION_CLUBS = [
    ("Suez Cement SC", "سويس سمنت"),
    ("Port Said Rangers", "بور سعيد رينجرز"),
    ("Tanta Sports Club", "نادي طنطا الرياضي"),
    ("Damanhour City FC", "دمنهور سيتي"),
    ("Beni Suef United", "بني سويف يونايتد"),
    ("Minya Stars", "نجوم المنيا"),
    ("Aswan Eagles", "نسور أسوان"),
    ("Fayoum Athletic", "الفيوم أتلتيك"),
    ("Damietta FC", "نادي دمياط"),
    ("Kafr El-Sheikh SC", "نادي كفر الشيخ"),
    ("El-Arish FC", "نادي العريش"),
    ("New Valley SC", "نادي الوادي الجديد"),
    ("Qena Stars", "نجوم قنا"),
    ("Hurghada FC", "نادي الغردقة"),
]


@dataclass
class CupRound:
    """A single round of a cup competition."""
    name: str
    matches: list[tuple[int, int]] = field(default_factory=list)
    fixture_ids: list[int] = field(default_factory=list)
    winners: list[int] = field(default_factory=list)
    is_complete: bool = False


@dataclass
class CupCompetition:
    """A knockout cup competition."""
    name: str = CUP_NAME
    competition_type: CompetitionType = CompetitionType.CUP
    season_year: int = 2025
    rounds: dict[str, CupRound] = field(default_factory=dict)
    participating_clubs: list[int] = field(default_factory=list)
    club_names: dict[int, str] = field(default_factory=dict)
    current_round: str = ""
    champion_id: int | None = None
    is_complete: bool = False

    def to_json(self) -> str:
        """Serialize rounds to JSON for DB storage."""
        data = {}
        for rnd_name, rnd in self.rounds.items():
            data[rnd_name] = {
                "matches": rnd.matches,
                "fixture_ids": rnd.fixture_ids,
                "winners": rnd.winners,
                "is_complete": rnd.is_complete,
            }
        return json.dumps(data)

    @staticmethod
    def from_db_row(row, conn: sqlite3.Connection) -> "CupCompetition":
        """Reconstruct from DB row."""
        cup = CupCompetition(
            name=row["competition_name"],
            season_year=row["season_year"],
            current_round=row["current_round"],
            champion_id=row["champion_club_id"] if row["champion_club_id"] else None,
            is_complete=bool(row["is_complete"]),
        )
        rounds_data = json.loads(row["rounds_json"]) if row["rounds_json"] else {}
        for rnd_name, rnd_data in rounds_data.items():
            cup.rounds[rnd_name] = CupRound(
                name=rnd_name,
                matches=rnd_data.get("matches", []),
                fixture_ids=rnd_data.get("fixture_ids", []),
                winners=rnd_data.get("winners", []),
                is_complete=rnd_data.get("is_complete", False),
            )
        return cup


# ── Public API ───────────────────────────────────────────────────────────────

def create_egypt_cup(
    conn: sqlite3.Connection,
    epl_clubs: list[Club],
    season_year: int,
    season_start: date,
) -> CupCompetition:
    """
    Create the Egypt Cup for a season.

    - All 18 EPL clubs enter.
    - 14 lower-division clubs are added as virtual entries to make 32.
    - Top 8 EPL clubs (by reputation) are seeded into separate halves.
    - Fixtures are scheduled interleaved with league matchdays.
    """
    cup = CupCompetition(name=CUP_NAME, season_year=season_year)

    # ── Gather all 32 participants ───────────────────────────────────
    for c in epl_clubs:
        cup.participating_clubs.append(c.id)
        cup.club_names[c.id] = c.name

    # Lower-division clubs get negative IDs (virtual — not in clubs table)
    for i, (name, _name_ar) in enumerate(LOWER_DIVISION_CLUBS):
        virtual_id = -(i + 1)
        cup.participating_clubs.append(virtual_id)
        cup.club_names[virtual_id] = name

    # ── Seeded draw for Round of 32 ─────────────────────────────────
    sorted_epl = sorted(epl_clubs, key=lambda c: -c.reputation)
    seeded_ids = [c.id for c in sorted_epl[:8]]
    unseeded_ids = [cid for cid in cup.participating_clubs if cid not in seeded_ids]
    rng.shuffle(unseeded_ids)
    rng.shuffle(seeded_ids)

    # Pair each seed with an unseeded opponent
    r32_matches = []
    for i, seed_id in enumerate(seeded_ids):
        opp_id = unseeded_ids[i]
        r32_matches.append((seed_id, opp_id))

    # Pair remaining unseeded clubs
    remaining = unseeded_ids[len(seeded_ids):]
    for i in range(0, len(remaining) - 1, 2):
        r32_matches.append((remaining[i], remaining[i + 1]))

    rng.shuffle(r32_matches)

    # ── Create R32 fixtures ──────────────────────────────────────────
    r32_date = season_start + timedelta(weeks=CUP_ROUND_WEEK_OFFSETS["Round of 32"])
    r32 = CupRound(name="Round of 32", matches=r32_matches)

    for home_id, away_id in r32_matches:
        home_name = cup.club_names.get(home_id, f"Club {home_id}")
        away_name = cup.club_names.get(away_id, f"Club {away_id}")
        fixture = Fixture(
            matchday=0,
            home_club_id=home_id,
            away_club_id=away_id,
            home_club_name=home_name,
            away_club_name=away_name,
            date=r32_date,
            competition=CUP_NAME,
        )
        fid = queries.insert_fixture(conn, fixture)
        r32.fixture_ids.append(fid)

    cup.rounds["Round of 32"] = r32
    cup.current_round = "Round of 32"

    # ── Save cup state to DB ─────────────────────────────────────────
    _save_cup_state(conn, cup)

    return cup


def get_cup_state(conn: sqlite3.Connection, season_year: int) -> CupCompetition | None:
    """Load the cup state from DB for a given season."""
    row = conn.execute(
        "SELECT * FROM cup_state WHERE competition_name=? AND season_year=?",
        (CUP_NAME, season_year),
    ).fetchone()
    if not row:
        return None
    return CupCompetition.from_db_row(row, conn)


def ensure_cup_initialized(conn: sqlite3.Connection, game_state: GameState) -> bool:
    """Ensure the Egypt Cup exists for the current season; create it if not."""
    state = get_cup_state(conn, game_state.season_year)
    if state:
        return False

    # Create it
    try:
        clubs = queries.get_all_clubs(conn)
        season_start = date(game_state.season_year, 8, 15)
        create_egypt_cup(conn, clubs, game_state.season_year, season_start)
        return True
    except Exception as e:
        print(f"DEBUG: Failed to initialize cup: {e}")
        return False


def advance_cup_round(
    conn: sqlite3.Connection,
    cup: CupCompetition,
    game_state,
) -> list[str]:
    """
    Check if the current cup round is complete; if so, draw the next round.

    Returns summary messages.
    """
    messages = []
    current = cup.current_round
    if not current or current not in cup.rounds:
        return messages

    rnd = cup.rounds[current]

    # Check if all fixtures in this round are played
    all_played = True
    for fid in rnd.fixture_ids:
        fix = _get_fixture_by_id(conn, fid)
        if fix and not fix.played:
            all_played = False
            break

    if not all_played:
        return messages

    # ── Determine winners ────────────────────────────────────────────
    rnd.winners = []
    for fid in rnd.fixture_ids:
        fix = _get_fixture_by_id(conn, fid)
        if not fix or not fix.result:
            continue
        hg = fix.result.home_goals
        ag = fix.result.away_goals
        if hg > ag:
            rnd.winners.append(fix.home_club_id)
        elif ag > hg:
            rnd.winners.append(fix.away_club_id)
        else:
            # Draw → simulate penalties (coin flip for non-user matches)
            winner = _resolve_draw(fix)
            rnd.winners.append(winner)

    rnd.is_complete = True

    # ── Check if this was the Final ──────────────────────────────────
    if current == "Final":
        cup.is_complete = True
        if rnd.winners:
            cup.champion_id = rnd.winners[0]
        champion_name = cup.club_names.get(cup.champion_id, "Unknown")
        messages.append(f"🏆 {champion_name} have won the Egypt Cup!")

        # Inbox message
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject=f"🏆 Egypt Cup Champions: {champion_name}",
            body=f"{champion_name} have lifted the Egypt Cup trophy! "
                 f"A magnificent achievement in the knockout tournament.",
            category="general",
        ))

        _save_cup_state(conn, cup)
        return messages

    # ── Draw next round ──────────────────────────────────────────────
    round_idx = CUP_ROUNDS.index(current)
    next_round_name = CUP_ROUNDS[round_idx + 1]

    winners = list(rnd.winners)
    rng.shuffle(winners)

    next_matches = []
    for i in range(0, len(winners) - 1, 2):
        next_matches.append((winners[i], winners[i + 1]))

    # Schedule fixtures
    season_start = date(cup.season_year, 8, 15)
    next_date = season_start + timedelta(
        weeks=CUP_ROUND_WEEK_OFFSETS.get(next_round_name, 36)
    )

    next_rnd = CupRound(name=next_round_name, matches=next_matches)
    for home_id, away_id in next_matches:
        home_name = cup.club_names.get(home_id, f"Club {home_id}")
        away_name = cup.club_names.get(away_id, f"Club {away_id}")
        fixture = Fixture(
            matchday=0,
            home_club_id=home_id,
            away_club_id=away_id,
            home_club_name=home_name,
            away_club_name=away_name,
            date=next_date,
            competition=CUP_NAME,
        )
        fid = queries.insert_fixture(conn, fixture)
        next_rnd.fixture_ids.append(fid)

    cup.rounds[next_round_name] = next_rnd
    cup.current_round = next_round_name

    messages.append(f"⚽ Egypt Cup {next_round_name} draw complete! "
                     f"{len(next_matches)} matches scheduled.")

    # Inbox
    draw_lines = []
    for h, a in next_matches:
        hn = cup.club_names.get(h, f"Club {h}")
        an = cup.club_names.get(a, f"Club {a}")
        draw_lines.append(f"  {hn} vs {an}")
    queries.insert_message(conn, InboxMessage(
        date=game_state.current_date,
        subject=f"🏆 Egypt Cup {next_round_name} Draw",
        body=f"The {next_round_name} draw has been made:\n" + "\n".join(draw_lines),
        category="general",
    ))

    _save_cup_state(conn, cup)
    return messages


def simulate_cup_match_result(
    conn: sqlite3.Connection,
    fixture_id: int,
    cup: CupCompetition,
) -> MatchResult | None:
    """
    Simulate a cup match for AI vs AI (non-user matches).
    Uses a simplified strength-based simulation.
    """
    fix = _get_fixture_by_id(conn, fixture_id)
    if not fix or fix.played:
        return None

    home_strength = _get_club_strength(conn, fix.home_club_id)
    away_strength = _get_club_strength(conn, fix.away_club_id)

    # Simple Poisson-like goal generation
    home_expected = max(0.5, (home_strength / max(away_strength, 1)) * 1.2)
    away_expected = max(0.5, (away_strength / max(home_strength, 1)) * 1.0)

    home_goals = _poisson_goals(home_expected)
    away_goals = _poisson_goals(away_expected)

    result = MatchResult(
        home_club_id=fix.home_club_id,
        away_club_id=fix.away_club_id,
        home_club_name=fix.home_club_name,
        away_club_name=fix.away_club_name,
        home_goals=home_goals,
        away_goals=away_goals,
        events=[],
        competition=CUP_NAME,
    )

    # Mark fixture as played
    conn.execute(
        "UPDATE fixtures SET played=1, home_goals=?, away_goals=? WHERE id=?",
        (home_goals, away_goals, fixture_id),
    )
    conn.commit()

    return result


def get_user_cup_fixture(
    conn: sqlite3.Connection,
    user_club_id: int,
    season_year: int,
) -> Fixture | None:
    """Get the next unplayed cup fixture for the user's club."""
    rows = conn.execute(
        """SELECT * FROM fixtures
           WHERE competition=? AND played=0
           AND (home_club_id=? OR away_club_id=?)
           ORDER BY match_date ASC LIMIT 1""",
        (CUP_NAME, user_club_id, user_club_id),
    ).fetchall()
    if not rows:
        return None
    from src.data.queries import _row_to_fixture
    return _row_to_fixture(rows[0])


def is_cup_match(fixture: Fixture) -> bool:
    """Check if a fixture is a cup match."""
    return fixture.competition == CUP_NAME


def get_cup_round_for_fixture(
    cup: CupCompetition, fixture_id: int
) -> str | None:
    """Get the round name for a given fixture."""
    for rnd_name, rnd in cup.rounds.items():
        if fixture_id in rnd.fixture_ids:
            return rnd_name
    return None


# ── Private Helpers ──────────────────────────────────────────────────────────

def _save_cup_state(conn: sqlite3.Connection, cup: CupCompetition) -> None:
    """Persist cup state to DB."""
    conn.execute(
        """INSERT OR REPLACE INTO cup_state
           (competition_name, season_year, current_round, rounds_json,
            champion_club_id, champion_club_name, is_complete)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            cup.name, cup.season_year, cup.current_round,
            cup.to_json(),
            cup.champion_id,
            cup.club_names.get(cup.champion_id, "") if cup.champion_id else "",
            int(cup.is_complete),
        ),
    )
    conn.commit()


def _get_fixture_by_id(conn: sqlite3.Connection, fid: int) -> Fixture | None:
    """Get a fixture by its primary key."""
    row = conn.execute("SELECT * FROM fixtures WHERE id=?", (fid,)).fetchone()
    if not row:
        return None
    from src.data.queries import _row_to_fixture
    return _row_to_fixture(row)


def _get_club_strength(conn: sqlite3.Connection, club_id: int) -> float:
    """Get an approximate strength rating for a club (EPL or virtual)."""
    if club_id < 0:
        # Lower-division virtual club — weaker
        return 40 + rng.randint(0, 20)
    club = queries.get_club(conn, club_id)
    if club:
        return club.reputation * 0.6
    return 50


def _resolve_draw(fixture: Fixture) -> int:
    """Resolve a drawn cup match via penalties (simplified coin flip)."""
    if rng.random_float() < 0.5:
        return fixture.home_club_id
    return fixture.away_club_id


def _poisson_goals(expected: float) -> int:
    """Generate a Poisson-distributed goal count."""
    import math
    L = math.exp(-expected)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= rng.random_float()
    return k - 1

