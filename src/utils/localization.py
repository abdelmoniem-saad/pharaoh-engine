"""
Localization support for English and Arabic.

Phase 1: English-only with string table architecture ready for Arabic.
"""
from __future__ import annotations

_current_language = "en"

# String tables keyed by language → key → display string
_strings: dict[str, dict[str, str]] = {
    "en": {
        # General
        "app_title": "Pharaoh Engine",
        "new_game": "New Game",
        "continue_game": "Continue",
        "settings": "Settings",
        "quit": "Quit",
        "back": "Back",
        "confirm": "Confirm",
        "cancel": "Cancel",
        "save": "Save",
        "load": "Load",

        # Screens
        "squad": "Squad",
        "tactics": "Tactics",
        "match_day": "Match Day",
        "league_table": "League Table",
        "inbox": "Inbox",
        "finances": "Finances",
        "transfers": "Transfers",

        # Match
        "kick_off": "Kick Off",
        "half_time": "Half Time",
        "full_time": "Full Time",
        "goal": "GOAL!",
        "yellow_card": "Yellow Card",
        "red_card": "Red Card",
        "substitution": "Substitution",
        "penalty": "Penalty",
        "injury": "Injury",
        "simulate": "Simulate Match",
        "home": "Home",
        "away": "Away",

        # League
        "position": "Pos",
        "team": "Team",
        "played": "P",
        "won": "W",
        "drawn": "D",
        "lost": "L",
        "goals_for": "GF",
        "goals_against": "GA",
        "goal_difference": "GD",
        "points": "Pts",

        # Player
        "name": "Name",
        "age": "Age",
        "overall": "OVR",
        "potential": "POT",

        # Tactics
        "formation": "Formation",
        "mentality": "Mentality",
        "ultra_defensive": "Ultra Defensive",
        "defensive": "Defensive",
        "cautious": "Cautious",
        "balanced": "Balanced",
        "positive": "Positive",
        "attacking": "Attacking",
        "ultra_attacking": "Ultra Attacking",

        # Calendar
        "next_match": "Next Match",
        "advance_day": "Advance Day",
        "matchday": "Matchday",

        # Season
        "season_end": "Season Over",
        "champion": "Champion!",
        "congratulations": "Congratulations!",
    },
    "ar": {
        "app_title": "محرك فرعون",
        "new_game": "لعبة جديدة",
        "continue_game": "استمرار",
        "settings": "الإعدادات",
        "quit": "خروج",
        "back": "رجوع",
        "confirm": "تأكيد",
        "cancel": "إلغاء",
        "save": "حفظ",
        "load": "تحميل",
        "squad": "التشكيلة",
        "tactics": "التكتيكات",
        "match_day": "يوم المباراة",
        "league_table": "جدول الدوري",
        "inbox": "البريد",
        "finances": "المالية",
        "transfers": "الانتقالات",
        "goal": "!هدف",
        "simulate": "محاكاة المباراة",
    },
}


def set_language(lang: str) -> None:
    """Set the active language."""
    global _current_language
    if lang in _strings:
        _current_language = lang


def get_language() -> str:
    """Get the current language code."""
    return _current_language


def t(key: str) -> str:
    """Translate a key to the current language. Falls back to English."""
    lang_table = _strings.get(_current_language, _strings["en"])
    return lang_table.get(key, _strings["en"].get(key, f"[{key}]"))

