"""
Shared card widgets — mobile-first reusable UI components.

Every screen should compose these primitives instead of building
raw ft.Container / ft.Row layouts inline.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme
from src.utils.localization import t


# ── Empty State ─────────────────────────────────────────────────────────────

def empty_state(icon, title: str, subtitle: str = "") -> ft.Container:
    """Friendly centered placeholder for empty lists and screens."""
    controls = [
        ft.Icon(icon, size=52, color=theme.TEXT_MUTED),
        ft.Container(height=10),
        ft.Text(title, size=theme.BODY_SIZE, weight=ft.FontWeight.W_600,
                color=theme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
    ]
    if subtitle:
        controls.append(ft.Container(height=4))
        controls.append(ft.Text(subtitle, size=theme.CAPTION_SIZE,
                                color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER))
    return ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=controls,
        ),
        padding=40,
        alignment=ft.Alignment(0, 0),
    )


# ── Section Card ────────────────────────────────────────────────────────────

def section_card(
    title: str,
    controls: list,
    icon: str | None = None,
    title_color: str = None,
    collapsed: bool = False,
    extra_action: ft.Control | None = None,
) -> ft.Container:
    """
    A titled card section — frosted glass style with golden accent border.
    """
    title_color = theme.ACCENT if title_color is None else title_color
    header_controls = []
    if icon:
        header_controls.append(ft.Icon(icon, size=16, color=title_color))
    header_controls.append(
        ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=title_color, expand=True)
    )
    if extra_action:
        header_controls.append(extra_action)

    return ft.Container(
        content=ft.Column(
            spacing=theme.ITEM_SPACING,
            controls=[
                ft.Row(controls=header_controls, spacing=6),
                *(controls if not collapsed else []),
            ],
        ),
        padding=theme.CARD_PADDING,
        border_radius=theme.CARD_RADIUS,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.only(
            left=ft.BorderSide(3, title_color),
            top=ft.BorderSide(1, theme.GOLD_BORDER),
            right=ft.BorderSide(1, theme.GOLD_BORDER),
            bottom=ft.BorderSide(1, theme.GOLD_BORDER),
        ),
        shadow=ft.BoxShadow(
            spread_radius=0, blur_radius=6,
            color=ft.Colors.with_opacity(0.08, title_color),
        ),
    )


# ── Collapsible Section ─────────────────────────────────────────────────────

def collapsible_section(
    title: str,
    controls: list,
    initially_expanded: bool = False,
    title_color: str = None,
    icon: str | None = None,
    subtitle: str | None = None,
) -> ft.Container:
    """
    A collapsible card section — tap header to expand / collapse.
    Same visual language as section_card but with progressive disclosure.
    """
    title_color = theme.ACCENT if title_color is None else title_color
    leading = None
    if icon:
        leading = ft.Icon(icon, size=16, color=title_color)

    return ft.Container(
        content=ft.ExpansionTile(
            title=ft.Text(title, size=13, weight=ft.FontWeight.W_600,
                          color=title_color),
            subtitle=ft.Text(subtitle, size=theme.TINY_SIZE, color=theme.TEXT_MUTED) if subtitle else None,
            leading=leading,
            controls=controls,
            expanded=initially_expanded,
            maintain_state=True,
            controls_padding=ft.padding.only(left=8, right=8, bottom=8),
            tile_padding=ft.padding.symmetric(horizontal=10, vertical=4),
            icon_color=title_color,
            collapsed_icon_color=theme.TEXT_MUTED,
            text_color=title_color,
            collapsed_text_color=theme.TEXT_SECONDARY,
            bgcolor=ft.Colors.TRANSPARENT,
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            dense=True,
        ),
        border_radius=theme.CARD_RADIUS,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.only(
            left=ft.BorderSide(3, title_color),
            top=ft.BorderSide(1, theme.GOLD_BORDER),
            right=ft.BorderSide(1, theme.GOLD_BORDER),
            bottom=ft.BorderSide(1, theme.GOLD_BORDER),
        ),
    )


# ── Info Tile ───────────────────────────────────────────────────────────────

def info_tile(
    label: str,
    value: str,
    icon=None,
    color: str = None,
    width: int | None = None,
) -> ft.Container:
    """
    Small rounded info block — replaces _info_chip, _summary_chip, _card_row.

    Displays icon + label + value in a compact pill.
    """
    color = theme.TEXT_PRIMARY if color is None else color
    inner = ft.Row(
        spacing=4, tight=True,
        controls=[
            *([ ft.Icon(icon, size=13, color=theme.ACCENT) ] if icon else []),
            ft.Column(spacing=0, controls=[
                ft.Text(label, size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
                ft.Text(value, size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD, color=color),
            ]),
        ],
    )
    return ft.Container(
        content=inner,
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=theme.CARD_RADIUS_SM,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.all(1, theme.GOLD_BORDER),
        width=width,
    )


# ── KV Row ──────────────────────────────────────────────────────────────────

def kv_row(
    label: str, value: str,
    color: str | None = None,
    bold: bool = True,
) -> ft.Container:
    """
    Full-width key-value row — replaces _finance_row scattered across files.
    """
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, size=theme.BODY_SIZE, color=theme.TEXT_SECONDARY),
                ft.Text(value, size=theme.BODY_SIZE,
                        weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
                        color=color or theme.TEXT_PRIMARY),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=8, vertical=3),
    )


# ── Badge ───────────────────────────────────────────────────────────────────

def badge(
    text: str,
    color: str = ft.Colors.WHITE,
    bgcolor: str = ft.Colors.RED_400,
    size: int = 9,
) -> ft.Container:
    """Small colored pill badge (e.g. "NEW", "C", "🏥")."""
    return ft.Container(
        content=ft.Text(text, size=size, color=color, weight=ft.FontWeight.BOLD),
        bgcolor=bgcolor,
        padding=ft.padding.symmetric(horizontal=5, vertical=2),
        border_radius=4,
    )


# ── Form Chips Row ──────────────────────────────────────────────────────────

def form_chips(results: list[str]) -> ft.Row:
    """
    Build W/D/L form display from a list of result types.

    results: list of "W", "D", "L" strings.
    """
    color_map = {"W": theme.TEXT_SUCCESS, "D": theme.TEXT_WARNING, "L": theme.TEXT_DANGER}
    chips = [
        ft.Container(
            content=ft.Text(r, size=10, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            width=22, height=22, border_radius=11,
            bgcolor=color_map.get(r, theme.TEXT_MUTED),
            alignment=ft.Alignment(0, 0),
        )
        for r in results
    ]
    return ft.Row(spacing=3, controls=chips if chips else [
        ft.Text("—", size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED)
    ])


# ── Stat Comparison Bar ────────────────────────────────────────────────────

def stat_comparison_bar(
    home_val: str, away_val: str, label: str,
    home_color: str = ft.Colors.GREEN_400,
    away_color: str = ft.Colors.BLUE_400,
) -> ft.Container:
    """Visual stat comparison bar — for post-match / match preview. Fully responsive."""
    try:
        hv = float(home_val.replace('%', ''))
        av = float(away_val.replace('%', ''))
    except ValueError:
        hv = av = 0
    total = hv + av if (hv + av) > 0 else 1
    # Use expand (flex) ratio so bars auto-fill available width
    home_flex = max(1, int(hv / total * 100))
    away_flex = max(1, int((1 - hv / total) * 100))

    return ft.Container(
        content=ft.Column(spacing=2, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text(home_val, size=12, weight=ft.FontWeight.BOLD),
                ft.Text(label, size=10, color=theme.TEXT_MUTED),
                ft.Text(away_val, size=12, weight=ft.FontWeight.BOLD),
            ]),
            ft.Row(spacing=2, controls=[
                ft.Container(
                    expand=home_flex, height=4,
                    bgcolor=home_color, border_radius=2,
                ),
                ft.Container(
                    expand=away_flex, height=4,
                    bgcolor=away_color, border_radius=2,
                ),
            ]),
        ]),
        padding=ft.padding.symmetric(vertical=2),
    )


# ── Action Card ─────────────────────────────────────────────────────────────

def action_card(
    title: str,
    subtitle: str = "",
    icon: str = ft.Icons.ARROW_FORWARD,
    on_click=None,
    color: str = None,
) -> ft.Container:
    """
    Full-width tappable navigation card — for "Go to Transfers", "View Table", etc.
    """
    color = theme.ACCENT if color is None else color
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, tight=True, controls=[
                    ft.Icon(icon, size=20, color=color),
                    ft.Column(spacing=0, controls=[
                        ft.Text(title, size=theme.BODY_SIZE, weight=ft.FontWeight.W_600),
                        *([ ft.Text(subtitle, size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY) ]
                          if subtitle else []),
                    ]),
                ]),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=theme.ACCENT),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
        border_radius=theme.CARD_RADIUS,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.all(1, theme.GOLD_BORDER),
        on_click=on_click,
        ink=True,
    )


# ── Match Score Card ────────────────────────────────────────────────────────

def match_score_card(
    home_name: str, away_name: str,
    home_goals: int | str = "", away_goals: int | str = "",
    competition: str = "",
    matchday: str = "",
    is_home: bool = True,
    date_str: str = "",
) -> ft.Card:
    """
    FIFA-style match VS card.
    """
    home_weight = ft.FontWeight.BOLD if is_home else ft.FontWeight.NORMAL
    away_weight = ft.FontWeight.BOLD if not is_home else ft.FontWeight.NORMAL
    home_icon_color = theme.TEXT_SUCCESS if is_home else theme.TEXT_MUTED
    away_icon_color = theme.TEXT_SUCCESS if not is_home else theme.TEXT_MUTED

    score = f"{home_goals} - {away_goals}" if home_goals != "" else "VS"
    score_color = theme.ACCENT if home_goals == "" else theme.TEXT_PRIMARY

    return ft.Card(
        content=ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=16),
            bgcolor=theme.CARD_GLASS_STRONG,
            border_radius=theme.CARD_RADIUS,
            border=ft.border.all(1, theme.GOLD_BORDER),
            shadow=ft.BoxShadow(
                spread_radius=0, blur_radius=8,
                color=ft.Colors.with_opacity(0.10, theme.ACCENT),
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    *([ ft.Container(
                        content=ft.Text(competition, size=theme.CAPTION_SIZE, color=theme.ACCENT,
                                        weight=ft.FontWeight.W_600),
                        padding=ft.padding.symmetric(horizontal=10, vertical=3),
                        border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.10, theme.ACCENT),
                    )] if competition else []),
                    *([ ft.Text(matchday, size=theme.TINY_SIZE, color=theme.TEXT_MUTED) ] if matchday else []),
                    ft.Container(height=4),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
                        controls=[
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4, width=110,
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.SHIELD, size=28,
                                                        color=home_icon_color),
                                        width=44, height=44, border_radius=22,
                                        bgcolor=ft.Colors.with_opacity(0.1, home_icon_color),
                                        alignment=ft.Alignment(0, 0),
                                    ),
                                    ft.Text(home_name, size=12, weight=home_weight,
                                            text_align=ft.TextAlign.CENTER, max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                            ),
                            ft.Text(score, size=24, weight=ft.FontWeight.BOLD,
                                    color=score_color),
                            ft.Column(
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                spacing=4, width=110,
                                controls=[
                                    ft.Container(
                                        content=ft.Icon(ft.Icons.SHIELD, size=28,
                                                        color=away_icon_color),
                                        width=44, height=44, border_radius=22,
                                        bgcolor=ft.Colors.with_opacity(0.1, away_icon_color),
                                        alignment=ft.Alignment(0, 0),
                                    ),
                                    ft.Text(away_name, size=12, weight=away_weight,
                                            text_align=ft.TextAlign.CENTER, max_lines=2,
                                            overflow=ft.TextOverflow.ELLIPSIS),
                                ],
                            ),
                        ],
                    ),
                    *([ ft.Text(date_str, size=theme.TINY_SIZE, color=theme.TEXT_MUTED) ] if date_str else []),
                ],
            ),
        ),
    )


# ── Player Card (Horizontal) ───────────────────────────────────────────────

def player_card_h(
    name: str,
    position: str,
    ovr: int,
    age: int,
    fitness: int = 100,
    form: float = 7.0,
    morale: int = 50,
    is_captain: bool = False,
    is_injured: bool = False,
    is_suspended: bool = False,
    transfer_listed: bool = False,
    training_focus: str = "",
    on_click=None,
    highlight: bool = False,
) -> ft.Container:
    """
    FIFA-style horizontal player card (72px tall).

    ┌──────────────────────────────────────────────┐
    │  [OVR]  Name  ©🏥🚫        FIT  😊  🏋️    │
    │  [POS]  Age XX  Form 7.2                     │
    └──────────────────────────────────────────────┘
    """

    pos_clr = theme.position_color(position)
    ovr_clr = theme.ovr_color(ovr)
    fit_clr = theme.fitness_color(fitness)

    # Name with badges
    name_badges = []
    if is_captain:
        name_badges.append(badge("C", bgcolor=theme.ACCENT_DARK, size=8))
    if is_injured:
        name_badges.append(badge("🏥", bgcolor=ft.Colors.RED_800, size=8))
    if is_suspended:
        name_badges.append(badge("🚫", bgcolor=ft.Colors.ORANGE_800, size=8))
    if transfer_listed:
        name_badges.append(badge("📤", bgcolor=ft.Colors.RED_700, size=8))

    morale_emoji = "😊" if morale >= 70 else "😐" if morale >= 40 else "😞"

    train_map = {
        "Shooting": "⚽", "Defending": "🛡️", "Physical": "🏃",
        "Playmaking": "🎯", "Mental": "🧠", "Goalkeeping": "🧤",
        "Set Pieces": "🎯", "Balanced": "⚖️",
    }
    train_label = train_map.get(training_focus, "")

    return ft.Container(
        content=ft.Row(
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                # Left: OVR + Position badge
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2, width=40,
                    controls=[
                        ft.Container(
                            content=ft.Text(str(ovr), size=16, weight=ft.FontWeight.BOLD,
                                            color=ovr_clr, text_align=ft.TextAlign.CENTER),
                            width=38, height=28,
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(
                            content=ft.Text(position, size=9, weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                            width=32, height=16, border_radius=4,
                            bgcolor=pos_clr,
                            alignment=ft.Alignment(0, 0),
                        ),
                    ],
                ),
                # Center: Name + info
                ft.Column(
                    spacing=2, expand=True,
                    controls=[
                        ft.Row(spacing=4, tight=True, controls=[
                            ft.Text(name, size=theme.BODY_SIZE, weight=ft.FontWeight.W_600,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            *name_badges,
                        ]),
                        ft.Row(spacing=8, tight=True, controls=[
                            ft.Text(f"Age {age}", size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY),
                            ft.Text(f"Form {form:.1f}", size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY),
                        ]),
                    ],
                ),
                # Right: Fitness + Morale + Training
                ft.Row(spacing=6, tight=True, controls=[
                    ft.Container(
                        content=ft.Text(f"{fitness}", size=theme.CAPTION_SIZE,
                                        weight=ft.FontWeight.BOLD, color=fit_clr),
                        width=30, alignment=ft.Alignment(1, 0),
                    ),
                    ft.Text(morale_emoji, size=14),
                    *([ ft.Text(train_label, size=12) ] if train_label else []),
                ]),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=theme.CARD_RADIUS_SM,
        bgcolor=theme.CARD_BG_HIGHLIGHT if highlight else theme.CARD_GLASS,
        border=ft.border.only(
            left=ft.BorderSide(3, pos_clr),
            top=ft.BorderSide(1, theme.GOLD_BORDER),
            right=ft.BorderSide(1, theme.GOLD_BORDER),
            bottom=ft.BorderSide(1, theme.GOLD_BORDER),
        ),
        on_click=on_click,
        ink=True,
    )


# ── Player Card Compact ────────────────────────────────────────────────────

def player_card_compact(
    name: str,
    position: str,
    ovr: int,
    age: int,
    value_str: str = "",
    club_name: str = "",
    badges_list: list[str] | None = None,
    on_click=None,
) -> ft.Container:
    """
    Compact player card for transfer search / shortlist (~56px).
    """
    pass
    pos_clr = theme.position_color(position)
    ovr_clr = theme.ovr_color(ovr)

    badges_text = " ".join(badges_list) if badges_list else ""

    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(spacing=8, tight=True, expand=True, controls=[
                    ft.Container(
                        content=ft.Text(position, size=9, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                        width=30, height=18, border_radius=4,
                        bgcolor=pos_clr, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(spacing=0, expand=True, controls=[
                        ft.Row(spacing=4, tight=True, controls=[
                            ft.Text(name, size=12, weight=ft.FontWeight.W_500,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            *([ ft.Text(badges_text, size=9) ] if badges_text else []),
                        ]),
                        ft.Row(spacing=8, tight=True, controls=[
                            ft.Text(f"Age {age}", size=10, color=theme.TEXT_SECONDARY),
                            ft.Text(str(ovr), size=10, weight=ft.FontWeight.BOLD, color=ovr_clr),
                            *([ ft.Text(club_name, size=10, color=theme.TEXT_MUTED) ] if club_name else []),
                        ]),
                    ]),
                ]),
                *([ ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END,
                              controls=[
                        ft.Text(value_str, size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                                color=theme.ACCENT),
                        ft.Text("EGP", size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
                    ]) ] if value_str else []),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=7),
        border_radius=theme.CARD_RADIUS_SM,
        bgcolor=theme.CARD_GLASS,
        border=ft.border.all(1, theme.GOLD_BORDER),
        on_click=on_click,
        ink=True,
    )


# ── Position Group Header ──────────────────────────────────────────────────

def position_group_header(group_name: str, count: int) -> ft.Container:
    """Section header for player position groups (GK, DEF, MID, FWD)."""
    pass
    group_colors = {
        "GK": theme.POS_GK, "DEF": theme.POS_DEF, "MID": theme.POS_MID, "FWD": theme.POS_FWD,
    }
    clr = group_colors.get(group_name, theme.TEXT_MUTED)

    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=6, tight=True, controls=[
                    ft.Container(width=3, height=14, bgcolor=clr, border_radius=2),
                    ft.Text(group_name, size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                            color=clr),
                ]),
                ft.Text(f"{count}", size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )



