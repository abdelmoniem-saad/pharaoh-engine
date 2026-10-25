"""Durable inbox bids. Reading a letter never decides a transfer.

Seven calendar days are allowed from issue; the expiry date is exclusive.
Legacy letters are imported once without guessing decisions from read flags.
"""
from datetime import date, timedelta
import re
from threading import RLock

# Flet may dispatch two callbacks on separate threads sharing the career connection.
_decision_lock = RLock()


def import_letter(conn, message_id, issued, body):
    match = re.search(r"^TRANSFER_OFFER\|(\d+)\|(\d+)\|(\d+)\|(\d+)\|(\d+)\s*$", body, re.M)
    if not match:
        return
    from src.core.transfers import is_transfer_window_open
    issued_date = date.fromisoformat(issued)
    expiry = issued_date + timedelta(days=7)
    for offset in range(8):
        candidate = issued_date + timedelta(days=offset)
        if not is_transfer_window_open(candidate):
            expiry = min(expiry, candidate)
            break
    conn.execute("""INSERT OR IGNORE INTO incoming_offers
        (message_id, player_id, seller_id, buyer_id, fee, wage, expires_on)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (message_id, *map(int, match.groups()), expiry.isoformat()))


def refresh_offers(conn, today):
    with _decision_lock, conn:
        for row in conn.execute("""SELECT id, message_date, body FROM inbox
                WHERE body LIKE '%TRANSFER_OFFER|%' AND id NOT IN
                (SELECT message_id FROM incoming_offers)""").fetchall():
            import_letter(conn, row[0], row[1], row[2])
        conn.execute("""UPDATE incoming_offers SET status='expired', resolved_on=?
            WHERE status='pending' AND (expires_on<=? OR NOT EXISTS
            (SELECT 1 FROM players WHERE players.id=incoming_offers.player_id
             AND players.club_id=incoming_offers.seller_id))""", (today.isoformat(), today.isoformat()))


def get_offer(conn, message_id):
    row = conn.execute("SELECT * FROM incoming_offers WHERE message_id=?", (message_id,)).fetchone()
    return dict(row) if row else None


def decide_offer(conn, message_id, decision, today, user_club_id):
    """Return persisted status; conditional write serializes competing decisions.

    Offer state, ownership, both finances and the read flag commit together.
    No helper that commits independently is used inside this transaction.
    """
    if decision not in ('accepted', 'declined'):
        raise ValueError('Unknown offer decision')
    with _decision_lock, conn:
        changed = conn.execute("""UPDATE incoming_offers SET status=?, resolved_on=?
            WHERE message_id=? AND status='pending' AND seller_id=?""",
            (decision, today.isoformat(), message_id, user_club_id)).rowcount
        offer = get_offer(conn, message_id)
        if not changed:
            return offer['status'] if offer and offer['seller_id'] == user_club_id else 'unavailable'
        player = conn.execute('SELECT club_id,wage_weekly FROM players WHERE id=?', (offer['player_id'],)).fetchone()
        buyer = conn.execute('SELECT balance,transfer_budget FROM clubs WHERE id=?', (offer['buyer_id'],)).fetchone()
        seller = conn.execute('SELECT id FROM clubs WHERE id=?', (offer['seller_id'],)).fetchone()
        stale = (today.isoformat() >= offer['expires_on'] or not player
                 or player['club_id'] != offer['seller_id'] or not buyer or not seller
                 or offer['buyer_id'] == offer['seller_id'])
        if decision == 'accepted' and buyer:
            stale |= buyer['balance'] < offer['fee'] or buyer['transfer_budget'] < offer['fee']
        if stale:
            conn.execute("UPDATE incoming_offers SET status='expired' WHERE message_id=?", (message_id,))
            return 'expired'
        if decision == 'accepted':
            conn.execute("""UPDATE players SET club_id=?,wage_weekly=?,contract_expiry=?,
                transfer_listed=0,morale=60 WHERE id=?""", (offer['buyer_id'], offer['wage'],
                (today + timedelta(days=365*3)).isoformat(), offer['player_id']))
            conn.execute("""UPDATE clubs SET balance=balance+?,transfer_budget=transfer_budget+?,
                wage_bill_weekly=MAX(0,wage_bill_weekly-?) WHERE id=?""",
                (offer['fee'], offer['fee'], player['wage_weekly'], offer['seller_id']))
            conn.execute("""UPDATE clubs SET balance=balance-?,transfer_budget=transfer_budget-?,
                wage_bill_weekly=wage_bill_weekly+? WHERE id=?""",
                (offer['fee'], offer['fee'], offer['wage'], offer['buyer_id']))
            conn.execute("""UPDATE incoming_offers SET status='expired',resolved_on=?
                WHERE player_id=? AND status='pending'""", (today.isoformat(), offer['player_id']))
        conn.execute('UPDATE inbox SET is_read=1 WHERE id=?', (message_id,))
        return decision
