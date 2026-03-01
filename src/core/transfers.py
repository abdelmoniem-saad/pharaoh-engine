"""
Transfer market — negotiations, offers, and player trading.

Negotiations are async (take days, not instant):
  Phase 1: Fee negotiation → submit offer → next day get response
  Phase 2: Wage negotiation → offer wage → next day player responds
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from dataclasses import dataclass

from src.data.models import Player, Club, InboxMessage, GameState
from src.core.finance import can_afford_transfer, can_afford_wage
from src.data import queries
from src.utils import rng


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class Negotiation:
    """A single ongoing transfer negotiation."""
    id: int
    player_id: int
    player_name: str
    from_club_id: int
    from_club_name: str
    to_club_id: int
    to_club_name: str
    phase: str          # "fee" or "wage"
    status: str         # "pending", "accepted", "rejected", "completed", "expired"
    current_offer: int
    asking_price: int
    counter_price: int
    wage_offer: int
    current_wage: int
    attempt: int
    max_attempts: int
    submitted_date: str
    respond_date: str
    direction: str      # "user_buying" or "user_selling"


# ── Valuation ────────────────────────────────────────────────────────────────

def estimate_player_value(player: Player) -> int:
    """
    Estimate a player's transfer value in EGP.

    Factors: current ability, potential, age, contract length.
    """
    base_value = player.current_ability * 50000

    if player.age <= 21:
        age_mod = 1.5
    elif player.age <= 27:
        age_mod = 1.2
    elif player.age <= 30:
        age_mod = 1.0
    elif player.age <= 33:
        age_mod = 0.6
    else:
        age_mod = 0.3

    pa_mod = 1.0 + (player.potential_ability - player.current_ability) / 200.0

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
    return int(max(100000, value))


def can_sign_player(buying_club: Club, player: Player, fee: int) -> tuple[bool, str]:
    """Check if a club can sign a player. Returns (success, reason)."""
    if not can_afford_transfer(buying_club, fee):
        return False, "Insufficient transfer budget"

    suggested_wage = player.contract.wage_weekly
    if not can_afford_wage(buying_club, suggested_wage):
        return False, "Cannot afford player wages"

    return True, "Transfer possible"


def negotiate_fee(asking_price: int, offer: int, attempt: int = 1) -> tuple[bool, int]:
    """
    Negotiate a transfer fee.

    Returns (accepted, counter_price).
    Counter-offers always go DOWN each attempt to converge toward the buyer.
    """
    # Accept threshold: 90% of asking price
    if offer >= asking_price * 0.90:
        return True, offer

    # Too low — below 50%: flat reject
    if offer < asking_price * 0.50:
        return False, asking_price

    # Counter-offer: starts near asking and drops toward midpoint each attempt
    #   attempt 1: counter = asking * 0.95  (barely budges)
    #   attempt 2: counter = asking * 0.88  (comes down more)
    #   attempt 3: counter = asking * 0.82  (final offer, close to accept threshold)
    discount = 0.05 + (attempt - 1) * 0.07
    counter = int(asking_price * (1.0 - discount))

    # Counter should never be higher than asking price
    counter = min(counter, asking_price)
    # Counter should never be lower than the buyer's offer
    counter = max(counter, offer)

    return False, counter


# ── Async negotiation DB operations ─────────────────────────────────────────

def submit_transfer_offer(conn: sqlite3.Connection, gs: GameState,
                           player: Player, offer: int,
                           direction: str = "user_buying") -> Negotiation:
    """
    Submit a new transfer offer. The response comes the next day.
    """
    from_club = queries.get_club(conn, player.club_id) if player.club_id else None
    to_club = queries.get_club(conn, gs.user_club_id)
    asking = estimate_player_value(player)

    respond = (gs.current_date + timedelta(days=1)).isoformat()

    conn.execute("""
        INSERT INTO transfer_negotiations
        (player_id, player_name, from_club_id, from_club_name,
         to_club_id, to_club_name, phase, status,
         current_offer, asking_price, counter_price,
         wage_offer, current_wage, attempt, max_attempts,
         submitted_date, respond_date, direction)
        VALUES (?, ?, ?, ?, ?, ?, 'fee', 'pending',
                ?, ?, 0, 0, ?, 1, 3, ?, ?, ?)
    """, (
        player.id, player.name,
        player.club_id or 0, from_club.name if from_club else "Free Agent",
        gs.user_club_id, to_club.name if to_club else "",
        offer, asking,
        player.contract.wage_weekly,
        gs.current_date.isoformat(), respond,
        direction,
    ))
    conn.commit()
    neg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    return _get_negotiation(conn, neg_id)


def submit_counter_response(conn: sqlite3.Connection, gs: GameState,
                              neg_id: int, new_offer: int) -> None:
    """
    Submit a revised offer (counter-to-counter). Response comes next day.
    """
    respond = (gs.current_date + timedelta(days=1)).isoformat()
    conn.execute("""
        UPDATE transfer_negotiations
        SET current_offer = ?, status = 'pending',
            attempt = attempt + 1,
            submitted_date = ?, respond_date = ?
        WHERE id = ?
    """, (new_offer, gs.current_date.isoformat(), respond, neg_id))
    conn.commit()


def submit_wage_offer(conn: sqlite3.Connection, gs: GameState,
                       neg_id: int, wage: int) -> None:
    """
    After fee is agreed, submit a wage offer to the player. Response next day.
    """
    respond = (gs.current_date + timedelta(days=1)).isoformat()
    conn.execute("""
        UPDATE transfer_negotiations
        SET phase = 'wage', wage_offer = ?, status = 'pending',
            submitted_date = ?, respond_date = ?
        WHERE id = ?
    """, (wage, gs.current_date.isoformat(), respond, neg_id))
    conn.commit()


def accept_negotiation(conn: sqlite3.Connection, neg: Negotiation) -> None:
    """Finalize a completed negotiation — execute the actual transfer."""
    queries.transfer_player(
        conn, neg.player_id, neg.from_club_id, neg.to_club_id,
        fee=neg.current_offer, wage=neg.wage_offer,
    )
    conn.execute("UPDATE transfer_negotiations SET status='completed' WHERE id=?",
                 (neg.id,))
    conn.commit()


def cancel_negotiation(conn: sqlite3.Connection, neg_id: int) -> None:
    """Cancel / withdraw from a negotiation."""
    conn.execute("UPDATE transfer_negotiations SET status='expired' WHERE id=?",
                 (neg_id,))
    conn.commit()


def get_user_negotiations(conn: sqlite3.Connection, user_club_id: int) -> list[Negotiation]:
    """Get all active negotiations for the user."""
    rows = conn.execute("""
        SELECT * FROM transfer_negotiations
        WHERE (to_club_id = ? OR from_club_id = ?)
          AND status IN ('pending', 'fee_agreed', 'countered')
        ORDER BY respond_date ASC
    """, (user_club_id, user_club_id)).fetchall()
    return [_row_to_negotiation(r) for r in rows]


def _get_negotiation(conn: sqlite3.Connection, neg_id: int) -> Negotiation:
    row = conn.execute("SELECT * FROM transfer_negotiations WHERE id=?", (neg_id,)).fetchone()
    return _row_to_negotiation(row)


def _row_to_negotiation(row) -> Negotiation:
    return Negotiation(
        id=row[0],
        player_id=row[1],
        player_name=row[2],
        from_club_id=row[3],
        from_club_name=row[4],
        to_club_id=row[5],
        to_club_name=row[6],
        phase=row[7],
        status=row[8],
        current_offer=row[9],
        asking_price=row[10],
        counter_price=row[11],
        wage_offer=row[12],
        current_wage=row[13],
        attempt=row[14],
        max_attempts=row[15],
        submitted_date=row[16],
        respond_date=row[17],
        direction=row[18],
    )


# ── Daily processing (called from advance_day) ──────────────────────────────

def process_pending_negotiations(conn: sqlite3.Connection,
                                   gs: GameState) -> list[str]:
    """
    Process all negotiations whose respond_date has arrived.
    Generates inbox messages with results.
    """
    messages: list[str] = []
    today = gs.current_date.isoformat()

    rows = conn.execute("""
        SELECT * FROM transfer_negotiations
        WHERE status = 'pending' AND respond_date <= ?
    """, (today,)).fetchall()

    for row in rows:
        neg = _row_to_negotiation(row)

        if neg.phase == "fee":
            _process_fee_response(conn, gs, neg, messages)
        elif neg.phase == "wage":
            _process_wage_response(conn, gs, neg, messages)

    return messages


def _process_fee_response(conn: sqlite3.Connection, gs: GameState,
                           neg: Negotiation, messages: list[str]) -> None:
    """AI club responds to a fee offer."""
    accepted, counter = negotiate_fee(neg.asking_price, neg.current_offer, neg.attempt)

    if accepted:
        # Fee agreed — move to wage phase
        conn.execute("""
            UPDATE transfer_negotiations
            SET status = 'fee_agreed', counter_price = ?
            WHERE id = ?
        """, (neg.current_offer, neg.id))
        conn.commit()

        body = (
            f"✅ {neg.from_club_name} have accepted your offer of "
            f"{neg.current_offer:,} EGP for {neg.player_name}!\n\n"
            f"You now need to agree personal terms with the player.\n"
            f"Go to Transfer Market → 📋 Negotiations to offer wages.\n\n"
            f"FEE_AGREED|{neg.id}"
        )
        queries.insert_message(conn, InboxMessage(
            date=gs.current_date,
            subject=f"✅ Fee Agreed: {neg.player_name}",
            body=body, category="transfer",
        ))
        messages.append(f"Fee agreed for {neg.player_name}: {neg.current_offer:,} EGP")

    elif neg.attempt >= neg.max_attempts:
        # Exhausted attempts — deal collapsed
        conn.execute("UPDATE transfer_negotiations SET status='rejected' WHERE id=?",
                     (neg.id,))
        conn.commit()

        body = (
            f"❌ {neg.from_club_name} have ended negotiations for {neg.player_name}.\n\n"
            f"Your final offer of {neg.current_offer:,} EGP was not enough.\n"
            f"Their valuation: {neg.asking_price:,} EGP."
        )
        queries.insert_message(conn, InboxMessage(
            date=gs.current_date,
            subject=f"❌ Deal Collapsed: {neg.player_name}",
            body=body, category="transfer",
        ))
        messages.append(f"Negotiations broke down for {neg.player_name}")

    else:
        # Counter-offer from the selling club
        conn.execute("""
            UPDATE transfer_negotiations
            SET status = 'countered', counter_price = ?
            WHERE id = ?
        """, (counter, neg.id))
        conn.commit()

        body = (
            f"↩️ {neg.from_club_name} have rejected your offer of "
            f"{neg.current_offer:,} EGP for {neg.player_name}.\n\n"
            f"They counter-offer: {counter:,} EGP\n"
            f"(Attempt {neg.attempt}/{neg.max_attempts})\n\n"
            f"Go to Transfer Market → 📋 Negotiations to respond.\n\n"
            f"COUNTER_OFFER|{neg.id}|{counter}"
        )
        queries.insert_message(conn, InboxMessage(
            date=gs.current_date,
            subject=f"↩️ Counter: {neg.player_name} — {counter:,} EGP",
            body=body, category="transfer",
        ))
        messages.append(f"Counter-offer for {neg.player_name}: {counter:,} EGP")


def _process_wage_response(conn: sqlite3.Connection, gs: GameState,
                             neg: Negotiation, messages: list[str]) -> None:
    """Player responds to wage offer."""
    min_acceptable = int(neg.current_wage * 0.85)

    if neg.wage_offer >= min_acceptable:
        # Player accepts — complete the transfer!
        conn.execute("UPDATE transfer_negotiations SET status='completed' WHERE id=?",
                     (neg.id,))
        conn.commit()

        # Execute the actual transfer
        queries.transfer_player(
            conn, neg.player_id, neg.from_club_id, neg.to_club_id,
            fee=neg.current_offer, wage=neg.wage_offer,
        )

        body = (
            f"🎉 {neg.player_name} has agreed personal terms!\n\n"
            f"Transfer fee: {neg.current_offer:,} EGP\n"
            f"Weekly wage: {neg.wage_offer:,} EGP\n\n"
            f"The transfer is complete. Welcome to the squad!"
        )
        queries.insert_message(conn, InboxMessage(
            date=gs.current_date,
            subject=f"🎉 Transfer Complete: {neg.player_name}",
            body=body, category="transfer",
        ))
        messages.append(f"Transfer complete: {neg.player_name} signed!")

    else:
        # Player rejects wage
        wanted = int(neg.current_wage * 0.95)
        conn.execute("""
            UPDATE transfer_negotiations
            SET status = 'fee_agreed', counter_price = ?
            WHERE id = ?
        """, (wanted, neg.id))
        conn.commit()

        body = (
            f"❌ {neg.player_name} has rejected your wage offer of "
            f"{neg.wage_offer:,} EGP/wk.\n\n"
            f"The player wants at least {wanted:,} EGP/wk.\n"
            f"The transfer fee ({neg.current_offer:,} EGP) is still agreed.\n\n"
            f"Go to Transfer Market → 📋 Negotiations to revise your offer.\n\n"
            f"WAGE_REJECTED|{neg.id}|{wanted}"
        )
        queries.insert_message(conn, InboxMessage(
            date=gs.current_date,
            subject=f"❌ Wage Rejected: {neg.player_name}",
            body=body, category="transfer",
        ))
        messages.append(f"{neg.player_name} rejected wage offer of {neg.wage_offer:,}")


# ── AI bids on user's listed players ─────────────────────────────────────────

def generate_ai_bids(conn: sqlite3.Connection, game_state: GameState) -> list[str]:
    """
    AI clubs make bids on transfer-listed user players.
    Called from advance_day. ~10% chance per listed player per day.
    """
    messages: list[str] = []
    listed = queries.search_players(conn, exclude_club_id=0, limit=100)
    user_listed = [p for p in listed
                   if p.club_id == game_state.user_club_id and p.transfer_listed]

    if not user_listed:
        return messages

    all_clubs = queries.get_all_clubs(conn)
    ai_clubs = [c for c in all_clubs if c.id != game_state.user_club_id]

    for player in user_listed:
        if not rng.chance(0.10):
            continue

        value = estimate_player_value(player)
        eligible = [c for c in ai_clubs
                    if c.finances.transfer_budget >= int(value * 0.7)]
        if not eligible:
            continue

        bidder = rng.choice(eligible)
        bid_amount = int(value * rng.uniform(0.7, 1.0))

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
            body=body, category="transfer",
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
            body=body, category="board",
        ))
        messages.append(f"{len(expiring_soon)} contracts expiring soon")

    return messages

