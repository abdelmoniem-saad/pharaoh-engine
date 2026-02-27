"""
Transfer market — negotiations, offers, and player trading.

Phase 2 module — stub with basic transfer logic.
"""
from __future__ import annotations

from src.data.models import Player, Club, PlayerContract
from src.core.finance import can_afford_transfer, can_afford_wage
from src.core.player import calculate_overall_rating
from src.utils import rng
from datetime import date


def estimate_player_value(player: Player) -> int:
    """
    Estimate a player's transfer value in EGP.

    Factors: current ability, potential, age, contract length.
    """
    base_value = player.current_ability * 50000  # Base: CA × 50K

    # Age modifier
    if player.age <= 21:
        age_mod = 1.5  # Young talent premium
    elif player.age <= 27:
        age_mod = 1.2  # Peak years
    elif player.age <= 30:
        age_mod = 1.0
    elif player.age <= 33:
        age_mod = 0.6
    else:
        age_mod = 0.3

    # Potential modifier (PA headroom adds value)
    pa_mod = 1.0 + (player.potential_ability - player.current_ability) / 200.0

    # Contract modifier (less time = less value)
    if player.contract.contract_expiry:
        days_left = (player.contract.contract_expiry - date.today()).days
        if days_left <= 180:
            contract_mod = 0.3
        elif days_left <= 365:
            contract_mod = 0.6
        else:
            contract_mod = 1.0
    else:
        contract_mod = 0.5

    value = base_value * age_mod * pa_mod * contract_mod
    return int(max(100000, value))  # Minimum 100K EGP


def can_sign_player(buying_club: Club, player: Player, fee: int) -> tuple[bool, str]:
    """Check if a club can sign a player. Returns (success, reason)."""
    if not can_afford_transfer(buying_club, fee):
        return False, "Insufficient transfer budget"

    suggested_wage = player.contract.wage_weekly
    if not can_afford_wage(buying_club, suggested_wage):
        return False, "Cannot afford player wages"

    return True, "Transfer possible"


def negotiate_fee(asking_price: int, offer: int) -> tuple[bool, int]:
    """
    Simple negotiation: if offer >= 90% of asking, auto-accept.
    Otherwise, counter-offer.
    """
    if offer >= asking_price * 0.9:
        return True, offer

    # Counter-offer: somewhere between asking and offer
    counter = int((asking_price * 0.85 + offer * 0.15))
    return False, counter

