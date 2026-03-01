"""
Database seeding — populates a new game with clubs, generated players, and fixtures.

Players are generated procedurally based on club reputation tiers and
governorate talent profiles, producing realistic squad compositions.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from src.data.database import init_schema
from src.data import queries
from src.data.models import (
    Player, PlayerAttributes, PlayerContract, Club, ClubFinances,
    GameState,
)
from src.utils.config import Position, Foot, ATTR_MIN, ATTR_MAX
from src.utils import rng

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "seed"

# ── Name Pools (Fictionalized Egyptian-style names) ──────────────────────────

FIRST_NAMES = [
    "Ahmed", "Mohamed", "Mahmoud", "Omar", "Ali", "Hassan", "Youssef",
    "Ibrahim", "Khaled", "Tamer", "Amr", "Karim", "Mostafa", "Tarek",
    "Hossam", "Walid", "Sherif", "Nabil", "Hazem", "Ramy", "Eslam",
    "Abdallah", "Ashraf", "Bassem", "Ehab", "Fathy", "Gamal",
    "Hamdi", "Ismail", "Jihad", "Lotfy", "Magdy", "Nashaat",
    "Osama", "Reda", "Saad", "Shady", "Wael", "Zaki", "Ayman",
    "Hany", "Marwan", "Sameh", "Adel", "Emad", "Kareem", "Mido",
    "Nour", "Said", "Yasser", "Barakat", "Diab", "Fakhr",
    "Galal", "Helmy", "Issa", "Jawad", "Maher", "Nagib",
]

LAST_NAMES = [
    "El-Sayed", "Abdel-Rahman", "Hassan", "Ibrahim", "El-Din",
    "Mansour", "El-Naggar", "Farouk", "Shehata", "El-Masry",
    "Abou-Gabal", "Salah", "Zidan", "El-Hadary", "Barakat",
    "Hegazy", "Sobhy", "Ashour", "El-Wensh", "Elneny",
    "Trezeguet", "El-Shennawy", "Mohsen", "Ghaly", "Warda",
    "Hamdy", "Kahraba", "Kouka", "Marmoush", "El-Shahat",
    "Fathy", "Abdel-Shafy", "Gomaa", "Meteb", "Ekramy",
    "Aboutrika", "Moteab", "El-Khatib", "Samir", "Attia",
    "Ragab", "Soliman", "Abdelaal", "Raouf", "Zahran",
    "Nassar", "Gaber", "Nasser", "Refaat", "Shaaban",
]

# Squad composition template: position → count of players needed
SQUAD_TEMPLATE: dict[Position, int] = {
    Position.GK: 3,
    Position.CB: 4,
    Position.LB: 2,
    Position.RB: 2,
    Position.CDM: 2,
    Position.CM: 3,
    Position.CAM: 2,
    Position.LW: 2,
    Position.RW: 2,
    Position.ST: 3,
}

# Reputation tiers → ability ranges
REPUTATION_TIERS = {
    "elite":    (170, 200, 140, 175),   # rep >= 170: CA 140-175, PA 155-200
    "strong":   (140, 170, 110, 150),   # rep 140-169: CA 110-150, PA 130-170
    "mid":      (110, 140, 80, 130),    # rep 110-139: CA 80-130, PA 100-150
    "low":      (0,   110, 55, 110),    # rep < 110:  CA 55-110, PA 75-130
}


def _get_tier(reputation: int) -> tuple[int, int, int, int]:
    """Get ability ranges based on club reputation."""
    for tier_name, (rep_min, rep_max, ca_min, ca_max) in REPUTATION_TIERS.items():
        if reputation >= rep_min:
            return (rep_min, rep_max, ca_min, ca_max)
    return REPUTATION_TIERS["low"]


def _generate_player_attributes(position: Position, current_ability: int) -> PlayerAttributes:
    """Generate realistic attributes for a player based on position and ability."""
    # Base attribute level scaled from CA (1-200) → attrs (1-20)
    base = max(ATTR_MIN, min(ATTR_MAX, int(current_ability / 12)))
    variance = 3

    def attr(bonus: int = 0) -> int:
        val = rng.gaussian_clamped(base + bonus, variance, ATTR_MIN, ATTR_MAX)
        return int(round(val))

    # Position-specific attribute generation
    if position == Position.GK:
        return PlayerAttributes(
            finishing=attr(-5), passing=attr(-2), dribbling=attr(-4),
            first_touch=attr(-2), crossing=attr(-5), heading=attr(-3),
            long_shots=attr(-6), tackling=attr(-4), marking=attr(-3),
            free_kicks=attr(-4),
            pace=attr(-1), stamina=attr(-1), strength=attr(1),
            agility=attr(1), jumping=attr(1),
            composure=attr(1), vision=attr(-1), work_rate=attr(-1),
            leadership=attr(0), aggression=attr(-2), positioning=attr(0),
            decisions=attr(0),
            gk_reflexes=attr(3), gk_handling=attr(3), gk_positioning=attr(3),
            gk_one_on_ones=attr(2), gk_kicking=attr(1),
        )

    # Outfield GK attributes are low
    gk_base = max(ATTR_MIN, base - 6)

    if position in (Position.CB,):
        return PlayerAttributes(
            finishing=attr(-3), passing=attr(-1), dribbling=attr(-2),
            first_touch=attr(-1), crossing=attr(-3), heading=attr(3),
            long_shots=attr(-3), tackling=attr(3), marking=attr(3),
            free_kicks=attr(-2),
            pace=attr(0), stamina=attr(1), strength=attr(3),
            agility=attr(-1), jumping=attr(2),
            composure=attr(1), vision=attr(-1), work_rate=attr(1),
            leadership=attr(2), aggression=attr(1), positioning=attr(2),
            decisions=attr(1),
            gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
            gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
            gk_kicking=rng.randint(1, 3),
        )

    if position in (Position.LB, Position.RB):
        return PlayerAttributes(
            finishing=attr(-2), passing=attr(1), dribbling=attr(1),
            first_touch=attr(0), crossing=attr(3), heading=attr(0),
            long_shots=attr(-2), tackling=attr(2), marking=attr(2),
            free_kicks=attr(-1),
            pace=attr(3), stamina=attr(2), strength=attr(0),
            agility=attr(2), jumping=attr(0),
            composure=attr(0), vision=attr(0), work_rate=attr(2),
            leadership=attr(-1), aggression=attr(0), positioning=attr(1),
            decisions=attr(0),
            gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
            gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
            gk_kicking=rng.randint(1, 3),
        )

    if position in (Position.CDM,):
        return PlayerAttributes(
            finishing=attr(-2), passing=attr(2), dribbling=attr(0),
            first_touch=attr(1), crossing=attr(-1), heading=attr(1),
            long_shots=attr(0), tackling=attr(3), marking=attr(2),
            free_kicks=attr(0),
            pace=attr(0), stamina=attr(2), strength=attr(2),
            agility=attr(0), jumping=attr(1),
            composure=attr(1), vision=attr(1), work_rate=attr(2),
            leadership=attr(1), aggression=attr(1), positioning=attr(2),
            decisions=attr(2),
            gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
            gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
            gk_kicking=rng.randint(1, 3),
        )

    if position in (Position.CM,):
        return PlayerAttributes(
            finishing=attr(0), passing=attr(3), dribbling=attr(1),
            first_touch=attr(2), crossing=attr(0), heading=attr(0),
            long_shots=attr(1), tackling=attr(1), marking=attr(0),
            free_kicks=attr(1),
            pace=attr(0), stamina=attr(2), strength=attr(0),
            agility=attr(1), jumping=attr(0),
            composure=attr(1), vision=attr(3), work_rate=attr(1),
            leadership=attr(0), aggression=attr(0), positioning=attr(1),
            decisions=attr(2),
            gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
            gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
            gk_kicking=rng.randint(1, 3),
        )

    if position in (Position.CAM,):
        return PlayerAttributes(
            finishing=attr(2), passing=attr(3), dribbling=attr(3),
            first_touch=attr(3), crossing=attr(1), heading=attr(-2),
            long_shots=attr(2), tackling=attr(-3), marking=attr(-3),
            free_kicks=attr(2),
            pace=attr(1), stamina=attr(0), strength=attr(-1),
            agility=attr(2), jumping=attr(-1),
            composure=attr(2), vision=attr(3), work_rate=attr(0),
            leadership=attr(0), aggression=attr(-1), positioning=attr(1),
            decisions=attr(2),
            gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
            gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
            gk_kicking=rng.randint(1, 3),
        )

    if position in (Position.LW, Position.RW, Position.LM, Position.RM):
        return PlayerAttributes(
            finishing=attr(1), passing=attr(1), dribbling=attr(3),
            first_touch=attr(2), crossing=attr(3), heading=attr(-2),
            long_shots=attr(1), tackling=attr(-2), marking=attr(-3),
            free_kicks=attr(1),
            pace=attr(3), stamina=attr(1), strength=attr(-1),
            agility=attr(3), jumping=attr(-1),
            composure=attr(1), vision=attr(1), work_rate=attr(1),
            leadership=attr(-1), aggression=attr(0), positioning=attr(1),
            decisions=attr(1),
            gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
            gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
            gk_kicking=rng.randint(1, 3),
        )

    # ST / default
    return PlayerAttributes(
        finishing=attr(3), passing=attr(0), dribbling=attr(2),
        first_touch=attr(2), crossing=attr(-1), heading=attr(2),
        long_shots=attr(1), tackling=attr(-3), marking=attr(-4),
        free_kicks=attr(0),
        pace=attr(2), stamina=attr(0), strength=attr(1),
        agility=attr(2), jumping=attr(1),
        composure=attr(3), vision=attr(0), work_rate=attr(0),
        leadership=attr(0), aggression=attr(1), positioning=attr(3),
        decisions=attr(1),
        gk_reflexes=rng.randint(1, 3), gk_handling=rng.randint(1, 3),
        gk_positioning=rng.randint(1, 3), gk_one_on_ones=rng.randint(1, 3),
        gk_kicking=rng.randint(1, 3),
    )


def _generate_player(position: Position, club_rep: int,
                      governorate: str, shirt_number: int) -> Player:
    """Generate a single player with attributes based on position and club tier."""
    _, _, ca_min, ca_max = _get_tier(club_rep)

    # Generate ability with some variance — stars and duds
    current_ability = rng.randint(ca_min, ca_max)

    # Potential is always >= CA, with young players having more headroom
    age = _generate_age()
    pa_headroom = max(0, (28 - age) * 3)  # younger = more potential headroom
    potential_ability = min(200, current_ability + rng.randint(0, pa_headroom + 15))

    name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"

    # Preferred foot: 80% right, 12% left, 8% both
    foot_roll = rng.random_float()
    if foot_roll < 0.12:
        foot = Foot.LEFT
    elif foot_roll < 0.20:
        foot = Foot.BOTH
    else:
        foot = Foot.RIGHT

    attributes = _generate_player_attributes(position, current_ability)

    return Player(
        name=name,
        age=age,
        nationality="Egyptian",
        governorate=governorate,
        position=position,
        preferred_foot=foot,
        attributes=attributes,
        current_ability=current_ability,
        potential_ability=potential_ability,
        morale=rng.randint(40, 70),
        fitness=rng.randint(85, 100),
        form=round(rng.uniform(6.0, 7.5), 1),
        shirt_number=shirt_number,
        contract=PlayerContract(
            wage_weekly=_wage_from_ability(current_ability),
            contract_expiry=date(2025 + rng.randint(1, 4), 6, 30),
        ),
    )


def _generate_age() -> int:
    """Generate a realistic age distribution for a squad player."""
    # Weighted toward 22-30 (peak years), with tails at 17-21 and 31-36
    roll = rng.random_float()
    if roll < 0.12:
        return rng.randint(17, 20)    # Youth
    elif roll < 0.45:
        return rng.randint(21, 24)    # Developing
    elif roll < 0.80:
        return rng.randint(25, 29)    # Peak
    elif roll < 0.95:
        return rng.randint(30, 33)    # Veteran
    else:
        return rng.randint(34, 36)    # Twilight


def _wage_from_ability(ca: int) -> int:
    """Rough weekly wage in EGP based on current ability."""
    if ca >= 160:
        return rng.randint(200000, 400000)
    elif ca >= 130:
        return rng.randint(100000, 250000)
    elif ca >= 100:
        return rng.randint(40000, 120000)
    elif ca >= 70:
        return rng.randint(15000, 50000)
    else:
        return rng.randint(5000, 20000)


def seed_database(conn: sqlite3.Connection, game_seed: int = 42) -> GameState:
    """
    Seed a fresh database with clubs, players, and fixtures.
    Returns the initial GameState.
    """
    rng.seed(game_seed)
    init_schema(conn)

    # 1. Load and insert clubs
    clubs_data = _load_json("clubs.json")
    clubs: list[Club] = []
    for cd in clubs_data:
        club = Club(
            name=cd["name"],
            short_name=cd["short_name"],
            city=cd["city"],
            governorate=cd["governorate"],
            reputation=cd["reputation"],
            facilities_level=cd["facilities_level"],
            youth_rating=cd["youth_rating"],
            stadium_name=cd["stadium_name"],
            stadium_capacity=cd["stadium_capacity"],
            primary_color=cd["primary_color"],
            secondary_color=cd["secondary_color"],
            finances=ClubFinances(
                balance=cd["balance"],
                transfer_budget=cd["transfer_budget"],
                wage_budget_weekly=cd["wage_budget_weekly"],
                matchday_income=cd["matchday_income"],
                sponsorship_income_yearly=cd["sponsorship_income_yearly"],
                tv_revenue_yearly=cd["tv_revenue_yearly"],
            ),
        )
        club_id = queries.insert_club(conn, club)
        club.id = club_id
        clubs.append(club)

    # 2. Generate players for each club
    for club in clubs:
        shirt = 1
        for position, count in SQUAD_TEMPLATE.items():
            for _ in range(count):
                player = _generate_player(
                    position=position,
                    club_rep=club.reputation,
                    governorate=club.governorate,
                    shirt_number=shirt,
                )
                player.club_id = club.id
                queries.insert_player(conn, player)
                shirt += 1

    # 3. Initialize standings
    queries.init_standings(conn, clubs)

    # 4. Generate fixtures (done in league module, but create initial state)
    season_start = date(2025, 8, 15)
    game_state = GameState(
        save_name="default",
        season_year=2025,
        current_date=season_start,
        rng_seed=game_seed,
    )
    queries.save_game_state(conn, game_state)

    # 5. Insert a welcome inbox message
    from src.data.models import InboxMessage
    queries.insert_message(conn, InboxMessage(
        date=date(2025, 8, 15),
        subject="Welcome to Pharaoh Engine!",
        body="Your journey as a manager in the Egyptian Premier League begins now. Good luck!",
        category="general",
        is_read=False,
    ))

    return game_state


def _load_json(filename: str) -> list | dict:
    """Load a JSON file from the seed data directory."""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
