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
        ft.Icon(icon, rtl=theme.rtl(), size=52, color=theme.TEXT_MUTED),
        ft.Container(rtl=theme.rtl(), height=10),
        ft.Text(title, rtl=theme.rtl(), size=theme.BODY_SIZE, weight=ft.FontWeight.W_600,
                color=theme.TEXT_SECONDARY, text_align=ft.TextAlign.CENTER),
    ]
    if subtitle:
        controls.append(ft.Container(rtl=theme.rtl(), height=4))
        controls.append(ft.Text(subtitle, rtl=theme.rtl(), size=theme.CAPTION_SIZE,
                                color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER))
    return ft.Container(
        rtl=theme.rtl(), content=ft.Column(
            rtl=theme.rtl(), horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
        header_controls.append(ft.Icon(icon, rtl=theme.rtl(), size=16, color=title_color))
    header_controls.append(
        ft.Text(title.lstrip("📊📋🏟️💰📈⚽🏆💡🎯🎛️⚡🏥🚫 "), rtl=theme.rtl(), size=16, weight=ft.FontWeight.W_600, color=title_color, expand=True)
    )
    if extra_action:
        header_controls.append(extra_action)

    return ft.Container(
        rtl=theme.rtl(), content=ft.Column(
            rtl=theme.rtl(), spacing=theme.ITEM_SPACING,
            controls=[
                ft.Row(rtl=theme.rtl(), controls=header_controls, spacing=6),
                *(controls if not collapsed else []),
            ],
        ),
        padding=theme.CARD_PADDING,
        border_radius=theme.CARD_RADIUS,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.only(
            left=ft.BorderSide(1, theme.GOLD_BORDER),
            top=ft.BorderSide(1, theme.GOLD_BORDER),
            right=ft.BorderSide(1, theme.GOLD_BORDER),
            bottom=ft.BorderSide(1, theme.GOLD_BORDER),
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
        leading = ft.Icon(icon, rtl=theme.rtl(), size=16, color=title_color)

    return ft.Container(
        rtl=theme.rtl(), content=ft.ExpansionTile(
            rtl=theme.rtl(), title=ft.Text(title.lstrip("📊📋🏟️💰📈⚽🏆💡🎯🎛️⚡🏥🚫 "), rtl=theme.rtl(), size=16, weight=ft.FontWeight.W_600,
                          color=title_color),
            subtitle=ft.Text(subtitle, rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED) if subtitle else None,
            leading=leading,
            controls=controls,
            expanded=initially_expanded,
            maintain_state=True,
            controls_padding=ft.padding.only(left=8, right=8, bottom=8),
            tile_padding=ft.padding.symmetric(horizontal=16, vertical=10),
            icon_color=title_color,
            collapsed_icon_color=theme.TEXT_MUTED,
            text_color=title_color,
            collapsed_text_color=theme.TEXT_SECONDARY,
            bgcolor=ft.Colors.TRANSPARENT,
            collapsed_bgcolor=ft.Colors.TRANSPARENT,
            dense=False,
        ),
        border_radius=theme.CARD_RADIUS,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.only(
            left=ft.BorderSide(1, theme.GOLD_BORDER),
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
        rtl=theme.rtl(), spacing=4, tight=True,
        controls=[
            *([ ft.Icon(icon, rtl=theme.rtl(), size=13, color=theme.ACCENT) ] if icon else []),
            ft.Column(rtl=theme.rtl(), spacing=0, controls=[
                ft.Text(label, rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
                ft.Text(value, rtl=theme.rtl(), size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD, color=color),
            ]),
        ],
    )
    return ft.Container(
        rtl=theme.rtl(), content=inner,
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
        rtl=theme.rtl(), content=ft.Row(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text(label, rtl=theme.rtl(), size=theme.BODY_SIZE, color=theme.TEXT_SECONDARY),
                ft.Text(value, rtl=theme.rtl(), size=theme.BODY_SIZE,
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
        rtl=theme.rtl(), content=ft.Text(text, rtl=theme.rtl(), size=size, color=color, weight=ft.FontWeight.BOLD),
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
            rtl=theme.rtl(), content=ft.Text(r, rtl=theme.rtl(), size=10, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
            width=22, height=22, border_radius=11,
            bgcolor=color_map.get(r, theme.TEXT_MUTED),
            alignment=ft.Alignment(0, 0),
        )
        for r in results
    ]
    return ft.Row(rtl=theme.rtl(), spacing=3, controls=chips if chips else [
        ft.Text("—", rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED)
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
        rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=2, controls=[
            ft.Row(rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text(home_val, rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
                ft.Text(label, rtl=theme.rtl(), size=10, color=theme.TEXT_MUTED),
                ft.Text(away_val, rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
            ]),
            ft.Row(rtl=theme.rtl(), spacing=2, controls=[
                ft.Container(
                    rtl=theme.rtl(), expand=home_flex, height=4,
                    bgcolor=home_color, border_radius=2,
                ),
                ft.Container(
                    rtl=theme.rtl(), expand=away_flex, height=4,
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
        rtl=theme.rtl(), content=ft.Row(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(rtl=theme.rtl(), spacing=10, tight=True, controls=[
                    ft.Icon(icon, rtl=theme.rtl(), size=20, color=color),
                    ft.Column(rtl=theme.rtl(), spacing=0, controls=[
                        ft.Text(title, rtl=theme.rtl(), size=theme.BODY_SIZE, weight=ft.FontWeight.W_600),
                        *([ ft.Text(subtitle, rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY) ]
                          if subtitle else []),
                    ]),
                ]),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, rtl=theme.rtl(), size=18, color=theme.ACCENT),
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
    """A responsive match fixture with original typographic club monograms."""
    from src.utils.localization import is_rtl
    def club(name, managed):
        initials = "".join(word[0] for word in name.split()[:2])
        return ft.Column(rtl=theme.rtl(), expand=True, spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(rtl=theme.rtl(), width=60, height=68, border_radius=12,
                    bgcolor=theme.ACCENT_BG if managed else theme.BG_SURFACE,
                    border=ft.border.all(1, theme.GOLD_BORDER),
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(initials, rtl=theme.rtl(), size=22, weight=ft.FontWeight.W_700,
                                    color=theme.ACCENT if managed else theme.TEXT_SECONDARY)),
                ft.Text(name, rtl=theme.rtl(), size=14, weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER, max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(("ناديك" if is_rtl() else "YOUR CLUB") if managed else
                        ("المنافس" if is_rtl() else "OPPOSITION"),
                        rtl=theme.rtl(), size=10, color=theme.TEXT_MUTED),
            ])
    played = home_goals != ""
    return ft.Card(rtl=theme.rtl(), elevation=0, margin=0, content=ft.Container(
        rtl=theme.rtl(), padding=24, border_radius=theme.CARD_RADIUS,
        bgcolor=theme.CARD_GLASS_STRONG,
        border=ft.border.all(1, theme.GOLD_BORDER),
        content=ft.Column(rtl=theme.rtl(), spacing=24, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Column(rtl=theme.rtl(), spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(competition.upper(), rtl=theme.rtl(), size=11, weight=ft.FontWeight.W_600,
                        color=theme.ACCENT, text_align=ft.TextAlign.CENTER),
                ft.Text(matchday, rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
            ]),
            ft.Row(rtl=theme.rtl(), spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                club(home_name, is_home),
                ft.Text(theme.scoreline(home_goals, away_goals) if played else t("versus_short"),
                        rtl=False, size=40 if played else 16, font_family=theme.display_font(), weight=ft.FontWeight.W_700,
                        color=theme.TEXT_PRIMARY if played else theme.TEXT_MUTED),
                club(away_name, not is_home),
            ]),
            *([ft.Container(rtl=theme.rtl(), height=1, bgcolor=theme.GOLD_BORDER),
               ft.Text(date_str, rtl=theme.rtl(), size=12, color=theme.TEXT_SECONDARY,
                       text_align=ft.TextAlign.CENTER)] if date_str else []),
        ])))


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
    """Readable roster row with aligned rating and condition columns."""
    status = []
    for active, icon, label, color in [
        (is_injured, ft.Icons.LOCAL_HOSPITAL_OUTLINED, t("injured_label"), theme.TEXT_DANGER),
        (is_suspended, ft.Icons.BLOCK, t("suspended_label"), theme.TEXT_WARNING),
        (transfer_listed, ft.Icons.SWAP_HORIZ, t("transfers"), theme.TEXT_INFO),
    ]:
        if active:
            status.append(ft.Icon(icon, rtl=theme.rtl(), size=15, color=color, tooltip=label))
    if is_captain:
        status.append(ft.Text("C", rtl=theme.rtl(), size=11, color=theme.ACCENT, tooltip=t("captain")))
    return ft.Container(
        rtl=theme.rtl(), padding=ft.padding.symmetric(horizontal=14, vertical=16),
        bgcolor=theme.CARD_BG_HIGHLIGHT if highlight else theme.CARD_GLASS,
        border=ft.border.only(bottom=ft.BorderSide(1, theme.GOLD_BORDER)),
        on_click=on_click, ink=True,
        tooltip=f"{t('morale')}: {morale}" + (f" · {training_focus}" if training_focus else ""),
        content=ft.Row(rtl=theme.rtl(), spacing=12, controls=[
            ft.Container(rtl=theme.rtl(), width=40, height=42, border_radius=8,
                bgcolor=theme.BG_SURFACE, alignment=ft.Alignment(0, 0),
                content=ft.Text(position, rtl=theme.rtl(), size=11, weight=ft.FontWeight.W_700,
                                color=theme.position_color(position))),
            ft.Column(rtl=theme.rtl(), expand=True, spacing=6, controls=[
                ft.Row(rtl=theme.rtl(), spacing=5, controls=[
                    ft.Text(name, rtl=theme.rtl(), size=14, weight=ft.FontWeight.W_600, expand=True,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS), *status]),
                ft.Text(f"{t('age')} {age}  ·  {t('form')} {form:.1f}",
                        rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
            ]),
            ft.Column(rtl=theme.rtl(), width=36, spacing=5, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Text(str(ovr), rtl=theme.rtl(), font_family=theme.display_font(), size=24, weight=ft.FontWeight.W_600, color=theme.TEXT_PRIMARY),
                ft.Text(t("overall"), rtl=theme.rtl(), size=9, color=theme.TEXT_MUTED, max_lines=1),
            ]),
            ft.Column(rtl=theme.rtl(), width=42, spacing=8, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[
                ft.Text(f"{fitness}%", rtl=theme.rtl(), size=12, color=theme.fitness_color(fitness)),
                ft.ProgressBar(rtl=theme.rtl(), value=fitness / 100, width=36, height=3,
                               color=theme.fitness_color(fitness), bgcolor=theme.GOLD_BORDER),
            ]),
        ]))


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
        rtl=theme.rtl(), content=ft.Row(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(rtl=theme.rtl(), spacing=8, tight=True, expand=True, controls=[
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Text(position, rtl=theme.rtl(), size=9, weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                        width=30, height=18, border_radius=4,
                        bgcolor=pos_clr, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(rtl=theme.rtl(), spacing=0, expand=True, controls=[
                        ft.Row(rtl=theme.rtl(), spacing=4, tight=True, controls=[
                            ft.Text(name, rtl=theme.rtl(), size=12, weight=ft.FontWeight.W_500,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            *([ ft.Text(badges_text, rtl=theme.rtl(), size=9) ] if badges_text else []),
                        ]),
                        ft.Row(rtl=theme.rtl(), spacing=8, tight=True, controls=[
                            ft.Text(f"Age {age}", rtl=theme.rtl(), size=10, color=theme.TEXT_SECONDARY),
                            ft.Text(str(ovr), rtl=theme.rtl(), size=10, weight=ft.FontWeight.BOLD, color=ovr_clr),
                            *([ ft.Text(club_name, rtl=theme.rtl(), size=10, color=theme.TEXT_MUTED) ] if club_name else []),
                        ]),
                    ]),
                ]),
                *([ ft.Column(rtl=theme.rtl(), spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END,
                              controls=[
                        ft.Text(value_str, rtl=theme.rtl(), size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                                color=theme.ACCENT),
                        ft.Text("EGP", rtl=theme.rtl(), size=theme.TINY_SIZE, color=theme.TEXT_MUTED),
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
        rtl=theme.rtl(), content=ft.Row(
            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(rtl=theme.rtl(), spacing=6, tight=True, controls=[
                    ft.Container(rtl=theme.rtl(), width=3, height=14, bgcolor=clr, border_radius=2),
                    ft.Text(group_name, rtl=theme.rtl(), size=theme.CAPTION_SIZE, weight=ft.FontWeight.BOLD,
                            color=clr),
                ]),
                ft.Text(f"{count}", rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED),
            ],
        ),
        padding=ft.padding.only(left=2, right=2, top=20, bottom=10),
    )



