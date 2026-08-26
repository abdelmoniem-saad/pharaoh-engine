"""
Long-term player development plans.

A plan is a season-long commitment the manager sets on a player. Every
in-game week it builds progress and nudges targeted attributes; conversion
plans can ultimately retrain a player into a new position entirely.

Progress speed follows age curves and is gated by potential headroom, so
youngsters fly through plans while veterans grind — making youth investment
a real long-term strategy rather than a cosmetic label.
"""
from __future__ import annotations

from src.data.models import Player
from src.utils.config import Position
from src.utils import rng


# ── Plan catalog ────────────────────────────────────────────────────────────
# key → {"label", "focus": [attribute names], "conversion": (from_positions,
# target_position) | None}
PLANS: dict[str, dict] = {
    # Attribute-focus programmes
    "finisher":  {"label": "🎯 Finisher",   "focus": ["finishing", "composure", "positioning"],
                  "conversion": None},
    "playmaker": {"label": "🧠 Playmaker",  "focus": ["vision", "passing", "first_touch"],
                  "conversion": None},
    "engine":    {"label": "🔋 Engine",     "focus": ["stamina", "work_rate", "agility"],
                  "conversion": None},
    "rock":      {"label": "🧱 Rock",       "focus": ["tackling", "marking", "heading"],
                  "conversion": None},
    "speedster": {"label": "💨 Speedster",  "focus": ["pace", "agility", "dribbling"],
                  "conversion": None},
    # Position-conversion programmes
    "conv_st":   {"label": "🔁 Retrain → Striker",
                  "focus": ["finishing", "positioning", "composure"],
                  "conversion": ({Position.LW, Position.RW}, Position.ST)},
    "conv_cdm":  {"label": "🔁 Retrain → Anchor (CDM)",
                  "focus": ["tackling", "positioning", "strength"],
                  "conversion": ({Position.CM, Position.CAM}, Position.CDM)},
    "conv_cb":   {"label": "🔁 Retrain → Centre-Back",
                  "focus": ["marking", "heading", "strength"],
                  "conversion": ({Position.LB, Position.RB}, Position.CB)},
    "conv_cm":   {"label": "🔁 Retrain → Box-to-Box (CM)",
                  "focus": ["work_rate", "passing", "stamina"],
                  "conversion": ({Position.CAM}, Position.CM)},
}


def plan_label(key: str) -> str:
    """Human-readable label for a plan key."""
    return PLANS.get(key, {}).get("label", key)


def _age_speed(age: int) -> float:
    """Learning speed multiplier by age — kids learn, veterans grind."""
    if age <= 20:
        return 1.6
    if age <= 24:
        return 1.25
    if age <= 28:
        return 1.0
    if age <= 31:
        return 0.6
    return 0.3


def _headroom(p: Player) -> int:
    """Ability growth remaining before the player hits his potential."""
    try:
        return max(0, int(p.potential_ability) - int(p.current_ability))
    except Exception:
        return 10


def apply_weekly_development(player: Player) -> str | None:
    """
    Advance *player*'s development plan by one in-game week.

    Returns a short news line when something notable happened (attribute
    improvement, position conversion, programme completion), else None.
    """
    key = getattr(player, "dev_plan", "")
    if not key:
        return None
    plan = PLANS.get(key)
    if not plan:
        return None

    focus = plan["focus"]
    a = player.attributes

    speed = _age_speed(int(getattr(player, "age", 25)))
    headroom = _headroom(player)
    speed *= 1.15 if headroom > 8 else (0.75 if headroom > 2 else 0.35)

    notes: list[str] | None = None

    # ── Attribute growth chance this week ─────────────────────────────
    grew_attr = None
    if rng.chance(min(0.85, 0.30 * speed)) and headroom > 2:
        attr_name = focus[rng.randint(0, len(focus) - 1)]
        current_val = int(getattr(a, attr_name, 10))
        if current_val < 18:
            setattr(a, attr_name, min(19, current_val + 1))
            player.current_ability = min(
                int(player.potential_ability), int(player.current_ability) + 2
            )
            grew_attr = attr_name

    # ── Progress build ────────────────────────────────────────────────
    gain = max(1, round(6 * speed)) + rng.randint(0, 2)
    before = int(getattr(player, "dev_progress", 0))
    player.dev_progress = min(100, before + gain)

    if grew_attr:
        notes = f"📈 {player.name} improved {grew_attr.title()} through his {plan['label']} plan."

    # ── Completion ────────────────────────────────────────────────────
    if player.dev_progress >= 100:
        conv = plan.get("conversion")
        if conv:
            from_positions, target_pos = conv
            if player.position in from_positions:
                player.position = target_pos
                player.dev_plan = ""
                player.dev_progress = 0
                return f"🔄 {player.name} completed his retraining — now a {target_pos.value}!"
            player.dev_plan = ""
            player.dev_progress = 0
            return f"🏅 {player.name} completed the '{plan['label']}' programme."
        player.dev_plan = ""
        player.dev_progress = 0
        return f"🏅 {player.name} mastered the '{plan['label']}' programme."

    return notes
