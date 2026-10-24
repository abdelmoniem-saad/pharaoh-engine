"""
UI Theme constants — centralized colors, spacing, and styling for mobile-first design.

Restrained club-management workspace with opaque surfaces and clear hierarchy.
Portrait-mode optimized for 360px–430px phone widths.
"""
from __future__ import annotations

import flet as ft
from src.utils.localization import is_rtl as rtl, t

# ── Brand Palette ───────────────────────────────────────────────────────────
# Deep navy → teal gradient background inspired by Egyptian night sky
BG_DARK = "#10141B"        # deepest background
BG_MID = "#171D26"          # mid-tone panels
BG_SURFACE = "#202833"      # card surfaces
BG_TEAL = "#202833"         # teal accent tone

# Golden / Amber — the pharaoh accent
GOLD = "#DDC08A"
GOLD_DARK = "#9C7741"
GOLD_GLOW = ft.Colors.with_opacity(0.25, "#FFD54F")
GOLD_BORDER = "#2C3642"
GOLD_BORDER_STRONG = "#596674"

ACCENT = "#DDC08A"
ACCENT_DARK = "#795B2F"
ACCENT_BG = ft.Colors.with_opacity(0.10, ft.Colors.AMBER)

# ── Card / Glass surfaces ──────────────────────────────────────────────────
CARD_BG = "#1B222C"
CARD_GLASS = "#171D26"
CARD_GLASS_STRONG = "#1B222C"
CARD_BG_HOVER = "#25303D"
CARD_BG_HIGHLIGHT = ft.Colors.with_opacity(0.12, ft.Colors.GREEN)
CARD_BG_DANGER = ft.Colors.with_opacity(0.12, ft.Colors.RED)

SECTION_BG = "#171D26"

# ── Text ────────────────────────────────────────────────────────────────────
TEXT_PRIMARY = "#F1F3F5"
TEXT_SECONDARY = "#B3BDC8"
TEXT_MUTED = "#91A0B3"
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
CARD_RADIUS = 16
CARD_RADIUS_SM = 10
CARD_PADDING = 20
CARD_PADDING_SM = 10
PAGE_PADDING = 20
SECTION_SPACING = 24
ITEM_SPACING = 12

# ── Touch targets ───────────────────────────────────────────────────────
MIN_TOUCH_TARGET = 44
TOUCH_ROW_PADDING_V = 10
NAV_BAR_HEIGHT = 60

# ── Typography ──────────────────────────────────────────────────────────────
TITLE_SIZE = 28
SUBTITLE_SIZE = 15
BODY_SIZE = 15
CAPTION_SIZE = 12
TINY_SIZE = 11

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
        colors=colors or [BG_DARK, BG_DARK],
        begin=begin,
        end=end,
    )


def screen_container(content: ft.Control, page: ft.Page | None = None) -> ft.Container:
    """Full-screen container with the signature dark gradient background."""
    return ft.Container(
        rtl=rtl(), content=content,
        gradient=gradient_bg(),
        expand=True,
        padding=0,
    )


def glass_card(
    content: ft.Control,
    padding: int | ft.Padding = CARD_PADDING,
    border_color: str | None = None,
    border_radius: int | None = None,
    glow: bool = False,
    on_click=None,
) -> ft.Container:
    """Frosted-glass styled card with optional golden glow border."""
    border_color = GOLD_BORDER if border_color is None else border_color
    border_radius = CARD_RADIUS if border_radius is None else border_radius
    shadow = None
    return ft.Container(
        rtl=rtl(), content=content,
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
    # Screen title provides hierarchy; icons are reserved for actions.
    left.append(
        ft.Column(rtl=rtl(), spacing=6, expand=True, controls=[
            ft.Text(title, rtl=rtl(), size=TITLE_SIZE + 4, font_family=display_font(), weight=ft.FontWeight.BOLD,
                    color=TEXT_PRIMARY),
            *([ ft.Text(subtitle, rtl=rtl(), size=CAPTION_SIZE, color=TEXT_SECONDARY) ]
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
                rtl=rtl(), controls=[
                    ft.IconButton(
                        rtl=rtl(), icon=ft.Icons.NOTIFICATIONS_OUTLINED,
                        icon_size=20, icon_color=GOLD,
                        tooltip=t("inbox"),
                        on_click=lambda e: navigate(page, "/inbox"),
                    ),
                    *(
                        [ft.Container(
                            rtl=rtl(), content=ft.Text(str(min(unread, 99)), rtl=rtl(), size=8,
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
            rtl=rtl(), icon=ft.Icons.ARROW_BACK, icon_size=20,
            icon_color=TEXT_SECONDARY, tooltip=t("back"),
            on_click=go_back,
        ))

    return ft.Container(
        rtl=rtl(), content=ft.Row(
            rtl=rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(rtl=rtl(), spacing=10, expand=True, controls=left),
                ft.Row(rtl=rtl(), spacing=0, controls=right) if right else ft.Container(rtl=rtl()),
            ],
        ),
        padding=ft.padding.only(left=0, right=0, top=12, bottom=16),

    )


def golden_divider() -> ft.Container:
    """A subtle golden horizontal rule."""
    return ft.Container(
        rtl=rtl(), height=1,
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



# Theme names describe the game UI, not a claimed brand partnership.
THEME_NAMES = {"classic": ("Classic Pharaoh", "الفرعون الكلاسيكي"),
               "supporter": ("Supporter", "المدرج")}
SECONDARY_ACCENT = "#69C5DD"
_classic = {key: value for key, value in globals().copy().items() if key.isupper()}
_active = "classic"


def current_theme() -> str:
    return _active


def configure(name: str) -> None:
    """Select a palette; consumers access this module when building controls."""
    global _active, PRIMARY_BTN_STYLE, SECONDARY_BTN_STYLE
    _active = name if name in THEME_NAMES else "classic"
    globals().update(_classic)
    if _active == "supporter":
        globals().update(
            BG_DARK="#11191F", BG_MID="#18252D", BG_SURFACE="#23343E", BG_TEAL="#123B48",
            GOLD="#FFAC7A", GOLD_DARK="#C34A15", ACCENT="#FFAC7A", ACCENT_DARK="#AA3D10",
            ACCENT_BG="#332D27", GOLD_GLOW="#334F2818", GOLD_BORDER="#2C3C45",
            GOLD_BORDER_STRONG="#69C5DD", CARD_BG="#23343E", CARD_GLASS="#1D2C35",
            CARD_GLASS_STRONG="#1B2B33", CARD_BG_HOVER="#304652", SECTION_BG="#18252D",
            TEXT_PRIMARY="#F5F3ED", TEXT_SECONDARY="#BDC9CD", TEXT_MUTED="#A4B5BD",
            CARD_RADIUS=16, CARD_RADIUS_SM=10, TITLE_SIZE=28, BODY_SIZE=15,
            CAPTION_SIZE=12, TINY_SIZE=11, SECTION_SPACING=24,
        )
    PRIMARY_BTN_STYLE = ft.ButtonStyle(
        bgcolor=ACCENT_DARK, color="#FFFFFF",
        text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD),
        shape=ft.RoundedRectangleBorder(radius=CARD_RADIUS_SM), elevation=0,
        padding=ft.padding.symmetric(horizontal=24, vertical=14),
    )
    SECONDARY_BTN_STYLE = ft.ButtonStyle(
        bgcolor=CARD_GLASS_STRONG, color=TEXT_PRIMARY,
        text_style=ft.TextStyle(size=15),
        shape=ft.RoundedRectangleBorder(radius=CARD_RADIUS_SM),
        side=ft.BorderSide(1, GOLD_BORDER),
    )


def display_font() -> str:
    from src.utils.localization import is_rtl
    return "NotoArabic" if is_rtl() else "BarlowDisplay"


def apply_to_page(page: ft.Page) -> None:
    from src.utils.localization import is_rtl
    page.bgcolor = BG_DARK
    page.fonts = {"BarlowDisplay": "fonts/BarlowCondensed-Bold.ttf",
                  "NotoArabic": "fonts/NotoSansArabic.ttf"}
    page.theme = ft.Theme(color_scheme_seed=ACCENT,
                          font_family="NotoArabic" if is_rtl() else "Roboto",
        color_scheme=ft.ColorScheme(primary=ACCENT, on_primary=BG_DARK,
            surface=BG_MID, on_surface=TEXT_PRIMARY, on_surface_variant=TEXT_SECONDARY,
            outline=GOLD_BORDER_STRONG, outline_variant=GOLD_BORDER),
        dialog_theme=ft.DialogTheme(bgcolor=CARD_GLASS_STRONG, elevation=0,
            shape=ft.RoundedRectangleBorder(radius=18),
            title_text_style=ft.TextStyle(size=24, font_family=display_font(), color=TEXT_PRIMARY),
            content_text_style=ft.TextStyle(size=14, color=TEXT_SECONDARY)),
        outlined_button_theme=ft.OutlinedButtonTheme(style=ft.ButtonStyle(
            color=TEXT_PRIMARY, side=ft.BorderSide(1, GOLD_BORDER_STRONG),
            shape=ft.RoundedRectangleBorder(radius=10))),
    )


def theme_label(arabic: bool = False) -> str:
    return THEME_NAMES[_active][1 if arabic else 0]


def tab_style(selected: bool) -> ft.ButtonStyle:
    """One selection treatment for navigation within a screen."""
    return ft.ButtonStyle(color=TEXT_PRIMARY if selected else TEXT_MUTED,
        bgcolor=BG_SURFACE if selected else ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=14, vertical=12))


def scoreline(home, away) -> str:
    """Keep each score adjacent to its club when the fixture row is mirrored."""
    values = f"{away} : {home}" if rtl() else f"{home} : {away}"
    # Isolate the numeric pair from surrounding RTL text, including Flutter inheritance.
    return "\u2066" + values + "\u2069"


def leading_border(color, outline=False):
    edge = ft.BorderSide(3, color)
    neutral = ft.BorderSide(1, GOLD_BORDER) if outline else ft.BorderSide(0, ft.Colors.TRANSPARENT)
    return ft.border.only(left=neutral if rtl() else edge, right=edge if rtl() else neutral,
                          top=neutral, bottom=neutral)
