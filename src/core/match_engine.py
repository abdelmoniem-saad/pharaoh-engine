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
from src.core import commentary


def _per_minute_drain(p: Player) -> float:
    """
    Condition points lost per minute by *p*.

    Low stamina tires far faster; goalkeepers track at half rate.
    Outfield reference (before tempo/pressing/Ramadan multipliers):
    stamina 18 → ~0.148/min (~13 pts over a match), stamina 13 →
    ~0.208/min (~19 pts), stamina 8 → ~0.268/min (~24 pts).
    """
    base = 0.10 + max(0.0, (22 - p.attributes.stamina) * 0.012)
    if p.position == Position.GK:
        base *= 0.5
    return base


def simulate_match(
    home_club: Club,
    away_club: Club,
    home_squad: list[Player],
    away_squad: list[Player],
    home_tactics: TeamTactics,
    away_tactics: TeamTactics,
    match_date=None,
    is_derby: bool = False,
    minutes_played_offset: dict[int, int] | None = None,
) -> MatchResult:
    """
    Simulate a full match between two teams.

    Every tactical decision matters:
    - Formation & position suitability drive team strength
    - Mentality shifts attack/defense balance
    - Pressing increases fouls but boosts midfield
    - High tempo = more chances but more turnovers
    - Fan happiness scales home advantage
    - Per-player stamina: each player's condition drains minute by minute
      (stamina attribute, fitness, tempo, pressing, Ramadan) and feeds back
      into effective team strength — subs bring genuinely fresh legs
    - Red cards remove players from the XI
    - Training focus gives small match bonuses
    - Derby → amplified morale effects

    ``minutes_played_offset`` optionally maps player_id → minutes already on
    the pitch (used by the live-match re-simulation after a substitution, so
    the rest of the match starts from the real fatigue state while the new
    arrival begins fresh).
    """
    # Build player lookup maps
    home_players = {p.id: p for p in home_squad}
    away_players = {p.id: p for p in away_squad}

    # Mutable XIs (red cards will remove players)
    home_active_xi = list(home_tactics.starting_xi)
    away_active_xi = list(away_tactics.starting_xi)

    # Calculate team strengths
    home_strength = calculate_team_strength(home_squad, home_tactics)
    away_strength = calculate_team_strength(away_squad, away_tactics)

    # ── Home advantage scales with fan happiness ─────────────────────
    # Base HOME_ADVANTAGE_BONUS is ~1.05; fan happiness adds up to +0.05 more
    fan_bonus = 1.0
    if home_club.fan_happiness >= 70:
        fan_bonus = HOME_ADVANTAGE_BONUS + 0.03      # electric crowd
    elif home_club.fan_happiness >= 40:
        fan_bonus = HOME_ADVANTAGE_BONUS              # normal
    elif home_club.fan_happiness >= 20:
        fan_bonus = HOME_ADVANTAGE_BONUS - 0.02       # unhappy crowd
    else:
        fan_bonus = 1.0                               # furious fans = no home advantage

    home_attack = home_strength["attack"] * fan_bonus
    home_midfield = home_strength["midfield"] * fan_bonus
    home_defense = home_strength["defense"] * fan_bonus
    home_gk = home_strength["goalkeeper"] * fan_bonus

    away_attack = away_strength["attack"]
    away_midfield = away_strength["midfield"]
    away_defense = away_strength["defense"]
    away_gk = away_strength["goalkeeper"]

    # ── Training focus micro-bonuses ──────────────────────────────────
    # Players with a training focus get a small bump in the relevant area
    _training_bonus_attack = 0.0
    _training_bonus_defense = 0.0
    for pid in home_tactics.starting_xi:
        p = home_players.get(pid)
        if p and p.training_focus:
            if p.training_focus in ("Shooting", "Playmaking"):
                _training_bonus_attack += 0.15
            elif p.training_focus in ("Defending",):
                _training_bonus_defense += 0.15
    home_attack += _training_bonus_attack
    home_defense += _training_bonus_defense

    # Away team training bonuses (mirror of home)
    _away_training_attack = 0.0
    _away_training_defense = 0.0
    for pid in away_tactics.starting_xi:
        p = away_players.get(pid)
        if p and p.training_focus:
            if p.training_focus in ("Shooting", "Playmaking"):
                _away_training_attack += 0.15
            elif p.training_focus in ("Defending",):
                _away_training_defense += 0.15
    away_attack += _away_training_attack
    away_defense += _away_training_defense

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

    # ── Per-player live condition model ────────────────────────────────
    # Every player starts at his real fitness and drains each minute based
    # on his own stamina, his team's tempo & pressing, and Ramadan fasting.
    # Team effectiveness follows the average condition of whoever is on the
    # pitch right now — which is exactly why substitutions matter.
    def _tempo_press_factor(tactics) -> float:
        tempo = getattr(tactics, "tempo", 5)
        press = getattr(tactics, "pressing_intensity", 5)
        return (0.90 + tempo * 0.02) * (0.95 + press * 0.01)

    ramadan_drain_mult = 1.0
    if match_date:
        from src.utils.config import is_ramadan as _is_ramadan
        if _is_ramadan(match_date):
            ramadan_drain_mult = 1.10  # fasting players tire ~10% faster

    offsets = minutes_played_offset or {}
    condition: dict[int, float] = {}
    cond_factor: dict[int, float] = {}
    for _pmap, _xi, _f in (
        (home_players, home_tactics.starting_xi, _tempo_press_factor(home_tactics)),
        (away_players, away_tactics.starting_xi, _tempo_press_factor(away_tactics)),
    ):
        for _pid in _xi:
            _p = _pmap.get(_pid)
            if not _p:
                continue
            _pre = offsets.get(_pid, 0)
            _cond = float(getattr(_p, "fitness", 85) or 85)
            _cond -= _pre * _per_minute_drain(_p) * _f * ramadan_drain_mult
            condition[_pid] = max(20.0, min(100.0, _cond))
            cond_factor[_pid] = _f

    # Simulate minute by minute
    for minute in range(1, MATCH_DURATION_MINUTES + second_half_added + 1):
        if minute == 46:
            events.append(MatchEvent(
                minute=45, event_type=MatchEventType.HALF_TIME,
                description="Half time."
            ))

        is_second_half = minute > 45

        # ── Fatigue: drain every player, then read team condition ─────
        for pid in condition:
            p = home_players.get(pid) or away_players.get(pid)
            if not p:
                continue
            condition[pid] = max(
                20.0,
                condition[pid] - _per_minute_drain(p) * cond_factor[pid] * ramadan_drain_mult,
            )

        def _team_condition_pct(player_map, xi) -> float:
            vals = [condition[pid] for pid in xi if pid in condition]
            if not vals:
                return 100.0
            return sum(vals) / len(vals)

        # Effectiveness from team condition: linear, clamped.
        # Condition 100 → ×1.00, 87 (typical fresh side) → ×0.98, 50 → ×0.74.
        # A substitute arriving at full condition lifts the average at once.
        fatigue_mult_home = max(0.70, min(1.03, 0.74 + 0.26 * (_team_condition_pct(home_players, home_active_xi) - 50.0) / 50.0))
        fatigue_mult_away = max(0.70, min(1.03, 0.74 + 0.26 * (_team_condition_pct(away_players, away_active_xi) - 50.0) / 50.0))

        # ── Red card penalty: fewer players = weaker ─────────────────
        home_manpower = len(home_active_xi) / 11.0  # 1.0 at full, 0.91 with 10 men
        away_manpower = len(away_active_xi) / 11.0

        eff_home_attack = home_attack * fatigue_mult_home * home_manpower
        eff_home_defense = home_defense * fatigue_mult_home * home_manpower
        eff_away_attack = away_attack * fatigue_mult_away * away_manpower
        eff_away_defense = away_defense * fatigue_mult_away * away_manpower
        eff_home_gk = home_gk * fatigue_mult_home
        eff_away_gk = away_gk * fatigue_mult_away

        # ── Chance creation ──────────────────────────────────────────
        home_tempo = getattr(home_tactics, "tempo", 5)
        away_tempo = getattr(away_tactics, "tempo", 5)
        avg_tempo = (home_tempo + away_tempo) / 2.0
        action_chance = 0.08 + avg_tempo * 0.008

        # Home attack
        if rng.chance(action_chance * (home_possession / 50.0)):
            event = _simulate_attack(
                minute=min(minute, 90 + second_half_added),
                attacking_strength=eff_home_attack,
                defending_strength=eff_away_defense,
                gk_strength=eff_away_gk,
                attacking_club=home_club,
                attacking_players=home_players,
                attacking_xi=home_active_xi,
                attacking_formation=home_tactics.formation,
                is_home=True,
                attacking_tactics=home_tactics,
                defending_tactics=away_tactics,
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
                attacking_strength=eff_away_attack,
                defending_strength=eff_home_defense,
                gk_strength=eff_home_gk,
                attacking_club=away_club,
                attacking_players=away_players,
                attacking_xi=away_active_xi,
                attacking_formation=away_tactics.formation,
                is_home=False,
                attacking_tactics=away_tactics,
                defending_tactics=home_tactics,
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
        # Who fouls more depends on their pressing intensity
        home_press = getattr(home_tactics, "pressing_intensity", 5)
        away_press = getattr(away_tactics, "pressing_intensity", 5)
        total_press = home_press + away_press
        foul_chance = 0.02 + (total_press / 2.0) * 0.004

        if rng.chance(foul_chance):
            # Higher pressing team fouls more often (not 50/50)
            home_foul_prob = home_press / max(total_press, 1)
            is_home_foul = rng.chance(home_foul_prob)

            if is_home_foul:
                home_fouls += 1
                foul_player = _pick_fouler(home_players, home_active_xi)
            else:
                away_fouls += 1
                foul_player = _pick_fouler(away_players, away_active_xi)

            # Penalty chance (~3% of fouls are in the box)
            if rng.chance(0.03):
                # Penalty!
                if is_home_foul:
                    pen_taker = _pick_scorer(away_players, away_active_xi, away_tactics.formation)
                    pen_club = away_club
                else:
                    pen_taker = _pick_scorer(home_players, home_active_xi, home_tactics.formation)
                    pen_club = home_club

                if pen_taker:
                    # Penalty conversion based on composure + finishing
                    pen_quality = (pen_taker.attributes.composure * 0.5 +
                                   pen_taker.attributes.finishing * 0.5)
                    if rng.chance(0.75 + pen_quality / 200.0):  # ~80-90% conversion
                        if pen_club.id == home_club.id:
                            home_goals += 1
                            home_shots += 1
                            home_shots_on_target += 1
                        else:
                            away_goals += 1
                            away_shots += 1
                            away_shots_on_target += 1
                        events.append(MatchEvent(
                            minute=min(minute, 90 + second_half_added),
                            event_type=MatchEventType.PENALTY,
                            player_id=pen_taker.id,
                            player_name=pen_taker.name,
                            player_name_ar=pen_taker.name_ar,
                            club_id=pen_club.id,
                            description=commentary.generate(MatchEventType.GOAL, lang="en",
                                                            player=pen_taker.name,
                                                            club=pen_club.name) + " (Penalty!)",
                            description_ar=commentary.generate(MatchEventType.GOAL, lang="ar",
                                                               player=pen_taker.name_ar,
                                                               club=pen_club.name_ar) + " (ضربة جزاء!)",
                        ))
                    else:
                        events.append(MatchEvent(
                            minute=min(minute, 90 + second_half_added),
                            event_type=MatchEventType.PENALTY_MISS,
                            player_id=pen_taker.id,
                            player_name=pen_taker.name,
                            player_name_ar=pen_taker.name_ar,
                            club_id=pen_club.id,
                            description=f"PENALTY MISSED! {pen_taker.name} fails from the spot!",
                            description_ar=f"ضربة جزاء ضائعة! {pen_taker.name_ar} يخفق في التسجيل من علامة الجزاء!",
                        ))
                        if pen_club.id == home_club.id:
                            home_shots += 1
                        else:
                            away_shots += 1
                continue  # Skip the regular card logic for penalty fouls

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
                        player_name_ar=foul_player.name_ar,
                        club_id=home_club.id if is_home_foul else away_club.id,
                        description=f"Yellow card for {foul_player.name}",
                        description_ar=f"بطاقة صفراء لـ {foul_player.name_ar}",
                    ))

            # Rare red card (~1% of fouls) — REMOVES PLAYER FROM MATCH
            elif rng.chance(0.01):
                if is_home_foul:
                    home_reds += 1
                else:
                    away_reds += 1
                if foul_player:
                    events.append(MatchEvent(
                        minute=min(minute, 90 + second_half_added),
                        event_type=MatchEventType.RED_CARD,
                        player_id=foul_player.id,
                        player_name=foul_player.name,
                        player_name_ar=foul_player.name_ar,
                        club_id=home_club.id if is_home_foul else away_club.id,
                        description=commentary.generate(MatchEventType.RED_CARD, lang="en",
                                                         player=foul_player.name,
                                                         club=(home_club.name if is_home_foul else away_club.name)),
                        description_ar=commentary.generate(MatchEventType.RED_CARD, lang="ar",
                                                            player=foul_player.name_ar,
                                                            club=(home_club.name_ar if is_home_foul else away_club.name_ar)),
                    ))
                    # Remove from active XI — team plays with fewer players
                    if is_home_foul and foul_player.id in home_active_xi:
                        home_active_xi.remove(foul_player.id)
                    elif not is_home_foul and foul_player.id in away_active_xi:
                        away_active_xi.remove(foul_player.id)

        # ── Injuries (~1.5% chance per team per match, so ~0.017% per minute) ──
        if rng.chance(0.0017):
            inj_home = rng.chance(0.5)
            if inj_home:
                inj_player = _pick_random_player(home_players, home_active_xi)
                inj_club = home_club
            else:
                inj_player = _pick_random_player(away_players, away_active_xi)
                inj_club = away_club
            if inj_player:
                from src.utils.config import INJURY_TYPES
                inj_type = rng.choice(INJURY_TYPES)
                events.append(MatchEvent(
                    minute=min(minute, 90 + second_half_added),
                    event_type=MatchEventType.INJURY,
                    player_id=inj_player.id,
                    player_name=inj_player.name,
                    player_name_ar=inj_player.name_ar,
                    club_id=inj_club.id,
                    description=commentary.generate(
                        MatchEventType.INJURY, lang="en",
                        player=inj_player.name,
                        club=inj_club.name,
                        detail=inj_type.lower(),
                    ),
                    description_ar=commentary.generate(
                        MatchEventType.INJURY, lang="ar",
                        player=inj_player.name_ar,
                        club=inj_club.name_ar,
                        detail=inj_type.lower(), # injury types are technical
                    ),
                ))

    # Full time
    events.append(MatchEvent(
        minute=90, event_type=MatchEventType.FULL_TIME,
        description=commentary.generate(
            MatchEventType.FULL_TIME, lang="en",
            home=home_club.name, away=away_club.name,
            home_goals=home_goals, away_goals=away_goals,
        ),
        description_ar=commentary.generate(
            MatchEventType.FULL_TIME, lang="ar",
            home=home_club.name_ar, away=away_club.name_ar,
            home_goals=home_goals, away_goals=away_goals,
        ),
    ))

    # ── Generate individual player ratings ──────────────────────────────
    player_ratings: dict[int, float] = {}
    _rate_players(player_ratings, home_tactics.starting_xi, home_players,
                  events, home_club.id, home_goals, away_goals,
                  is_home_team=True, formation=home_tactics.formation)
    _rate_players(player_ratings, away_tactics.starting_xi, away_players,
                  events, away_club.id, away_goals, home_goals,
                  is_home_team=False, formation=away_tactics.formation)

    # Build result
    return MatchResult(
        home_club_id=home_club.id,
        away_club_id=away_club.id,
        home_club_name=home_club.name,
        away_club_name=away_club.name,
        home_club_name_ar=home_club.name_ar,
        away_club_name_ar=away_club.name_ar,
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
        player_ratings=player_ratings,
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
    attacking_tactics: TeamTactics | None = None,
    defending_tactics: TeamTactics | None = None,
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

    # High defensive line = more vulnerable to counters (boosts attacker's ratio)
    if defending_tactics:
        def_line = getattr(defending_tactics, "defensive_line", 5)
        attack_ratio *= 0.95 + def_line * 0.01  # high line = slightly easier to beat

    # Chance of getting a shot off
    shot_chance = rng.clamp(0.25 + (attack_ratio - 1.0) * 0.2, 0.1, 0.7)

    if not rng.chance(shot_chance):
        # Attack broken down, maybe a corner
        if rng.chance(0.3):
            return MatchEvent(
                minute=minute, event_type=MatchEventType.CORNER,
                club_id=attacking_club.id,
                description=f"Corner for {attacking_club.name}",
                description_ar=f"ركنية لـ {attacking_club.name_ar}",
            )
        return None

    # Shot taken — pick the shooter (weighted toward attackers)
    shooter = _pick_scorer(attacking_players, attacking_xi, attacking_formation)
    if not shooter:
        return None

    # Determine shooter's position suitability for their formation slot
    from src.core.player import position_suitability
    _positions = get_formation_positions(attacking_formation)
    shooter_suit = 1.0
    for idx, pid in enumerate(attacking_xi):
        if pid == shooter.id and idx < len(_positions):
            shooter_suit = position_suitability(shooter, _positions[idx])
            break

    # Shot quality based on shooter's finishing + composure, penalized if out of position
    shot_quality = (shooter.attributes.finishing * 0.6 +
                    shooter.attributes.composure * 0.3 +
                    shooter.attributes.positioning * 0.1) * shooter_suit

    # On target?
    on_target_chance = rng.clamp(shot_quality / 25.0, 0.2, 0.8)

    if not rng.chance(on_target_chance):
        return MatchEvent(
            minute=minute, event_type=MatchEventType.SHOT_OFF_TARGET,
            player_id=shooter.id, player_name=shooter.name,
            player_name_ar=shooter.name_ar,
            club_id=attacking_club.id,
            description=f"{shooter.name} shoots wide!",
            description_ar=f"{shooter.name_ar} يسدد بعيداً!",
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
            player_name_ar=shooter.name_ar,
            club_id=attacking_club.id,
            description=f"{shooter.name} forces a save!",
            description_ar=f"{shooter.name_ar} يجبر الحارس على التصدي!",
        )

    # GOAL!
    # Try to find an assist provider
    assister = _pick_assister(attacking_players, attacking_xi, shooter.id, attacking_formation)

    event = MatchEvent(
        minute=minute, event_type=MatchEventType.GOAL,
        player_id=shooter.id, player_name=shooter.name,
        player_name_ar=shooter.name_ar,
        club_id=attacking_club.id,
        description=f"GOAL! {shooter.name} scores for {attacking_club.name}!",
        description_ar=f"جووووووول! {shooter.name_ar} يسجل لـ {attacking_club.name_ar}!",
    )
    if assister:
        event.second_player_id = assister.id
        event.second_player_name = assister.name
        event.second_player_name_ar = assister.name_ar
        event.description += f" (Assisted by {assister.name})"
        event.description_ar += f" (صناعة {assister.name_ar})"

    return event


def _pick_scorer(players: dict[int, Player], xi: list[int],
                  formation: str) -> Player | None:
    """Pick a goalscorer from the starting XI, weighted by position, finishing,
    and position suitability — a CB playing ST rarely scores."""
    if not xi:
        return None

    from src.core.player import position_suitability

    positions = get_formation_positions(formation)
    candidates = []
    weights = []

    for i, pid in enumerate(xi):
        player = players.get(pid)
        if not player:
            continue

        pos = positions[i] if i < len(positions) else Position.CM

        # Weight by formation slot (attackers score more)
        pos_weight = {
            Position.ST: 5.0, Position.CAM: 2.5,
            Position.LW: 2.0, Position.RW: 2.0,
            Position.CM: 1.0, Position.LM: 1.5, Position.RM: 1.5,
            Position.CDM: 0.5, Position.CB: 0.3,
            Position.LB: 0.2, Position.RB: 0.2, Position.GK: 0.01,
        }.get(pos, 0.5)

        # Also weight by finishing attribute
        attr_weight = player.attributes.finishing / 10.0

        # Position suitability: a CB in a ST slot has suit ~0.2, so their
        # effective finishing contribution drops massively
        suit = position_suitability(player, pos)

        total_weight = pos_weight * attr_weight * suit

        candidates.append(player)
        weights.append(max(total_weight, 0.01))  # ensure never zero

    if not candidates:
        return None

    return rng.choices(candidates, k=1, weights=weights)[0]


def _pick_assister(players: dict[int, Player], xi: list[int],
                    scorer_id: int, formation: str = "4-3-3") -> Player | None:
    """Pick an assist provider (60% chance of having an assist)."""
    if not rng.chance(0.6):
        return None

    from src.core.player import position_suitability
    positions = get_formation_positions(formation)

    candidates = []
    weights = []

    for i, pid in enumerate(xi):
        if pid == scorer_id:
            continue
        player = players.get(pid)
        if not player:
            continue

        # Position suitability multiplier
        pos = positions[i] if i < len(positions) else Position.CM
        suit = position_suitability(player, pos)

        # Weight by vision, passing, crossing — scaled by suitability
        weight = ((player.attributes.vision + player.attributes.passing +
                   player.attributes.crossing) / 30.0) * suit
        candidates.append(player)
        weights.append(max(weight, 0.01))

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


def _pick_fouler(players: dict[int, Player],
                  xi: list[int]) -> Player | None:
    """Pick a player who commits a foul — weighted by aggression (low composure,
    high work_rate, tackles a lot). Defenders and midfielders foul more."""
    candidates = []
    weights = []
    for pid in xi:
        p = players.get(pid)
        if not p:
            continue
        # Low composure + high work rate = more fouls
        aggression = (20 - p.attributes.composure) + p.attributes.work_rate + p.attributes.tackling
        # Defenders and DMs foul more
        pos_mult = {
            Position.GK: 0.1, Position.CB: 1.5, Position.LB: 1.3, Position.RB: 1.3,
            Position.CDM: 1.4, Position.CM: 1.0, Position.CAM: 0.7,
            Position.LM: 0.8, Position.RM: 0.8, Position.LW: 0.6, Position.RW: 0.6,
            Position.ST: 0.5,
        }.get(p.position, 1.0)
        candidates.append(p)
        weights.append(max(aggression * pos_mult, 0.1))

    if not candidates:
        return None
    return rng.choices(candidates, k=1, weights=weights)[0]


def _rate_players(ratings: dict[int, float], xi: list[int],
                   players: dict[int, Player], events: list[MatchEvent],
                   club_id: int, own_goals: int, opp_goals: int,
                   is_home_team: bool, formation: str = "4-3-3") -> None:
    """Generate 1-10 ratings for every starter on a team.
    Players out of position get a rating penalty."""
    from src.core.player import position_suitability

    positions = get_formation_positions(formation)

    # Base rating depends on team result
    if own_goals > opp_goals:
        base = rng.gaussian_clamped(7.2, 0.6, 6.0, 9.0)
    elif own_goals == opp_goals:
        base = rng.gaussian_clamped(6.5, 0.5, 5.5, 8.0)
    else:
        base = rng.gaussian_clamped(5.8, 0.6, 4.0, 7.5)

    # Count per-player event bonuses
    goal_count: dict[int, int] = {}
    assist_count: dict[int, int] = {}
    yellow_count: dict[int, int] = {}
    for ev in events:
        if ev.club_id != club_id:
            continue
        if ev.event_type == MatchEventType.GOAL and ev.player_id:
            goal_count[ev.player_id] = goal_count.get(ev.player_id, 0) + 1
        if ev.event_type == MatchEventType.GOAL and ev.second_player_id:
            assist_count[ev.second_player_id] = assist_count.get(ev.second_player_id, 0) + 1
        if ev.event_type == MatchEventType.YELLOW_CARD and ev.player_id:
            yellow_count[ev.player_id] = yellow_count.get(ev.player_id, 0) + 1

    for idx, pid in enumerate(xi):
        p = players.get(pid)
        if not p:
            continue
        r = base + rng.uniform(-0.4, 0.4)

        # Position suitability penalty on rating
        if idx < len(positions):
            suit = position_suitability(p, positions[idx])
            if suit < 1.0:
                # Out of position → lower rating (up to -1.5 for completely wrong)
                r -= (1.0 - suit) * 1.5

        # Goal bonus
        r += goal_count.get(pid, 0) * 0.8
        # Assist bonus
        r += assist_count.get(pid, 0) * 0.4
        # Yellow card penalty
        r -= yellow_count.get(pid, 0) * 0.3
        # Clean sheet bonus for defenders/GK
        if opp_goals == 0 and p.position.value in ("GK", "CB", "LB", "RB"):
            r += 0.3
        ratings[pid] = round(max(1.0, min(10.0, r)), 1)


