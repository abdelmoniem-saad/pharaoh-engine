"""
UI Theme constants — centralized colors, spacing, and styling for mobile-first design.

All screens should import from here instead of hardcoding color/padding values.
Portrait-mode optimized for 360px–430px phone widths.
"""
from __future__ import annotations

import flet as ft

# ── Colors ──────────────────────────────────────────────────────────────────
ACCENT = ft.Colors.AMBER_400
ACCENT_DARK = ft.Colors.AMBER_700
ACCENT_BG = ft.Colors.with_opacity(0.08, ft.Colors.AMBER)

CARD_BG = ft.Colors.with_opacity(0.07, ft.Colors.WHITE)
CARD_BG_HOVER = ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
CARD_BG_HIGHLIGHT = ft.Colors.with_opacity(0.15, ft.Colors.GREEN)
CARD_BG_DANGER = ft.Colors.with_opacity(0.12, ft.Colors.RED)

SECTION_BG = ft.Colors.with_opacity(0.04, ft.Colors.WHITE)

TEXT_PRIMARY = ft.Colors.WHITE
TEXT_SECONDARY = ft.Colors.GREY_400
TEXT_MUTED = ft.Colors.GREY_600
TEXT_SUCCESS = ft.Colors.GREEN_400
TEXT_WARNING = ft.Colors.YELLOW_400
TEXT_DANGER = ft.Colors.RED_400
TEXT_INFO = ft.Colors.BLUE_400

# Position colors
POS_GK = ft.Colors.AMBER_600
POS_DEF = ft.Colors.BLUE_400
POS_MID = ft.Colors.GREEN_400
POS_FWD = ft.Colors.RED_400

# ── Spacing ─────────────────────────────────────────────────────────────────
CARD_RADIUS = 12
CARD_RADIUS_SM = 8
CARD_PADDING = 14
CARD_PADDING_SM = 10
PAGE_PADDING = 12
SECTION_SPACING = 10
ITEM_SPACING = 6

# ── Touch targets ───────────────────────────────────────────────────────────
MIN_TOUCH_TARGET = 44       # minimum height for tappable elements (px)
TOUCH_ROW_PADDING_V = 10    # vertical padding to reach ~44px touch height
NAV_BAR_HEIGHT = 60          # bottom nav bar consumes this much

# ── Typography ──────────────────────────────────────────────────────────────
TITLE_SIZE = 20
SUBTITLE_SIZE = 14
BODY_SIZE = 13
CAPTION_SIZE = 11
TINY_SIZE = 9

# ── Responsive helpers ──────────────────────────────────────────────────────

def get_page_width(page: ft.Page) -> int:
    """Get usable page width, defaulting to 390 if not yet known."""
    try:
        w = page.width
        if w and w > 0:
            return int(w)
    except Exception:
        pass
    return 390  # iPhone 14 default


def content_width(page: ft.Page) -> int:
    """Usable content width = page width minus 2 * PAGE_PADDING."""
    return get_page_width(page) - 2 * PAGE_PADDING


def pitch_width(page: ft.Page) -> int:
    """Width for pitch visualizations — fits within content area with some margin."""
    return min(content_width(page) - 8, 320)


def pitch_height(page: ft.Page) -> int:
    """Height for pitch — 4:3 aspect ratio based on pitch_width."""
    pw = pitch_width(page)
    return int(pw * 1.28)  # ~360 for 280px width


def dialog_width(page: ft.Page) -> int:
    """Safe dialog content width — always fits even on 360px phones."""
    return min(get_page_width(page) - 60, 300)


# ── Position color helpers ──────────────────────────────────────────────────

def position_color(pos_value: str) -> str:
    """Get the color for a position value string."""
    if pos_value == "GK":
        return POS_GK
    elif pos_value in ("CB", "LB", "RB"):
        return POS_DEF
    elif pos_value in ("CDM", "CM", "CAM", "LM", "RM"):
        return POS_MID
    elif pos_value in ("ST", "LW", "RW"):
        return POS_FWD
    return TEXT_SECONDARY


def ovr_color(ovr: int) -> str:
    """Get color based on overall rating."""
    if ovr >= 78:
        return ft.Colors.GREEN_300
    elif ovr >= 68:
        return ft.Colors.LIGHT_GREEN_400
    elif ovr >= 58:
        return TEXT_WARNING
    elif ovr >= 48:
        return ft.Colors.ORANGE_400
    return TEXT_DANGER


def fitness_color(fitness: int) -> str:
    """Get color based on fitness percentage."""
    if fitness >= 80:
        return TEXT_SUCCESS
    elif fitness >= 50:
        return TEXT_WARNING
    return TEXT_DANGER

