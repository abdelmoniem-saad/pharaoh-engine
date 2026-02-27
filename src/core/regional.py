"""
Regional talent dynamics — governorate-based player generation profiles.

Maps Egyptian governorates to talent pool characteristics that influence
player generation: attribute bonuses, volume, and playing style bias.
"""
from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass
from src.utils.config import EGYPTIAN_GOVERNORATES

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "seed"


@dataclass
class GovernorateProfile:
    """Talent profile for an Egyptian governorate."""
    name: str
    talent_pool: str          # very_high, high, medium, low, very_low
    style_bias: str           # technical, physical, creative, pacy, etc.
    description: str
    attribute_bonuses: dict[str, int]
    player_volume: float      # Multiplier for number of players generated


_profiles: dict[str, GovernorateProfile] = {}


def load_governorate_profiles() -> dict[str, GovernorateProfile]:
    """Load governorate profiles from JSON seed data."""
    global _profiles
    if _profiles:
        return _profiles

    filepath = DATA_DIR / "governorates.json"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return _get_default_profiles()

    for name, info in data.get("governorates", {}).items():
        _profiles[name] = GovernorateProfile(
            name=name,
            talent_pool=info.get("talent_pool", "medium"),
            style_bias=info.get("style_bias", "balanced"),
            description=info.get("description", ""),
            attribute_bonuses=info.get("attribute_bonuses", {}),
            player_volume=info.get("player_volume", 0.5),
        )

    return _profiles


def get_profile(governorate: str) -> GovernorateProfile:
    """Get the talent profile for a governorate."""
    profiles = load_governorate_profiles()
    return profiles.get(governorate, GovernorateProfile(
        name=governorate,
        talent_pool="low",
        style_bias="balanced",
        description="Unknown region.",
        attribute_bonuses={},
        player_volume=0.3,
    ))


def apply_regional_bonuses(attributes: dict[str, int],
                            governorate: str) -> dict[str, int]:
    """Apply governorate-specific attribute bonuses to a player."""
    profile = get_profile(governorate)
    result = dict(attributes)
    for attr, bonus in profile.attribute_bonuses.items():
        if attr in result:
            result[attr] = min(20, result[attr] + bonus)
    return result


def _get_default_profiles() -> dict[str, GovernorateProfile]:
    """Fallback profiles if JSON data is not available."""
    defaults = {}
    for gov in EGYPTIAN_GOVERNORATES:
        defaults[gov] = GovernorateProfile(
            name=gov,
            talent_pool="medium",
            style_bias="balanced",
            description=f"Football talent from {gov}.",
            attribute_bonuses={},
            player_volume=0.5,
        )
    return defaults

