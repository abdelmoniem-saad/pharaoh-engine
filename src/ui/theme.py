"""
UI Theme constants — centralized colors, spacing, and styling for mobile-first design.

Premium Egyptian pharaoh-themed visual language: rich dark gradients,
golden amber accents, frosted glass cards with glow borders.
Portrait-mode optimized for 360px–430px phone widths.
"""
from __future__ import annotations

import flet as ft

# ── Brand Palette ───────────────────────────────────────────────────────────
# Deep navy → teal gradient background inspired by Egyptian night sky
BG_DARK = "#0a0e1a"        # deepest background
BG_MID = "#0f1729"          # mid-tone panels
BG_SURFACE = "#141e33"      # card surfaces
BG_TEAL = "#0d2137"         # teal accent tone

# Golden / Amber — the pharaoh accent
GOLD = "#FFD54F"
GOLD_DARK = "#F9A825"
GOLD_GLOW = ft.Colors.with_opacity(0.25, "#FFD54F")
GOLD_BORDER = ft.Colors.with_opacity(0.18, "#FFD54F")
GOLD_BORDER_STRONG = ft.Colors.with_opacity(0.35, "#FFD54F")

ACCENT = ft.Colors.AMBER_400
ACCENT_DARK = ft.Colors.AMBER_700
ACCENT_BG = ft.Colors.with_opacity(0.10, ft.Colors.AMBER)

# ── Card / Glass surfaces ──────────────────────────────────────────────────
CARD_BG = ft.Colors.with_opacity(0.10, ft.Colors.WHITE)
CARD_GLASS = ft.Colors.with_opacity(0.08, ft.Colors.WHITE)       # frosted glass
CARD_GLASS_STRONG = ft.Colors.with_opacity(0.14, ft.Colors.WHITE) # elevated glass
CARD_BG_HOVER = ft.Colors.with_opacity(0.16, ft.Colors.WHITE)
CARD_BG_HIGHLIGHT = ft.Colors.with_opacity(0.12, ft.Colors.GREEN)
CARD_BG_DANGER = ft.Colors.with_opacity(0.12, ft.Colors.RED)

SECTION_BG = ft.Colors.with_opacity(0.05, ft.Colors.WHITE)

# ── Text ────────────────────────────────────────────────────────────────────
TEXT_PRIMARY = "#EAEAEA"
TEXT_SECONDARY = "#9E9E9E"
TEXT_MUTED = "#616161"
TEXT_SUCCESS = "#66BB6A"
TEXT_WARNING = "#FFCA28"
TEXT_DANGER = "#EF5350"
TEXT_INFO = "#42A5F5"

# Position colors
POS_GK = "#FFB300"
POS_DEF = "#42A5F5"
POS_MID = "#66BB6A"
POS_FWD = "#EF5350"

# ── Pitch ───────────────────────────────────────────────────────────────────
PITCH_DARK = "#1B5E20"
PITCH_LIGHT = "#2E7D32"
PITCH_LINE = ft.Colors.with_opacity(0.35, ft.Colors.WHITE)

# ── Spacing ─────────────────────────────────────────────────────────────────
CARD_RADIUS = 14
CARD_RADIUS_SM = 10
CARD_PADDING = 14
CARD_PADDING_SM = 10
PAGE_PADDING = 14
SECTION_SPACING = 12
ITEM_SPACING = 6

# ── Touch targets ───────────────────────────────────────────────────────
MIN_TOUCH_TARGET = 44
TOUCH_ROW_PADDING_V = 10
NAV_BAR_HEIGHT = 60

# ── Typography ──────────────────────────────────────────────────────────────
TITLE_SIZE = 22
SUBTITLE_SIZE = 15
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


# ── Premium Visual Helpers ──────────────────────────────────────────────────

def gradient_bg(
    colors: list[str] | None = None,
    begin=ft.Alignment(0, -1),
    end=ft.Alignment(0, 1),
) -> ft.LinearGradient:
    """Dark-to-teal vertical gradient for screen backgrounds."""
    return ft.LinearGradient(
        colors=colors or [BG_DARK, BG_MID, BG_TEAL],
        begin=begin,
        end=end,
    )


def screen_container(content: ft.Control, page: ft.Page | None = None) -> ft.Container:
    """Full-screen container with the signature dark gradient background."""
    return ft.Container(
        content=content,
        gradient=gradient_bg(),
        expand=True,
        padding=0,
    )


def glass_card(
    content: ft.Control,
    padding: int | ft.Padding = CARD_PADDING,
    border_color: str = GOLD_BORDER,
    border_radius: int = CARD_RADIUS,
    glow: bool = False,
    on_click=None,
) -> ft.Container:
    """Frosted-glass styled card with optional golden glow border."""
    shadow = None
    if glow:
        shadow = ft.BoxShadow(
            spread_radius=0, blur_radius=8,
            color=GOLD_GLOW, offset=ft.Offset(0, 0),
        )
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=border_radius,
        bgcolor=CARD_GLASS_STRONG,
        border=ft.border.all(1, border_color),
        shadow=shadow,
        on_click=on_click,
        ink=True if on_click else False,
    )


def header_bar(
    title: str,
    subtitle: str = "",
    icon: str | None = None,
    back_route: str | None = None,
    page: ft.Page | None = None,
    extra_controls: list | None = None,
    show_notification_bell: bool = True,
) -> ft.Container:
    """
    Premium gradient header bar for screens.
    Provides visual weight at the top of every game screen.
    Includes a notification bell with unread count badge.
    """
    left = []
    if icon:
        left.append(ft.Icon(icon, size=22, color=GOLD))
    left.append(
        ft.Column(spacing=0, expand=True, controls=[
            ft.Text(title, size=TITLE_SIZE, weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY),
            *([ ft.Text(subtitle, size=CAPTION_SIZE, color=TEXT_SECONDARY) ]
              if subtitle else []),
        ])
    )

    right = list(extra_controls or [])

    # Notification bell
    if show_notification_bell and page:
        try:
            from src.ui.app import app_state, navigate
            from src.data.queries import get_unread_count
            unread = 0
            if app_state.db_conn:
                unread = get_unread_count(app_state.db_conn)
            bell_icon = ft.Stack(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                        icon_size=20, icon_color=GOLD,
                        tooltip="Inbox",
                        on_click=lambda e: navigate(page, "/inbox"),
                    ),
                    *(
                        [ft.Container(
                            content=ft.Text(str(min(unread, 99)), size=8,
                                            color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.BOLD,
                                            text_align=ft.TextAlign.CENTER),
                            width=16, height=16, border_radius=8,
                            bgcolor=ft.Colors.RED_600,
                            alignment=ft.Alignment(0, 0),
                            top=4, right=4,
                        )] if unread > 0 else []
                    ),
                ],
                width=40, height=36,
            )
            right.insert(0, bell_icon)
        except Exception:
            pass

    if back_route and page:
        from src.ui.app import navigate

        def go_back(e):
            navigate(page, back_route)
        right.append(ft.IconButton(
            icon=ft.Icons.ARROW_BACK, icon_size=20,
            icon_color=TEXT_SECONDARY, tooltip="Back",
            on_click=go_back,
        ))

    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=10, expand=True, controls=left),
                ft.Row(spacing=0, controls=right) if right else ft.Container(),
            ],
        ),
        padding=ft.padding.only(left=PAGE_PADDING, right=8, top=12, bottom=10),
        gradient=ft.LinearGradient(
            colors=[BG_SURFACE, ft.Colors.with_opacity(0, BG_SURFACE)],
            begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
        ),
        border=ft.border.only(bottom=ft.BorderSide(1, GOLD_BORDER)),
    )


def golden_divider() -> ft.Container:
    """A subtle golden horizontal rule."""
    return ft.Container(
        height=1,
        bgcolor=GOLD_BORDER,
        margin=ft.margin.symmetric(vertical=4),
    )


# ── Button Style Presets ────────────────────────────────────────────────────

PRIMARY_BTN_STYLE = ft.ButtonStyle(
    bgcolor=ACCENT_DARK,
    color=ft.Colors.WHITE,
    text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
    shape=ft.RoundedRectangleBorder(radius=12),
    elevation=4,
    shadow_color=GOLD_GLOW,
)

SECONDARY_BTN_STYLE = ft.ButtonStyle(
    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
    color=TEXT_PRIMARY,
    text_style=ft.TextStyle(size=15),
    shape=ft.RoundedRectangleBorder(radius=12),
    side=ft.BorderSide(1, GOLD_BORDER),
)

DANGER_BTN_STYLE = ft.ButtonStyle(
    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.RED),
    color=TEXT_DANGER,
    shape=ft.RoundedRectangleBorder(radius=12),
    side=ft.BorderSide(1, ft.Colors.with_opacity(0.3, ft.Colors.RED)),
)


