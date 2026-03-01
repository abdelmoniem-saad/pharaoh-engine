"""
Transfer market — negotiations, offers, and player trading.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from src.data.models import Player, Club, InboxMessage, GameState
from src.core.finance import can_afford_transfer, can_afford_wage
from src.data import queries
from src.utils import rng


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


def generate_ai_bids(conn: sqlite3.Connection, game_state: GameState) -> list[str]:
    """
    AI clubs make bids on transfer-listed user players.
    Called from advance_day. ~10% chance per listed player per day.
    """
    messages: list[str] = []
    listed = queries.search_players(
        conn, exclude_club_id=0, limit=100,
    )
    # Filter to only user's listed players
    user_listed = [p for p in listed
                   if p.club_id == game_state.user_club_id and p.transfer_listed]

    if not user_listed:
        return messages

    all_clubs = queries.get_all_clubs(conn)
    ai_clubs = [c for c in all_clubs if c.id != game_state.user_club_id]

    for player in user_listed:
        if not rng.chance(0.10):  # 10% daily chance
            continue

        value = estimate_player_value(player)
        # Find an AI club that can afford this player
        eligible = [c for c in ai_clubs
                    if c.finances.transfer_budget >= int(value * 0.7)]
        if not eligible:
            continue

        bidder = rng.choice(eligible)
        # AI bids 70-100% of estimated value
        bid_amount = int(value * rng.uniform(0.7, 1.0))

        # Store offer details in the message body with a parseable format
        body = (
            f"{bidder.name} have made an offer of {bid_amount:,} EGP "
            f"for {player.name}.\n\n"
            f"Player Value: {value:,} EGP\n"
            f"Offer: {bid_amount:,} EGP\n\n"
            f"TRANSFER_OFFER|{player.id}|{player.club_id}|{bidder.id}|{bid_amount}|{player.contract.wage_weekly}"
        )

        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject=f"📨 Offer for {player.name} from {bidder.short_name}",
            body=body,
            category="transfer",
        ))
        messages.append(f"{bidder.name} bid {bid_amount:,} EGP for {player.name}")

    return messages


def check_expiring_contracts(conn: sqlite3.Connection,
                              game_state: GameState) -> list[str]:
    """
    Check for expiring contracts and send warning messages.
    Called monthly from advance_day.
    """
    messages: list[str] = []
    squad = queries.get_players_by_club(conn, game_state.user_club_id)

    expiring_soon = []
    for p in squad:
        if not p.contract.contract_expiry:
            continue
        days_left = (p.contract.contract_expiry - game_state.current_date).days
        if 0 < days_left <= 90:
            expiring_soon.append((p, days_left))

    if expiring_soon:
        lines = []
        for p, days in expiring_soon:
            lines.append(f"• {p.name} ({p.position.value}) — {days} days remaining")
        body = "The following players have contracts expiring soon:\n\n" + "\n".join(lines)
        body += "\n\nConsider renewing their contracts or risk losing them."

        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject=f"⚠️ {len(expiring_soon)} Contract(s) Expiring",
            body=body,
            category="board",
        ))
        messages.append(f"{len(expiring_soon)} contracts expiring soon")

    return messages


