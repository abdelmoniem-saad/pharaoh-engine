"""
Tactical system — formations, presets, and team selection logic.
"""
from __future__ import annotations

from src.data.models import Player, TacticalPreset, TeamTactics
from src.utils.config import Position, Mentality, FORMATION_TEMPLATES
from src.core.player import effective_ability, get_match_readiness


# ── Tactical Presets (Casual Mode) ───────────────────────────────────────────

PRESETS: dict[str, TacticalPreset] = {
    "park_the_bus": TacticalPreset(
        name="Park the Bus",
        formation="5-3-2",
        mentality=Mentality.ULTRA_DEFENSIVE,
        pressing_intensity=2,
        tempo=3,
        width=3,
        defensive_line=2,
        description="Maximum defensive solidity. Sit deep, stay compact, hit on the break.",
    ),
    "counter_attack": TacticalPreset(
        name="Counter Attack",
        formation="4-2-3-1",
        mentality=Mentality.CAUTIOUS,
        pressing_intensity=4,
        tempo=6,
        width=5,
        defensive_line=4,
        description="Absorb pressure, then strike quickly with pace on the wings.",
    ),
    "balanced": TacticalPreset(
        name="Balanced",
        formation="4-2-3-1",
        mentality=Mentality.BALANCED,
        pressing_intensity=5,
        tempo=5,
        width=5,
        defensive_line=5,
        description="A solid all-round approach. Adapt to the flow of the game.",
    ),
    "tiki_taka": TacticalPreset(
        name="Tiki-Taka",
        formation="4-3-3",
        mentality=Mentality.POSITIVE,
        pressing_intensity=7,
        tempo=4,
        width=6,
        defensive_line=7,
        description="Possession-based football. Short passing, high press, control the game.",
    ),
    "all_out_attack": TacticalPreset(
        name="All-Out Attack",
        formation="4-3-3",
        mentality=Mentality.ULTRA_ATTACKING,
        pressing_intensity=8,
        tempo=8,
        width=8,
        defensive_line=8,
        description="Throw everything forward. Maximum aggression and width.",
    ),
    "direct_play": TacticalPreset(
        name="Direct Play",
        formation="4-4-2",
        mentality=Mentality.ATTACKING,
        pressing_intensity=6,
        tempo=8,
        width=6,
        defensive_line=6,
        description="Get the ball forward quickly. Long balls, crosses, and set pieces.",
    ),
}


def get_available_formations() -> list[str]:
    """Return all available formation names."""
    return list(FORMATION_TEMPLATES.keys())


def get_formation_positions(formation: str) -> list[Position]:
    """Return the list of positions for a formation."""
    return FORMATION_TEMPLATES.get(formation, FORMATION_TEMPLATES["4-2-3-1"])


def get_preset(name: str) -> TacticalPreset:
    """Get a tactical preset by key name."""
    return PRESETS.get(name, PRESETS["balanced"])


def preset_to_tactics(preset: TacticalPreset) -> TeamTactics:
    """Convert a preset into a TeamTactics object."""
    return TeamTactics(
        formation=preset.formation,
        mentality=preset.mentality,
        pressing_intensity=preset.pressing_intensity,
        tempo=preset.tempo,
        width=preset.width,
        defensive_line=preset.defensive_line,
    )


def auto_select_xi(players: list[Player], formation: str) -> tuple[list[int], list[int]]:
    """
    Automatically select the best starting XI and bench for a formation.
    Excludes injured and suspended players.

    Returns (starting_xi_ids, bench_ids).
    """
    positions_needed = get_formation_positions(formation)

    # Filter out injured and suspended players
    available = [p for p in players
                 if p.injury_days_remaining <= 0 and p.suspension_matches <= 0]
    unavailable_ids = {p.id for p in players if p.id not in {a.id for a in available}}

    starting_xi: list[int] = []
    used_ids: set[int] = set()

    # For each position slot in the formation, pick the best available player
    for target_pos in positions_needed:
        best_player = None
        best_score = -1.0

        for p in available:
            if p.id in used_ids:
                continue
            # Score = effective ability × match readiness
            score = effective_ability(p, target_pos) * get_match_readiness(p)
            if score > best_score:
                best_score = score
                best_player = p

        if best_player:
            starting_xi.append(best_player.id)
            used_ids.add(best_player.id)

    # Bench: remaining players sorted by overall ability
    bench = [p.id for p in sorted(available, key=lambda x: x.current_ability, reverse=True)
             if p.id not in used_ids][:7]  # Max 7 subs on bench

    return starting_xi, bench


def calculate_team_strength(players: list[Player], tactics: TeamTactics) -> dict[str, float]:
    """
    Calculate composite team strength ratings for match simulation.
    Returns attack, midfield, defense, and overall ratings.
    """
    positions = get_formation_positions(tactics.formation)

    attack_attrs = []
    midfield_attrs = []
    defense_attrs = []
    gk_rating = 0.0

    # Map starting XI player IDs to players
    player_map = {p.id: p for p in players}

    for i, player_id in enumerate(tactics.starting_xi):
        if i >= len(positions):
            break
        player = player_map.get(player_id)
        if not player:
            continue

        a = player.attributes
        pos = positions[i]
        readiness = get_match_readiness(player)
        suit = 1.0  # simplified for team strength

        if pos == Position.GK:
            gk_rating = (a.gk_reflexes + a.gk_handling + a.gk_positioning +
                         a.gk_one_on_ones) / 4.0 * readiness
        elif pos in (Position.CB, Position.LB, Position.RB):
            defense_attrs.append(
                (a.tackling + a.marking + a.positioning + a.heading +
                 a.strength) / 5.0 * readiness
            )
        elif pos in (Position.CDM, Position.CM, Position.CAM, Position.LM, Position.RM):
            midfield_attrs.append(
                (a.passing + a.vision + a.dribbling + a.first_touch +
                 a.work_rate + a.stamina) / 6.0 * readiness
            )
        elif pos in (Position.LW, Position.RW, Position.ST):
            attack_attrs.append(
                (a.finishing + a.dribbling + a.pace + a.composure +
                 a.positioning) / 5.0 * readiness
            )

    attack = sum(attack_attrs) / max(len(attack_attrs), 1)
    midfield = sum(midfield_attrs) / max(len(midfield_attrs), 1)
    defense = (sum(defense_attrs) / max(len(defense_attrs), 1) + gk_rating) / 2.0
    overall = (attack * 0.3 + midfield * 0.35 + defense * 0.35)

    # Apply mentality modifiers
    mentality_attack_mod = {
        Mentality.ULTRA_DEFENSIVE: 0.8, Mentality.DEFENSIVE: 0.9,
        Mentality.CAUTIOUS: 0.95, Mentality.BALANCED: 1.0,
        Mentality.POSITIVE: 1.05, Mentality.ATTACKING: 1.1,
        Mentality.ULTRA_ATTACKING: 1.2,
    }
    mentality_defense_mod = {
        Mentality.ULTRA_DEFENSIVE: 1.2, Mentality.DEFENSIVE: 1.1,
        Mentality.CAUTIOUS: 1.05, Mentality.BALANCED: 1.0,
        Mentality.POSITIVE: 0.95, Mentality.ATTACKING: 0.9,
        Mentality.ULTRA_ATTACKING: 0.8,
    }

    attack *= mentality_attack_mod.get(tactics.mentality, 1.0)
    defense *= mentality_defense_mod.get(tactics.mentality, 1.0)

    # ── Tactical slider modifiers ────────────────────────────────────
    # pressing_intensity (1-10): high pressing boosts midfield but costs stamina
    press = getattr(tactics, "pressing_intensity", 5)
    midfield *= 0.9 + press * 0.02          # 0.92 .. 1.10
    defense *= 1.05 - press * 0.01          # 1.04 .. 0.95 (high press = riskier)

    # tempo (1-10): high tempo = more chances but less accuracy
    # (applied in match_engine's action_chance; here we nudge midfield control)
    tempo = getattr(tactics, "tempo", 5)
    midfield *= 1.05 - abs(tempo - 5) * 0.01  # optimal at 5, slight penalty at extremes

    # width (1-10): wide play boosts attack via crossing; narrow boosts central play
    width = getattr(tactics, "width", 5)
    attack *= 0.95 + width * 0.01            # 0.96 .. 1.05

    # defensive_line (1-10): high line compresses midfield; low line protects defense
    def_line = getattr(tactics, "defensive_line", 5)
    defense *= 1.05 - def_line * 0.01       # 1.04 .. 0.95
    midfield *= 0.95 + def_line * 0.01      # 0.96 .. 1.05

    return {
        "attack": round(attack, 2),
        "midfield": round(midfield, 2),
        "defense": round(defense, 2),
        "goalkeeper": round(gk_rating, 2),
        "overall": round(overall, 2),
    }

