"""
Media pressure system — headlines, press conferences, narrative events.

Generates detailed match reports, varied headlines, and random mid-season events.
"""
from __future__ import annotations

from src.data.models import MatchResult, InboxMessage
from src.utils.config import MatchEventType
from src.utils import rng
from datetime import date


# Headline templates for different scenarios
HEADLINES = {
    "big_win": [
        "{club} demolish {opponent} in stunning display!",
        "Dominant {club} cruise past {opponent}!",
        "{club} send a statement with emphatic victory!",
        "Ruthless {club} put {opponent} to the sword!",
    ],
    "narrow_win": [
        "{club} edge past {opponent} in tight affair",
        "Hard-fought victory for {club} against {opponent}",
        "{club} grab all three points against resilient {opponent}",
        "Late drama as {club} overcome {opponent}",
    ],
    "draw": [
        "Honours even as {club} and {opponent} share the spoils",
        "{club} held to a draw by determined {opponent}",
        "Neither side can find a winner in tense encounter",
        "Stalemate between {club} and {opponent}",
    ],
    "loss": [
        "Disappointing day for {club} as {opponent} take the points",
        "{club} suffer defeat at the hands of {opponent}",
        "Questions for {club} manager after loss to {opponent}",
        "{club} fall short against resolute {opponent}",
    ],
    "big_loss": [
        "Crisis at {club} after humiliating defeat to {opponent}!",
        "{club} capitulate in shocking loss to {opponent}!",
        "Manager under pressure after {club}'s dismal showing against {opponent}!",
        "Nightmare for {club} as {opponent} run riot!",
    ],
}

# ── Random mid-season event templates ────────────────────────────────────────
RANDOM_EVENTS = [
    {
        "subject": "🎤 Captain's Speech",
        "body": "The captain gathered the squad for a motivational talk before training. "
                "\"We need to stay focused and keep pushing,\" he told his teammates. "
                "Morale in the dressing room seems lifted.",
        "category": "general",
    },
    {
        "subject": "📰 Local Press Praise",
        "body": "The local newspapers have praised {club}'s recent performances. "
                "\"The fans are starting to believe again,\" one columnist wrote.",
        "category": "media",
    },
    {
        "subject": "🎨 Fan Tifo Planned",
        "body": "The ultras are planning a spectacular tifo display for the next home match. "
                "The club have given their blessing and supporters are buzzing with excitement.",
        "category": "general",
    },
    {
        "subject": "🏥 Minor Training Knock",
        "body": "{player} felt some discomfort during training but the medical staff say it's nothing serious. "
                "He should be available for the next match.",
        "category": "general",
    },
    {
        "subject": "🏛️ Board Member Visits Training",
        "body": "A board member visited the training ground today to observe the squad in action. "
                "He expressed satisfaction with the work being done by the coaching staff.",
        "category": "board",
    },
    {
        "subject": "📈 Scout Report Filed",
        "body": "Your scouting team has submitted a report on several promising young players in the lower divisions. "
                "They recommend keeping an eye on the transfer market.",
        "category": "transfer",
    },
    {
        "subject": "🎉 Community Outreach",
        "body": "{club} players visited a local school today as part of the club's community program. "
                "{player} was particularly popular with the children.",
        "category": "general",
    },
    {
        "subject": "💪 Training Intensity Up",
        "body": "The coaching staff have increased the intensity of training sessions this week. "
                "The squad is working hard and the fitness levels are improving.",
        "category": "general",
    },
    {
        "subject": "🏟️ Stadium Maintenance",
        "body": "Routine maintenance work is being carried out at the stadium this week. "
                "The pitch has been re-seeded and the facilities are in good shape.",
        "category": "general",
    },
    {
        "subject": "📺 TV Feature",
        "body": "A national TV channel is planning a feature on {club}'s season so far. "
                "The coverage should help boost the club's profile across the country.",
        "category": "media",
    },
    {
        "subject": "🧤 Goalkeeper Training Session",
        "body": "The goalkeeping coach organized a special session today. "
                "The keepers looked sharp and the coaching staff are pleased with their progress.",
        "category": "general",
    },
    {
        "subject": "⚡ Rivalry Tensions",
        "body": "Tensions are rising ahead of the next fixture. Fans on social media are already "
                "trading barbs. The players know this one matters.",
        "category": "media",
    },
    {
        "subject": "🍽️ Team Dinner",
        "body": "The squad went out for a team dinner last night. {player} organised the event "
                "and the players enjoyed some time to bond away from the pitch.",
        "category": "general",
    },
    {
        "subject": "📊 Data Analysis Update",
        "body": "The performance analysts have presented new data insights to the coaching staff. "
                "Tactical adjustments may be coming based on opponent weaknesses identified.",
        "category": "general",
    },
    {
        "subject": "🌟 Youth Prospect Impresses",
        "body": "A young player from the academy impressed during a behind-closed-doors friendly. "
                "The coaching staff are considering giving him more first-team involvement.",
        "category": "general",
    },
]


def generate_match_headline(result: MatchResult, user_club_id: int) -> str:
    """Generate a media headline after a match involving the user's club."""
    is_home = result.home_club_id == user_club_id

    if is_home:
        user_goals = result.home_goals
        opp_goals = result.away_goals
        club_name = result.home_club_name
        opp_name = result.away_club_name
    else:
        user_goals = result.away_goals
        opp_goals = result.home_goals
        club_name = result.away_club_name
        opp_name = result.home_club_name

    diff = user_goals - opp_goals

    if diff >= 3:
        category = "big_win"
    elif diff > 0:
        category = "narrow_win"
    elif diff == 0:
        category = "draw"
    elif diff >= -2:
        category = "loss"
    else:
        category = "big_loss"

    template = rng.choice(HEADLINES[category])
    return template.format(club=club_name, opponent=opp_name)


def _build_match_report_body(result: MatchResult, user_club_id: int) -> str:
    """Build a detailed match report with scorers, stats, and narrative."""
    is_home = result.home_club_id == user_club_id
    user_goals = result.home_goals if is_home else result.away_goals
    opp_goals = result.away_goals if is_home else result.home_goals

    lines = [result.score_display, ""]

    # ── Scorers ──────────────────────────────────────────────
    goals = [e for e in result.events if e.event_type == MatchEventType.GOAL]
    if goals:
        lines.append("⚽ Goals:")
        for g in goals:
            assist_text = f" (assist: {g.second_player_name})" if g.second_player_name else ""
            lines.append(f"  {g.minute}' {g.player_name}{assist_text}")
        lines.append("")

    # ── Key stats ────────────────────────────────────────────
    home_poss = result.home_stats.possession
    away_poss = result.away_stats.possession
    lines.append(f"📊 Possession: {home_poss:.0f}% - {away_poss:.0f}%")
    lines.append(
        f"🎯 Shots: {result.home_stats.shots} ({result.home_stats.shots_on_target} on target) "
        f"vs {result.away_stats.shots} ({result.away_stats.shots_on_target} on target)"
    )

    # ── Cards ────────────────────────────────────────────────
    cards = [e for e in result.events
             if e.event_type in (MatchEventType.YELLOW_CARD, MatchEventType.RED_CARD)]
    if cards:
        card_strs = []
        for c in cards:
            icon = "🟡" if c.event_type == MatchEventType.YELLOW_CARD else "🟥"
            card_strs.append(f"{icon} {c.player_name} ({c.minute}')")
        lines.append(f"Cards: {', '.join(card_strs)}")

    # ── Injuries ─────────────────────────────────────────────
    injuries = [e for e in result.events if e.event_type == MatchEventType.INJURY]
    if injuries:
        for inj in injuries:
            lines.append(f"🏥 {inj.player_name} was injured ({inj.minute}')")

    # ── Man of the Match ─────────────────────────────────────
    if result.player_ratings:
        best_pid = max(result.player_ratings, key=result.player_ratings.get)
        best_rating = result.player_ratings[best_pid]
        # Find name from events or use ID
        best_name = str(best_pid)
        for e in result.events:
            if e.player_id == best_pid:
                best_name = e.player_name
                break
            if e.second_player_id == best_pid:
                best_name = e.second_player_name
                break
        if best_rating >= 7.5:
            lines.append(f"\n⭐ Man of the Match: {best_name} ({best_rating})")

    # ── Narrative line ───────────────────────────────────────
    lines.append("")
    diff = user_goals - opp_goals
    if diff >= 3:
        lines.append(rng.choice([
            "A comprehensive victory that will delight the fans.",
            "A dominant display from start to finish.",
            "The team showed their class with a ruthless performance.",
        ]))
    elif diff > 0:
        lines.append(rng.choice([
            "A hard-earned three points that keeps the momentum going.",
            "Not always pretty, but the result is what matters.",
            "A professional performance to take all three points.",
        ]))
    elif diff == 0:
        lines.append(rng.choice([
            "A point gained or two dropped? The debate will rage on.",
            "The team will feel they could have done more today.",
            "A fair result in the end, though chances were there.",
        ]))
    elif diff >= -2:
        lines.append(rng.choice([
            "The manager will have plenty to think about after this one.",
            "A setback, but there's time to recover.",
            "Tough questions will be asked after this defeat.",
        ]))
    else:
        lines.append(rng.choice([
            "A performance the players will want to forget quickly.",
            "The dressing room will be a tough place after this.",
            "Serious concerns for the manager after this hammering.",
        ]))

    return "\n".join(lines)


def create_match_report_message(result: MatchResult, user_club_id: int,
                                  match_date: date) -> InboxMessage:
    """Create an inbox message with the match report."""
    headline = generate_match_headline(result, user_club_id)
    body = _build_match_report_body(result, user_club_id)

    return InboxMessage(
        date=match_date,
        subject=headline,
        body=body,
        category="media",
    )


def generate_random_event(club_name: str, player_name: str,
                           current_date: date) -> InboxMessage | None:
    """
    Maybe generate a random mid-season event (~5% daily chance).
    Returns an InboxMessage or None.
    """
    if not rng.chance(0.05):
        return None

    template = rng.choice(RANDOM_EVENTS)
    return InboxMessage(
        date=current_date,
        subject=template["subject"],
        body=template["body"].format(club=club_name, player=player_name),
        category=template["category"],
    )
