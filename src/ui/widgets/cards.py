"""
Shared card widgets — mobile-first reusable UI components.

Every screen should compose these primitives instead of building
raw ft.Container / ft.Row layouts inline.
"""
from __future__ import annotations

import flet as ft
from src.ui.theme import (
    ACCENT, ACCENT_DARK, ACCENT_BG,
    CARD_BG, CARD_BG_HIGHLIGHT, CARD_BG_DANGER,
    CARD_RADIUS, CARD_RADIUS_SM, CARD_PADDING, CARD_PADDING_SM,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    TEXT_SUCCESS, TEXT_WARNING, TEXT_DANGER,
    SECTION_SPACING, ITEM_SPACING,
    BODY_SIZE, CAPTION_SIZE, TINY_SIZE,
)


# ── Section Card ────────────────────────────────────────────────────────────

def section_card(
    title: str,
    controls: list,
    icon: str | None = None,
    title_color: str = ACCENT,
    collapsed: bool = False,
    extra_action: ft.Control | None = None,
) -> ft.Container:
    """
    A titled card section — the fundamental building block.

    Usage:
        section_card("⚽ Goals", [goal_row_1, goal_row_2])
    """
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
            spacing=ITEM_SPACING,
            controls=[
                ft.Row(controls=header_controls, spacing=6),
                *(controls if not collapsed else []),
            ],
        ),
        padding=CARD_PADDING,
        border_radius=CARD_RADIUS,
        bgcolor=CARD_BG,
        border=ft.border.only(left=ft.BorderSide(3, title_color)),
    )


# ── Info Tile ───────────────────────────────────────────────────────────────

def info_tile(
    label: str,
    value: str,
    icon=None,
    color: str = TEXT_PRIMARY,
    width: int | None = None,
) -> ft.Container:
    """
    Small rounded info block — replaces _info_chip, _summary_chip, _card_row.

    Displays icon + label + value in a compact pill.
    """
    inner = ft.Row(
        spacing=4, tight=True,
        controls=[
            *([ ft.Icon(icon, size=13, color=ACCENT) ] if icon else []),
            ft.Column(spacing=0, controls=[
                ft.Text(label, size=TINY_SIZE, color=TEXT_MUTED),
                ft.Text(value, size=CAPTION_SIZE, weight=ft.FontWeight.BOLD, color=color),
            ]),
        ],
    )
    return ft.Container(
        content=inner,
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border_radius=CARD_RADIUS_SM,
        bgcolor=CARD_BG,
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
                ft.Text(label, size=BODY_SIZE, color=TEXT_SECONDARY),
                ft.Text(value, size=BODY_SIZE,
                        weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL,
                        color=color or TEXT_PRIMARY),
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
    color_map = {"W": TEXT_SUCCESS, "D": TEXT_WARNING, "L": TEXT_DANGER}
    chips = [
        ft.Container(
            content=ft.Text(r, size=10, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            width=22, height=22, border_radius=11,
            bgcolor=color_map.get(r, TEXT_MUTED),
            alignment=ft.Alignment(0, 0),
        )
        for r in results
    ]
    return ft.Row(spacing=3, controls=chips if chips else [
        ft.Text("—", size=CAPTION_SIZE, color=TEXT_MUTED)
    ])


# ── Stat Comparison Bar ────────────────────────────────────────────────────

def stat_comparison_bar(
    home_val: str, away_val: str, label: str,
    bar_width: int = 260,
    home_color: str = ft.Colors.GREEN_400,
    away_color: str = ft.Colors.BLUE_400,
) -> ft.Container:
    """Visual stat comparison bar — for post-match / match preview."""
    try:
        hv = float(home_val.replace('%', ''))
        av = float(away_val.replace('%', ''))
    except ValueError:
        hv = av = 0
    total = hv + av if (hv + av) > 0 else 1
    home_pct = hv / total

    return ft.Container(
        content=ft.Column(spacing=2, controls=[
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text(home_val, size=12, weight=ft.FontWeight.BOLD),
                ft.Text(label, size=10, color=TEXT_MUTED),
                ft.Text(away_val, size=12, weight=ft.FontWeight.BOLD),
            ]),
            ft.Row(spacing=2, controls=[
                ft.Container(
                    width=max(4, home_pct * bar_width), height=4,
                    bgcolor=home_color, border_radius=2,
                ),
                ft.Container(
                    width=max(4, (1 - home_pct) * bar_width), height=4,
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
    color: str = ACCENT,
) -> ft.Container:
    """
    Full-width tappable navigation card — for "Go to Transfers", "View Table", etc.
    """
    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, tight=True, controls=[
                    ft.Icon(icon, size=20, color=color),
                    ft.Column(spacing=0, controls=[
                        ft.Text(title, size=BODY_SIZE, weight=ft.FontWeight.W_600),
                        *([ ft.Text(subtitle, size=CAPTION_SIZE, color=TEXT_SECONDARY) ]
                          if subtitle else []),
                    ]),
                ]),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, size=18, color=TEXT_MUTED),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
        border_radius=CARD_RADIUS,
        bgcolor=CARD_BG,
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
    home_icon_color = TEXT_SUCCESS if is_home else TEXT_MUTED
    away_icon_color = TEXT_SUCCESS if not is_home else TEXT_MUTED

    score = f"{home_goals} - {away_goals}" if home_goals != "" else "VS"
    score_color = ACCENT if home_goals == "" else TEXT_PRIMARY

    return ft.Card(
        content=ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=16),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    *([ ft.Text(competition, size=CAPTION_SIZE, color=ACCENT,
                                weight=ft.FontWeight.W_500) ] if competition else []),
                    *([ ft.Text(matchday, size=TINY_SIZE, color=TEXT_MUTED) ] if matchday else []),
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
                    *([ ft.Text(date_str, size=TINY_SIZE, color=TEXT_MUTED) ] if date_str else []),
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
    from src.ui.theme import position_color, ovr_color, fitness_color

    pos_clr = position_color(position)
    ovr_clr = ovr_color(ovr)
    fit_clr = fitness_color(fitness)

    # Name with badges
    name_badges = []
    if is_captain:
        name_badges.append(badge("C", bgcolor=ACCENT_DARK, size=8))
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
                            ft.Text(name, size=BODY_SIZE, weight=ft.FontWeight.W_600,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            *name_badges,
                        ]),
                        ft.Row(spacing=8, tight=True, controls=[
                            ft.Text(f"Age {age}", size=CAPTION_SIZE, color=TEXT_SECONDARY),
                            ft.Text(f"Form {form:.1f}", size=CAPTION_SIZE, color=TEXT_SECONDARY),
                        ]),
                    ],
                ),
                # Right: Fitness + Morale + Training
                ft.Row(spacing=6, tight=True, controls=[
                    ft.Container(
                        content=ft.Text(f"{fitness}", size=CAPTION_SIZE,
                                        weight=ft.FontWeight.BOLD, color=fit_clr),
                        width=30, alignment=ft.Alignment(1, 0),
                    ),
                    ft.Text(morale_emoji, size=14),
                    *([ ft.Text(train_label, size=12) ] if train_label else []),
                ]),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        border_radius=CARD_RADIUS_SM,
        bgcolor=CARD_BG_HIGHLIGHT if highlight else CARD_BG,
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
    from src.ui.theme import position_color, ovr_color
    pos_clr = position_color(position)
    ovr_clr = ovr_color(ovr)

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
                            ft.Text(f"Age {age}", size=10, color=TEXT_SECONDARY),
                            ft.Text(str(ovr), size=10, weight=ft.FontWeight.BOLD, color=ovr_clr),
                            *([ ft.Text(club_name, size=10, color=TEXT_MUTED) ] if club_name else []),
                        ]),
                    ]),
                ]),
                *([ ft.Column(spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END,
                              controls=[
                        ft.Text(value_str, size=CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                                color=ACCENT),
                        ft.Text("EGP", size=TINY_SIZE, color=TEXT_MUTED),
                    ]) ] if value_str else []),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=7),
        border_radius=CARD_RADIUS_SM,
        bgcolor=CARD_BG,
        on_click=on_click,
        ink=True,
    )


# ── Position Group Header ──────────────────────────────────────────────────

def position_group_header(group_name: str, count: int) -> ft.Container:
    """Section header for player position groups (GK, DEF, MID, FWD)."""
    from src.ui.theme import POS_GK, POS_DEF, POS_MID, POS_FWD
    group_colors = {
        "GK": POS_GK, "DEF": POS_DEF, "MID": POS_MID, "FWD": POS_FWD,
    }
    clr = group_colors.get(group_name, TEXT_MUTED)

    return ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=6, tight=True, controls=[
                    ft.Container(width=3, height=14, bgcolor=clr, border_radius=2),
                    ft.Text(group_name, size=CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                            color=clr),
                ]),
                ft.Text(f"{count}", size=CAPTION_SIZE, color=TEXT_MUTED),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )



