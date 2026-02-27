"""
Match simulation engine.

Simulates a football match minute-by-minute, producing goals, cards,
and key events based on team strengths, tactics, and individual attributes.
"""
from __future__ import annotations

from src.data.models import (
    Player, Club, MatchResult, MatchEvent, MatchStats, TeamTactics,
)
from src.utils.config import (
    Position, MatchEventType, Mentality,
    HOME_ADVANTAGE_BONUS, MATCH_DURATION_MINUTES,
)
from src.utils import rng
from src.core.tactics import calculate_team_strength, get_formation_positions
from src.core.player import get_match_readiness


def simulate_match(
    home_club: Club,
    away_club: Club,
    home_squad: list[Player],
    away_squad: list[Player],
    home_tactics: TeamTactics,
    away_tactics: TeamTactics,
) -> MatchResult:
    """
    Simulate a full match between two teams.

    Returns a MatchResult with score, events, and statistics.
    """
    # Build player lookup maps
    home_players = {p.id: p for p in home_squad}
    away_players = {p.id: p for p in away_squad}

    # Calculate team strengths
    home_strength = calculate_team_strength(home_squad, home_tactics)
    away_strength = calculate_team_strength(away_squad, away_tactics)

    # Apply home advantage
    home_attack = home_strength["attack"] * HOME_ADVANTAGE_BONUS
    home_midfield = home_strength["midfield"] * HOME_ADVANTAGE_BONUS
    home_defense = home_strength["defense"] * HOME_ADVANTAGE_BONUS
    home_gk = home_strength["goalkeeper"] * HOME_ADVANTAGE_BONUS

    away_attack = away_strength["attack"]
    away_midfield = away_strength["midfield"]
    away_defense = away_strength["defense"]
    away_gk = away_strength["goalkeeper"]

    # Initialize
    home_goals = 0
    away_goals = 0
    events: list[MatchEvent] = []
    home_shots = 0
    away_shots = 0
    home_shots_on_target = 0
    away_shots_on_target = 0
    home_corners = 0
    away_corners = 0
    home_fouls = 0
    away_fouls = 0
    home_yellows = 0
    away_yellows = 0
    home_reds = 0
    away_reds = 0
    home_saves = 0
    away_saves = 0

    events.append(MatchEvent(
        minute=0, event_type=MatchEventType.KICKOFF,
        description="The match kicks off!"
    ))

    # Possession calculation (midfield battle)
    total_mid = home_midfield + away_midfield
    if total_mid > 0:
        home_possession = (home_midfield / total_mid) * 100
    else:
        home_possession = 50.0
    home_possession = rng.gaussian_clamped(home_possession, 5.0, 25.0, 75.0)

    # Determine injury time
    first_half_added = rng.randint(1, 4)
    second_half_added = rng.randint(1, 7)

    # Simulate minute by minute
    for minute in range(1, MATCH_DURATION_MINUTES + second_half_added + 1):
        if minute == 46:
            events.append(MatchEvent(
                minute=45, event_type=MatchEventType.HALF_TIME,
                description="Half time."
            ))

        # Skip added first-half time visualization (events still happen)
        is_first_half = minute <= 45 + first_half_added
        is_second_half = minute > 45 + first_half_added

        # ── Chance creation ──────────────────────────────────────────
        # Base chance of something happening each minute
        action_chance = 0.12  # ~11 total chances per match per team

        # Home attack
        if rng.chance(action_chance * (home_possession / 50.0)):
            event = _simulate_attack(
                minute=min(minute, 90 + second_half_added),
                attacking_strength=home_attack,
                defending_strength=away_defense,
                gk_strength=away_gk,
                attacking_club=home_club,
                attacking_players=home_players,
                attacking_xi=home_tactics.starting_xi,
                attacking_formation=home_tactics.formation,
                is_home=True,
            )
            if event:
                events.append(event)
                if event.event_type == MatchEventType.GOAL:
                    home_goals += 1
                    home_shots += 1
                    home_shots_on_target += 1
                elif event.event_type == MatchEventType.SHOT_ON_TARGET:
                    home_shots += 1
                    home_shots_on_target += 1
                    away_saves += 1
                elif event.event_type == MatchEventType.SHOT_OFF_TARGET:
                    home_shots += 1
                elif event.event_type == MatchEventType.CORNER:
                    home_corners += 1

        # Away attack
        if rng.chance(action_chance * ((100 - home_possession) / 50.0)):
            event = _simulate_attack(
                minute=min(minute, 90 + second_half_added),
                attacking_strength=away_attack,
                defending_strength=home_defense,
                gk_strength=home_gk,
                attacking_club=away_club,
                attacking_players=away_players,
                attacking_xi=away_tactics.starting_xi,
                attacking_formation=away_tactics.formation,
                is_home=False,
            )
            if event:
                events.append(event)
                if event.event_type == MatchEventType.GOAL:
                    away_goals += 1
                    away_shots += 1
                    away_shots_on_target += 1
                elif event.event_type == MatchEventType.SHOT_ON_TARGET:
                    away_shots += 1
                    away_shots_on_target += 1
                    home_saves += 1
                elif event.event_type == MatchEventType.SHOT_OFF_TARGET:
                    away_shots += 1
                elif event.event_type == MatchEventType.CORNER:
                    away_corners += 1

        # ── Fouls & Cards ────────────────────────────────────────────
        if rng.chance(0.04):  # ~3-4 fouls per team per match
            is_home_foul = rng.chance(0.5)
            if is_home_foul:
                home_fouls += 1
                foul_player = _pick_random_player(home_players, home_tactics.starting_xi)
            else:
                away_fouls += 1
                foul_player = _pick_random_player(away_players, away_tactics.starting_xi)

            # Card probability
            if rng.chance(0.15):  # ~15% of fouls get a yellow
                card_type = MatchEventType.YELLOW_CARD
                if is_home_foul:
                    home_yellows += 1
                else:
                    away_yellows += 1

                if foul_player:
                    events.append(MatchEvent(
                        minute=min(minute, 90 + second_half_added),
                        event_type=card_type,
                        player_id=foul_player.id,
                        player_name=foul_player.name,
                        club_id=home_club.id if is_home_foul else away_club.id,
                        description=f"Yellow card for {foul_player.name}",
                    ))

    # Full time
    events.append(MatchEvent(
        minute=90, event_type=MatchEventType.FULL_TIME,
        description=f"Full time! {home_club.name} {home_goals} - {away_goals} {away_club.name}"
    ))

    # Build result
    return MatchResult(
        home_club_id=home_club.id,
        away_club_id=away_club.id,
        home_club_name=home_club.name,
        away_club_name=away_club.name,
        home_goals=home_goals,
        away_goals=away_goals,
        events=events,
        home_stats=MatchStats(
            possession=round(home_possession, 1),
            shots=home_shots,
            shots_on_target=home_shots_on_target,
            corners=home_corners,
            fouls=home_fouls,
            yellow_cards=home_yellows,
            red_cards=home_reds,
            saves=home_saves,
        ),
        away_stats=MatchStats(
            possession=round(100 - home_possession, 1),
            shots=away_shots,
            shots_on_target=away_shots_on_target,
            corners=away_corners,
            fouls=away_fouls,
            yellow_cards=away_yellows,
            red_cards=away_reds,
            saves=away_saves,
        ),
    )


def _simulate_attack(
    minute: int,
    attacking_strength: float,
    defending_strength: float,
    gk_strength: float,
    attacking_club: Club,
    attacking_players: dict[int, Player],
    attacking_xi: list[int],
    attacking_formation: str,
    is_home: bool,
) -> MatchEvent | None:
    """
    Simulate a single attacking action. Returns a MatchEvent or None.
    """
    if not attacking_xi:
        return None

    # Attack vs Defense ratio determines shot chance
    if defending_strength > 0:
        attack_ratio = attacking_strength / defending_strength
    else:
        attack_ratio = 2.0

    # Chance of getting a shot off (higher attack ratio = more shots)
    shot_chance = rng.clamp(0.25 + (attack_ratio - 1.0) * 0.2, 0.1, 0.7)

    if not rng.chance(shot_chance):
        # Attack broken down, maybe a corner
        if rng.chance(0.3):
            return MatchEvent(
                minute=minute, event_type=MatchEventType.CORNER,
                club_id=attacking_club.id,
                description=f"Corner for {attacking_club.name}",
            )
        return None

    # Shot taken — pick the shooter (weighted toward attackers)
    shooter = _pick_scorer(attacking_players, attacking_xi, attacking_formation)
    if not shooter:
        return None

    # Shot quality based on shooter's finishing + composure
    shot_quality = (shooter.attributes.finishing * 0.6 +
                    shooter.attributes.composure * 0.3 +
                    shooter.attributes.positioning * 0.1)

    # On target?
    on_target_chance = rng.clamp(shot_quality / 25.0, 0.2, 0.8)

    if not rng.chance(on_target_chance):
        return MatchEvent(
            minute=minute, event_type=MatchEventType.SHOT_OFF_TARGET,
            player_id=shooter.id, player_name=shooter.name,
            club_id=attacking_club.id,
            description=f"{shooter.name} shoots wide!",
        )

    # On target — GK save?
    save_chance = rng.clamp(gk_strength / 20.0, 0.1, 0.75)

    # Reduce save chance based on shot quality
    adjusted_save = save_chance * (1.0 - (shot_quality / 40.0))
    adjusted_save = rng.clamp(adjusted_save, 0.05, 0.7)

    if rng.chance(adjusted_save):
        return MatchEvent(
            minute=minute, event_type=MatchEventType.SHOT_ON_TARGET,
            player_id=shooter.id, player_name=shooter.name,
            club_id=attacking_club.id,
            description=f"{shooter.name} forces a save!",
        )

    # GOAL!
    # Try to find an assist provider
    assister = _pick_assister(attacking_players, attacking_xi, shooter.id)

    event = MatchEvent(
        minute=minute, event_type=MatchEventType.GOAL,
        player_id=shooter.id, player_name=shooter.name,
        club_id=attacking_club.id,
        description=f"GOAL! {shooter.name} scores for {attacking_club.name}!",
    )
    if assister:
        event.second_player_id = assister.id
        event.second_player_name = assister.name
        event.description += f" (Assisted by {assister.name})"

    return event


def _pick_scorer(players: dict[int, Player], xi: list[int],
                  formation: str) -> Player | None:
    """Pick a goalscorer from the starting XI, weighted by position and finishing."""
    if not xi:
        return None

    positions = get_formation_positions(formation)
    candidates = []
    weights = []

    for i, pid in enumerate(xi):
        player = players.get(pid)
        if not player:
            continue

        pos = positions[i] if i < len(positions) else Position.CM

        # Weight by position (attackers score more)
        pos_weight = {
            Position.ST: 5.0, Position.CAM: 2.5,
            Position.LW: 2.0, Position.RW: 2.0,
            Position.CM: 1.0, Position.LM: 1.5, Position.RM: 1.5,
            Position.CDM: 0.5, Position.CB: 0.3,
            Position.LB: 0.2, Position.RB: 0.2, Position.GK: 0.01,
        }.get(pos, 0.5)

        # Also weight by finishing attribute
        attr_weight = player.attributes.finishing / 10.0
        total_weight = pos_weight * attr_weight

        candidates.append(player)
        weights.append(total_weight)

    if not candidates:
        return None

    return rng.choices(candidates, k=1, weights=weights)[0]


def _pick_assister(players: dict[int, Player], xi: list[int],
                    scorer_id: int) -> Player | None:
    """Pick an assist provider (60% chance of having an assist)."""
    if not rng.chance(0.6):
        return None

    candidates = []
    weights = []

    for pid in xi:
        if pid == scorer_id:
            continue
        player = players.get(pid)
        if not player:
            continue

        # Weight by vision, passing, crossing
        weight = (player.attributes.vision + player.attributes.passing +
                  player.attributes.crossing) / 30.0
        candidates.append(player)
        weights.append(weight)

    if not candidates:
        return None

    return rng.choices(candidates, k=1, weights=weights)[0]


def _pick_random_player(players: dict[int, Player],
                         xi: list[int]) -> Player | None:
    """Pick a random player from the starting XI."""
    valid = [players[pid] for pid in xi if pid in players]
    if not valid:
        return None
    return rng.choice(valid)

