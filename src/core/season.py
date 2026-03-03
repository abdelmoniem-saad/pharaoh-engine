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
from src.utils.config import derive_season_expectation, expectation_display


def get_season_awards(conn: sqlite3.Connection,
                       game_state: GameState) -> dict:
    """Compute end-of-season awards."""
    standings = get_current_standings(conn)
    champion = standings[0] if standings else None
    top_scorers = queries.get_top_scorers(conn, limit=10)

    # Find user position
    user_pos = 0
    user_standing = None
    for i, s in enumerate(standings, 1):
        if s.club_id == game_state.user_club_id:
            user_pos = i
            user_standing = s
            break

    # Golden Boot — top scorer
    golden_boot = top_scorers[0] if top_scorers else None

    # Golden Glove — most clean sheets
    all_clubs = queries.get_all_clubs(conn)
    golden_glove = None
    best_cs = 0
    for club in all_clubs:
        squad = queries.get_players_by_club(conn, club.id)
        for p in squad:
            if p.position.value == "GK" and p.season_stats.clean_sheets > best_cs:
                best_cs = p.season_stats.clean_sheets
                golden_glove = {
                    "name": p.name, "clean_sheets": p.season_stats.clean_sheets,
                    "club_name": club.short_name,
                }

    # Young Player of the Season — best average rating for U21
    young_player = None
    best_young_rating = 0.0
    for club in all_clubs:
        squad = queries.get_players_by_club(conn, club.id)
        for p in squad:
            if p.age <= 21 and p.season_stats.appearances >= 10:
                if p.season_stats.average_rating > best_young_rating:
                    best_young_rating = p.season_stats.average_rating
                    young_player = {
                        "name": p.name, "age": p.age,
                        "rating": p.season_stats.average_rating,
                        "club_name": club.short_name,
                    }

    # Most assists
    most_assists = None
    best_assists = 0
    for club in all_clubs:
        squad = queries.get_players_by_club(conn, club.id)
        for p in squad:
            if p.season_stats.assists > best_assists:
                best_assists = p.season_stats.assists
                most_assists = {
                    "name": p.name, "assists": p.season_stats.assists,
                    "club_name": club.short_name,
                }

    return {
        "champion": champion,
        "standings": standings,
        "top_scorers": top_scorers,
        "user_position": user_pos,
        "user_standing": user_standing,
        "is_user_champion": champion and champion.club_id == game_state.user_club_id,
        "board_evaluation": [],
        "golden_boot": golden_boot,
        "golden_glove": golden_glove,
        "young_player": young_player,
        "most_assists": most_assists,
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

    # ── Archive historical stats BEFORE anything gets reset ──────────────────
    # This preserves the completed season's data for the history screen.
    try:
        awards = get_season_awards(conn, game_state)
        queries.archive_season_history(conn, game_state.season_year,
                                        awards, game_state.user_club_id)
        queries.archive_all_player_stats(conn, game_state.season_year)
        queries.archive_all_club_standings(conn, game_state.season_year)
        messages.append(f"Season {game_state.season_year}/{game_state.season_year + 1} archived to history.")
    except Exception as e:
        messages.append(f"Warning: Could not archive season history ({e}).")

    # Evaluate board objectives before reset
    user_club = queries.get_club(conn, game_state.user_club_id)
    if user_club:
        standings = get_current_standings(conn)
        user_pos = 0
        user_gf = 0
        user_gd = 0
        for i, s in enumerate(standings, 1):
            if s.club_id == game_state.user_club_id:
                user_pos = i
                user_gf = s.goals_for
                user_gd = s.goal_difference
                break
        # Generate objectives so we can evaluate them
        objectives = generate_season_objectives(user_club)
        user_club.board_objectives = objectives
        eval_msgs = evaluate_objectives(user_club, user_pos,
                                         goals_for=user_gf,
                                         goal_difference=user_gd)
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

    # Handle expired contracts — ALL clubs, not just user's
    from datetime import timedelta
    all_clubs = queries.get_all_clubs(conn)
    user_released = []
    for club in all_clubs:
        club_players = queries.get_players_by_club(conn, club.id)
        for p in club_players:
            if p.contract.contract_expiry and p.contract.contract_expiry <= game_state.current_date:
                # Actually renew the contract (1 year extension, same wage)
                new_expiry = game_state.current_date + timedelta(days=365)
                conn.execute("""
                    UPDATE players SET contract_expiry = ? WHERE id = ?
                """, (new_expiry.isoformat(), p.id))
                if club.id == game_state.user_club_id:
                    user_released.append(p.name)
    conn.commit()

    if user_released:
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject=f"📋 {len(user_released)} Contract(s) Auto-Renewed",
            body="The following players had expiring contracts and were auto-renewed for 1 year:\n\n" +
                 "\n".join(f"• {name}" for name in user_released),
            category="board",
        ))
        messages.append(f"{len(user_released)} contracts auto-renewed.")

    # Age players
    queries.age_all_players(conn)
    messages.append("All players aged by 1 year.")

    # Retire old players (age 38+)
    retired_msgs = _retire_old_players(conn, game_state)
    messages.extend(retired_msgs)

    # AI inter-club transfers (simulate offseason activity)
    ai_msgs = _simulate_ai_transfers(conn, game_state)
    messages.extend(ai_msgs)

    # Youth academy intake — generate a youth player for each club
    youth_msgs = _annual_youth_intake(conn, game_state)
    messages.extend(youth_msgs)

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

    # Re-derive season expectations for ALL clubs based on current reputation
    for c in clubs:
        c.season_expectation = derive_season_expectation(c.reputation)
        queries.update_club(conn, c)

    # Generate board objectives for user
    user_club = queries.get_club(conn, game_state.user_club_id)
    if user_club:
        objectives = generate_season_objectives(user_club)
        exp_name = expectation_display(user_club.season_expectation)
        obj_text = "\n".join(f"• {o.description} ({o.priority})" for o in objectives)
        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject="📋 Board Objectives",
            body=(
                f"The board has set the following objectives for the new season:\n\n"
                f"🎯 Season Target: {exp_name}\n\n{obj_text}"
            ),
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


def _retire_old_players(conn: sqlite3.Connection, game_state: GameState) -> list[str]:
    """Retire players aged 38+ (release from clubs)."""
    from src.utils import rng

    messages = []
    all_clubs = queries.get_all_clubs(conn)
    for club in all_clubs:
        squad = queries.get_players_by_club(conn, club.id)
        for p in squad:
            if p.age >= 38:
                # Higher chance of retirement the older they are
                retire_chance = 0.5 + (p.age - 38) * 0.15
                if rng.chance(retire_chance):
                    conn.execute("UPDATE players SET club_id = NULL WHERE id = ?", (p.id,))
                    if club.id == game_state.user_club_id:
                        queries.insert_message(conn, InboxMessage(
                            date=game_state.current_date,
                            subject=f"👋 {p.name} Retires",
                            body=f"{p.name} has announced their retirement from professional football at age {p.age}. "
                                 f"We thank them for their service.",
                            category="general",
                        ))
                    messages.append(f"{p.name} retired from {club.short_name}")
    conn.commit()
    return messages


def _simulate_ai_transfers(conn: sqlite3.Connection, game_state: GameState) -> list[str]:
    """Simulate AI inter-club transfers during the offseason."""
    from src.core.transfers import estimate_player_value
    from src.utils import rng

    messages = []
    all_clubs = queries.get_all_clubs(conn)
    ai_clubs = [c for c in all_clubs if c.id != game_state.user_club_id]

    # Each AI club may make 0-3 transfers
    transfers_made = []
    for club in ai_clubs:
        n_transfers = rng.randint(0, 3)
        if n_transfers == 0:
            continue

        squad = queries.get_players_by_club(conn, club.id)
        squad_size = len(squad)

        for _ in range(n_transfers):
            # Decide buy or sell
            if squad_size > 28 and rng.chance(0.7):
                # Too many players — sell a lower ability one
                sellable = [p for p in squad if p.current_ability < club.reputation * 0.7]
                if not sellable:
                    continue
                sell_player = rng.choice(sellable)
                buyer_clubs = [c for c in ai_clubs if c.id != club.id and c.id != game_state.user_club_id]
                if not buyer_clubs:
                    continue
                buyer = rng.choice(buyer_clubs)
                fee = estimate_player_value(sell_player, current_date=game_state.current_date)
                if buyer.finances.transfer_budget >= fee:
                    queries.transfer_player(
                        conn, sell_player.id, club.id, buyer.id,
                        fee=fee, wage=sell_player.contract.wage_weekly,
                        current_date=game_state.current_date,
                    )
                else:
                    # Buyer can't afford full fee — discount transfer
                    discounted = int(fee * 0.5)
                    queries.transfer_player(
                        conn, sell_player.id, club.id, buyer.id,
                        fee=discounted, wage=sell_player.contract.wage_weekly,
                        current_date=game_state.current_date,
                    )
                transfers_made.append(f"{sell_player.name}: {club.short_name} → {buyer.short_name} ({fee:,} EGP)")
                squad = [p for p in squad if p.id != sell_player.id]
                squad_size -= 1
            elif squad_size < 22 and rng.chance(0.6):
                # Need more players — buy from another club
                seller_clubs = [c for c in ai_clubs if c.id != club.id]
                if not seller_clubs:
                    continue
                seller = rng.choice(seller_clubs)
                seller_squad = queries.get_players_by_club(conn, seller.id)
                if len(seller_squad) <= 18:
                    continue
                buyable = [p for p in seller_squad if not p.is_captain]
                if not buyable:
                    continue
                buy_player = rng.choice(buyable)
                fee = estimate_player_value(buy_player, current_date=game_state.current_date)
                if club.finances.transfer_budget >= fee:
                    queries.transfer_player(
                        conn, buy_player.id, seller.id, club.id,
                        fee=fee, wage=buy_player.contract.wage_weekly,
                        current_date=game_state.current_date,
                    )
                    transfers_made.append(f"{buy_player.name}: {seller.short_name} → {club.short_name} ({fee:,} EGP)")
                    squad_size += 1

    conn.commit()

    if transfers_made:
        # Send a summary inbox message
        body = "Off-season transfer activity around the league:\n\n"
        body += "\n".join(f"• {t}" for t in transfers_made[:15])
        if len(transfers_made) > 15:
            body += f"\n\n...and {len(transfers_made) - 15} more transfers."

        queries.insert_message(conn, InboxMessage(
            date=game_state.current_date,
            subject=f"📰 {len(transfers_made)} Off-Season Transfers",
            body=body,
            category="transfer",
        ))
        messages.append(f"{len(transfers_made)} AI transfers completed.")

    return messages


def _annual_youth_intake(conn: sqlite3.Connection, game_state: GameState) -> list[str]:
    """Generate youth academy players for each club at the start of a new season."""
    from src.core.youth import generate_youth_player
    from src.utils import rng

    messages = []
    all_clubs = queries.get_all_clubs(conn)

    for club in all_clubs:
        # Number of youth players depends on youth_rating (1-10)
        num_youth = max(1, club.youth_rating // 3)  # 1-3 youths per club
        generated = []

        for _ in range(num_youth):
            youth = generate_youth_player(club)
            player_id = queries.insert_player(conn, youth)
            youth.id = player_id
            conn.execute("UPDATE players SET club_id = ? WHERE id = ?", (club.id, player_id))
            generated.append(youth)

        if club.id == game_state.user_club_id and generated:
            names = "\n".join(f"• {y.name} ({y.position.value}, Age {y.age}, PA: {y.potential_ability})"
                              for y in generated)
            queries.insert_message(conn, InboxMessage(
                date=game_state.current_date,
                subject=f"🌟 Youth Academy: {len(generated)} New Prospects!",
                body=f"The youth academy has produced {len(generated)} new players:\n\n{names}\n\n"
                     f"They have been added to your squad. Consider assigning training focuses.",
                category="general",
            ))
            messages.append(f"{len(generated)} youth players promoted to first team.")

    conn.commit()
    return messages
