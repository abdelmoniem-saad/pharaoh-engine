"""
Random Events system — generates interactive events during the between-match periods
to keep the game engaging when advancing days.

Events fire with a ~12% daily chance and offer player choices that
affect finances, morale, board confidence, and fan happiness.
"""
from __future__ import annotations

import sqlite3
from datetime import date
from dataclasses import dataclass, field

from src.data.models import GameState, InboxMessage
from src.data import queries
from src.utils import rng


@dataclass
class EventChoice:
    text: str
    board_delta: int = 0
    fan_delta: int = 0
    ultras_trust_delta: int = 0
    choreo_momentum_delta: int = 0
    protest_risk_delta: int = 0
    finance_delta: int = 0
    morale_delta: int = 0
    response: str = ""


@dataclass
class GameEvent:
    key: str
    title: str
    body: str
    category: str = "general"
    choices: list[EventChoice] = field(default_factory=list)


# ── Event Templates ─────────────────────────────────────────────────────────

def _get_event_pool(gs: GameState, club) -> list[GameEvent]:
    """Return the pool of possible events based on current game context."""
    club_name = gs.user_club_name
    budget_str = f"{club.finances.balance:,}" if club else "0"

    events = [
        GameEvent(
            key="sponsor_offer",
            title="💼 Sponsorship Opportunity",
            body=f"A local company wants to sponsor {club_name}. "
                 f"They're offering a deal worth 500,000 EGP per year.",
            category="finance",
            choices=[
                EventChoice("Accept the deal", board_delta=2, fan_delta=1,
                            finance_delta=500_000,
                            response="The sponsorship deal has been signed! 💰 +500,000 EGP to the club balance."),
                EventChoice("Hold out for a better offer", board_delta=-1, fan_delta=0,
                            finance_delta=0,
                            response="You decided to wait. The board hopes a better deal comes along."),
            ],
        ),
        GameEvent(
            key="stadium_upgrade",
            title="🏟️ Stadium Upgrade Proposal",
            body="The facilities team proposes upgrading the training ground. "
                 "Cost: 1,000,000 EGP. This would improve youth development.",
            category="board",
            choices=[
                EventChoice("Approve the upgrade", board_delta=3, fan_delta=2,
                            finance_delta=-1_000_000,
                            response="The upgrade is approved! Training facilities will improve over the coming months. 🏗️"),
                EventChoice("Too expensive right now", board_delta=-1, fan_delta=0,
                            finance_delta=0,
                            response="The proposal is shelved for now. The board understands budget constraints."),
            ],
        ),
        GameEvent(
            key="player_interview",
            title="📰 Player Interview Request",
            body="A newspaper wants to interview your star player. "
                 "It could boost the player's profile but might also cause distractions.",
            category="media",
            choices=[
                EventChoice("Allow the interview", board_delta=0, fan_delta=3,
                            morale_delta=3,
                            response="The interview went well. Fans loved hearing from the player! 📰"),
                EventChoice("Deny — focus on training", board_delta=1, fan_delta=-1,
                            morale_delta=-2,
                            response="You blocked the interview. The player is a bit disappointed, but the board approves your focus."),
            ],
        ),
        GameEvent(
            key="fan_protest",
            title="😤 Fan Protest",
            body="A group of supporters are protesting outside the stadium, "
                 "demanding better results. How do you respond?",
            category="general",
            choices=[
                EventChoice("Meet with fan leaders", board_delta=1, fan_delta=5,
                            morale_delta=0,
                            response="You met with the fans and listened to their concerns. They appreciate the gesture. 🤝"),
                EventChoice("Release a public statement", board_delta=0, fan_delta=2,
                            morale_delta=0,
                            response="Your statement acknowledged the fans' frustration and promised improvements."),
                EventChoice("Ignore the protests", board_delta=-2, fan_delta=-5,
                            morale_delta=-2,
                            response="You ignored the protests. The fans are furious and the players are unsettled. 😡"),
            ],
        ),
        GameEvent(
            key="charity_match",
            title="🎗️ Charity Match Invitation",
            body="A local charity has invited your team to play a friendly exhibition match "
                 "for a children's hospital.",
            category="general",
            choices=[
                EventChoice("Accept — it's for a good cause", board_delta=2, fan_delta=4,
                            morale_delta=2, finance_delta=-50_000,
                            response="The charity match was a success! Great PR for the club and the players loved it. ❤️"),
                EventChoice("Decline — can't risk injuries", board_delta=0, fan_delta=-2,
                            morale_delta=0,
                            response="You declined. Some fans are disappointed, but the squad stays fresh."),
            ],
        ),
        GameEvent(
            key="transfer_rumor",
            title="📰 Transfer Rumour",
            body="Reports suggest a rival club is interested in one of your key players. "
                 "The media is asking for a comment.",
            category="transfer",
            choices=[
                EventChoice("'He's not for sale at any price'", board_delta=1, fan_delta=2,
                            morale_delta=2,
                            response="Your strong stance has reassured the fans and the player feels valued. 💪"),
                EventChoice("'Everyone has a price'", board_delta=0, fan_delta=-2,
                            morale_delta=-3,
                            response="The fans are worried, and the player is unsettled by your response. 😰"),
                EventChoice("'No comment'", board_delta=0, fan_delta=0,
                            morale_delta=-1,
                            response="The rumours continue to swirl. No resolution yet."),
            ],
        ),
        GameEvent(
            key="youth_breakthrough",
            title="🌟 Youth Academy Report",
            body="Your youth coaches report that a promising youngster is "
                 "performing exceptionally well in training. They recommend "
                 "promoting them to the first team squad.",
            category="general",
            choices=[
                EventChoice("Promote them immediately", board_delta=1, fan_delta=2,
                            morale_delta=1,
                            response="The young player is thrilled! They're ready to prove themselves in the first team. ⭐"),
                EventChoice("Let them develop more in the academy", board_delta=0, fan_delta=0,
                            morale_delta=0,
                            response="You decided they need more time. The youth coaches will continue their development."),
            ],
        ),
        GameEvent(
            key="rival_provocation",
            title="🔥 Rival Manager Comments",
            body="The opposing manager made provocative comments about your team "
                 "in the press, calling your tactics \"predictable\".",
            category="media",
            choices=[
                EventChoice("Fire back publicly", board_delta=-1, fan_delta=4,
                            morale_delta=2,
                            response="The fans love your fighting spirit! The dressing room is fired up. 🔥"),
                EventChoice("Take the high road", board_delta=2, fan_delta=0,
                            morale_delta=0,
                            response="You stayed professional. The board appreciates your composure. 🧘"),
                EventChoice("'We'll answer on the pitch'", board_delta=1, fan_delta=3,
                            morale_delta=1,
                            response="A classic response. The pressure is now on the team to deliver. ⚽"),
            ],
        ),
        GameEvent(
            key="training_injury",
            title="🏥 Training Ground Injury",
            body="One of your players picked up a knock during training. "
                 "The physio says they need 3-7 days of rest.",
            category="general",
            choices=[
                EventChoice("Rest them — better safe than sorry", board_delta=0, fan_delta=0,
                            morale_delta=0,
                            response="The player will rest for a few days. Better to be cautious. 🏥"),
                EventChoice("Push through — we need them", board_delta=0, fan_delta=0,
                            morale_delta=-2,
                            response="The player will try to push through, but they're not happy about it."),
            ],
        ),
        GameEvent(
            key="community_event",
            title="🏘️ Community Outreach",
            body="The local municipality is organizing a football festival "
                 "and has invited your players to attend and coach kids.",
            category="general",
            choices=[
                EventChoice("Send some players", board_delta=1, fan_delta=5,
                            morale_delta=2,
                            response="The event was a huge hit! Players enjoyed connecting with the community. 🏘️"),
                EventChoice("Sorry, we're too busy", board_delta=0, fan_delta=-2,
                            morale_delta=0,
                            response="The municipality is understanding, but the fans are disappointed."),
            ],
        ),
    ]

    return events


def generate_daily_event(conn: sqlite3.Connection,
                          gs: GameState) -> GameEvent | None:
    """
    Roll for a random event. ~12% daily chance.
    Returns a GameEvent with choices, or None.
    """
    if not rng.chance(0.12):
        return None

    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return None

    pool = _get_event_pool(gs, club)
    if not pool:
        return None

    event = rng.choice(pool)

    # Don't offer stadium upgrade if balance is too low
    if event.key == "stadium_upgrade" and club.finances.balance < 1_200_000:
        pool = [e for e in pool if e.key != "stadium_upgrade"]
        if not pool:
            return None
        event = rng.choice(pool)

    return event


def apply_event_choice(conn: sqlite3.Connection, gs: GameState,
                        event: GameEvent, choice_idx: int) -> str:
    """
    Apply the effects of the player's choice and return the response text.
    """
    if choice_idx < 0 or choice_idx >= len(event.choices):
        return "Invalid choice."

    choice = event.choices[choice_idx]
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return choice.response

    # Apply deltas
    if choice.board_delta != 0:
        club.board_confidence = max(0, min(100, club.board_confidence + choice.board_delta))
    if choice.fan_delta != 0:
        club.fan_happiness = max(0, min(100, club.fan_happiness + choice.fan_delta))
    if choice.ultras_trust_delta != 0:
        club.ultras_trust = max(0, min(100, club.ultras_trust + choice.ultras_trust_delta))
    if choice.choreo_momentum_delta != 0:
        club.choreo_momentum = max(0, min(100, club.choreo_momentum + choice.choreo_momentum_delta))
    if choice.protest_risk_delta != 0:
        club.protest_risk = max(0, min(100, club.protest_risk + choice.protest_risk_delta))
    if choice.finance_delta != 0:
        # Check the club can actually afford expenses
        if choice.finance_delta < 0 and club.finances.balance + choice.finance_delta < -500_000:
            # Can't afford it — abort the financial part, still apply other deltas
            queries.update_club(conn, club)
            queries.insert_message(conn, InboxMessage(
                date=gs.current_date,
                subject=event.title,
                body=f"{event.body}\n\n📌 Your decision: {choice.text}\n\n"
                     f"❌ The club couldn't afford the cost of {abs(choice.finance_delta):,} EGP. "
                     f"The decision was reversed.",
                category=event.category,
            ))
            return f"❌ Not enough funds! Need {abs(choice.finance_delta):,} EGP but balance is {club.finances.balance:,} EGP."

        club.finances.balance += choice.finance_delta
        # Income → increase transfer budget; Expense → decrease transfer budget
        if choice.finance_delta > 0:
            club.finances.transfer_budget += choice.finance_delta
        else:
            club.finances.transfer_budget = max(0, club.finances.transfer_budget + choice.finance_delta)

    queries.update_club(conn, club)

    # Apply morale delta to all players
    if choice.morale_delta != 0:
        players = queries.get_players_by_club(conn, gs.user_club_id)
        for p in players:
            p.morale = max(0, min(100, p.morale + choice.morale_delta))
            queries.update_player_stats(conn, p)

    # Inbox message with outcome
    queries.insert_message(conn, InboxMessage(
        date=gs.current_date,
        subject=event.title,
        body=f"{event.body}\n\n📌 Your decision: {choice.text}\n\n{choice.response}",
        category=event.category,
    ))

    return choice.response

