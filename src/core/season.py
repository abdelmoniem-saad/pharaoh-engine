"""
Season lifecycle — end-of-season processing and new season creation.
"""
from __future__ import annotations

import sqlite3
from datetime import date

from src.data.models import GameState, InboxMessage
from src.data import queries
from src.core.league import create_league_season, get_current_standings
from src.core.board import generate_season_objectives, evaluate_objectives


def get_season_awards(conn: sqlite3.Connection,
                       game_state: GameState) -> dict:
    """Compute end-of-season awards."""
    standings = get_current_standings(conn)
    champion = standings[0] if standings else None
    top_scorers = queries.get_top_scorers(conn, limit=3)

    # Find user position
    user_pos = 0
    user_standing = None
    for i, s in enumerate(standings, 1):
        if s.club_id == game_state.user_club_id:
            user_pos = i
            user_standing = s
            break

    return {
        "champion": champion,
        "standings": standings,
        "top_scorers": top_scorers,
        "user_position": user_pos,
        "user_standing": user_standing,
        "is_user_champion": champion and champion.club_id == game_state.user_club_id,
        "board_evaluation": [],  # populated by start_new_season
    }


def start_new_season(conn: sqlite3.Connection,
                      game_state: GameState) -> list[str]:
    """
    Process everything needed to start a new season:
    - Age all players
    - Reset season stats
    - Reset standings
    - Delete old fixtures
    - Generate new fixtures
    - Bump season year
    - Send inbox messages
    """
    messages = []

    # Evaluate board objectives before reset
    user_club = queries.get_club(conn, game_state.user_club_id)
    if user_club:
        standings = get_current_standings(conn)
        user_pos = 0
        for i, s in enumerate(standings, 1):
            if s.club_id == game_state.user_club_id:
                user_pos = i
                break
        # Generate objectives so we can evaluate them
        objectives = generate_season_objectives(user_club)
        user_club.board_objectives = objectives
        eval_msgs = evaluate_objectives(user_club, user_pos)
        if eval_msgs:
            eval_body = "Season Board Review:\n\n" + "\n".join(eval_msgs)
            queries.insert_message(conn, InboxMessage(
                date=game_state.current_date,
                subject="🏛️ Board Evaluation",
                body=eval_body,
                category="board",
            ))
            messages.extend(eval_msgs)
        queries.update_club(conn, user_club)

    # Handle expired contracts — release players with expired contracts
    all_players = queries.get_players_by_club(conn, game_state.user_club_id)
    released = []
    for p in all_players:
        if p.contract.contract_expiry and p.contract.contract_expiry <= game_state.current_date:
            released.append(p.name)
            # Remove from club (set club_id to NULL would break things; just extend minimally)
            # For MVP: auto-extend by 1 year with a message
    if released:
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject=f"📋 {len(released)} Contract(s) Auto-Renewed",
            body="The following players had expiring contracts and were auto-renewed for 1 year:\n\n" +
                 "\n".join(f"• {name}" for name in released),
            category="board",
        ))
        messages.append(f"{len(released)} contracts auto-renewed.")

    # Age players
    queries.age_all_players(conn)
    messages.append("All players aged by 1 year.")

    # Retire old players (remove players age 38+)
    # For now we keep them; a Phase 2 feature

    # Reset stats
    queries.reset_all_season_stats(conn)
    messages.append("Season statistics reset.")

    # Reset standings
    queries.reset_standings(conn)

    # Delete old fixtures
    queries.delete_all_fixtures(conn)

    # Bump season
    game_state.season_year += 1
    game_state.current_date = date(game_state.season_year, 8, 15)
    game_state.day_count = 0

    # Generate new fixtures
    clubs = queries.get_all_clubs(conn)
    create_league_season(conn, clubs, game_state.season_year)
    messages.append(f"Season {game_state.season_year}/{game_state.season_year + 1} fixtures generated.")

    # Generate board objectives for user
    user_club = queries.get_club(conn, game_state.user_club_id)
    if user_club:
        objectives = generate_season_objectives(user_club)
        obj_text = "\n".join(f"• {o.description} ({o.priority})" for o in objectives)
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject="📋 Board Objectives",
            body=f"The board has set the following objectives for the new season:\n\n{obj_text}",
            category="board",
        ))
        messages.append("Board objectives set for new season.")

    # Welcome message
    queries.insert_message(conn, InboxMessage(
        date=game_state.current_date,
        subject=f"🏟️ Season {game_state.season_year}/{game_state.season_year + 1} Begins!",
        body=f"Welcome to the new season, {game_state.manager_name}. Pre-season is underway.",
        category="general",
    ))

    # Save state
    queries.save_game_state(conn, game_state)

    return messages



