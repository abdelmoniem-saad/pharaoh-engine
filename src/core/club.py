"""
Club management — squad operations, starting XI, AI manager logic.
"""
from __future__ import annotations

import sqlite3

from src.data.models import Club, Player, TeamTactics
from src.data import queries
from src.core.tactics import auto_select_xi, preset_to_tactics, get_preset, PRESETS
from src.utils.config import Mentality
from src.utils import rng


def get_club_with_squad(conn: sqlite3.Connection, club_id: int) -> tuple[Club, list[Player]]:
    """Load a club and its full squad from the database."""
    club = queries.get_club(conn, club_id)
    if club is None:
        raise ValueError(f"Club {club_id} not found")
    squad = queries.get_players_by_club(conn, club_id)
    return club, squad


def prepare_team_for_match(club: Club, squad: list[Player]) -> TeamTactics:
    """
    Prepare a team's tactics for a match.
    For AI clubs, auto-selects the best XI based on club's preferred formation.
    Uses the club's persisted tactical sliders (pressing, tempo, width, def line).
    """
    starting_xi, bench = auto_select_xi(squad, club.formation)

    return TeamTactics(
        formation=club.formation,
        mentality=club.mentality,
        pressing_intensity=club.pressing_intensity,
        tempo=club.tempo,
        width=club.width,
        defensive_line=club.defensive_line,
        starting_xi=starting_xi,
        bench=bench,
    )


def ai_select_tactics(club: Club) -> None:
    """AI manager selects tactics based on club reputation and style."""
    # Higher rep clubs tend to be more attacking
    if club.reputation >= 170:
        presets = ["tiki_taka", "balanced", "all_out_attack"]
    elif club.reputation >= 140:
        presets = ["balanced", "counter_attack", "direct_play"]
    elif club.reputation >= 110:
        presets = ["counter_attack", "balanced", "park_the_bus"]
    else:
        presets = ["park_the_bus", "counter_attack", "balanced"]

    chosen_preset = get_preset(rng.choice(presets))
    club.formation = chosen_preset.formation
    club.mentality = chosen_preset.mentality
    club.pressing_intensity = chosen_preset.pressing_intensity
    club.tempo = chosen_preset.tempo
    club.width = chosen_preset.width
    club.defensive_line = chosen_preset.defensive_line


def calculate_wage_bill(squad: list[Player]) -> int:
    """Calculate total weekly wage bill for a squad."""
    return sum(p.contract.wage_weekly for p in squad)


def get_squad_depth(squad: list[Player]) -> dict[str, int]:
    """Get count of players per position group."""
    from src.utils.config import POSITION_GROUP_MAP, PositionGroup

    depth = {group.value: 0 for group in PositionGroup}
    for p in squad:
        group = POSITION_GROUP_MAP.get(p.position)
        if group:
            depth[group.value] += 1
    return depth


def get_captain(squad: list[Player]) -> Player | None:
    """Find the team captain, or the player with highest leadership."""
    captains = [p for p in squad if p.is_captain]
    if captains:
        return captains[0]
    if squad:
        return max(squad, key=lambda p: p.attributes.leadership)
    return None


def get_squad_average_age(squad: list[Player]) -> float:
    """Calculate the average age of a squad."""
    if not squad:
        return 0.0
    return sum(p.age for p in squad) / len(squad)


def get_squad_average_ability(squad: list[Player]) -> float:
    """Calculate the average current ability of a squad."""
    if not squad:
        return 0.0
    return sum(p.current_ability for p in squad) / len(squad)

