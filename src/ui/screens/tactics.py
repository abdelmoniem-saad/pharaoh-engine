"""
Tactics screen — formation selector, mentality, visual pitch, and presets.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.core.tactics import get_available_formations, PRESETS
from src.utils.config import Mentality, Position, FORMATION_TEMPLATES
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.cards import collapsible_section
from src.utils.localization import t, t_format


# Position display coordinates on a pitch (x%, y%) from top-left
# x: 0=left edge, 100=right edge  |  y: 0=goal line (top), 100=own goal (bottom)
_POSITION_COORDS: dict[Position, tuple[float, float]] = {
    Position.GK:  (50, 92),
    Position.CB:  (50, 75),
    Position.LB:  (15, 70),
    Position.RB:  (85, 70),
    Position.CDM: (50, 58),
    Position.CM:  (50, 48),
    Position.CAM: (50, 35),
    Position.LM:  (12, 48),
    Position.RM:  (88, 48),
    Position.LW:  (18, 28),
    Position.RW:  (82, 28),
    Position.ST:  (50, 18),
}

# Horizontal gap between duplicate positions (in % of pitch width)
_SPREAD_GAP = 17


def build_tactics_screen(page: ft.Page) -> ft.Column:
    """Build the tactical setup content."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = build_nav_bar(page, 1)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text(t("no_game_loaded"))])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text(t("club_not_found_msg"))])

    formations = get_available_formations()
    mentality_options = [
        ft.dropdown.Option(m.name.replace("_", " ").title()) for m in Mentality
    ]

    def on_formation_change(e):
        club_obj = queries.get_club(conn, gs.user_club_id)
        if club_obj:
            club_obj.formation = e.control.value
            queries.update_club(conn, club_obj)
            navigate(page, "/tactics")
            show_snackbar(page, t_format("formation_set", f=e.control.value))

    def on_mentality_change(e):
        club_obj = queries.get_club(conn, gs.user_club_id)
        if club_obj:
            key = e.control.value.upper().replace(" ", "_")
            try:
                club_obj.mentality = Mentality[key]
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")
                show_snackbar(page, t_format("mentality_set", m=e.control.value))
            except KeyError:
                pass

    def make_preset_handler(preset_key):
        def handler(e):
            preset = PRESETS[preset_key]
            club_obj = queries.get_club(conn, gs.user_club_id)
            if club_obj:
                club_obj.formation = preset.formation
                club_obj.mentality = preset.mentality
                club_obj.pressing_intensity = preset.pressing_intensity
                club_obj.tempo = preset.tempo
                club_obj.width = preset.width
                club_obj.defensive_line = preset.defensive_line
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")
                show_snackbar(page, t_format("preset_applied", p=preset.name))
        return handler

    # Visual pitch
    pitch = _build_formation_pitch(club.formation, page)

    # ── Slider change handlers ────────────────────────────────────────
    def _make_slider_handler(attr_name, label):
        def handler(e):
            club_obj = queries.get_club(conn, gs.user_club_id)
            if club_obj:
                setattr(club_obj, attr_name, int(e.control.value))
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")
                show_snackbar(page, f"{label} set to {int(e.control.value)}")
        return handler

    def _slider_row(label, value, attr_name, low_label="Low", high_label="High"):
        return ft.Column(spacing=2, controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, size=12, weight=ft.FontWeight.W_500),
                    ft.Text(str(value), size=12, color=theme.ACCENT,
                            weight=ft.FontWeight.BOLD),
                ],
            ),
            ft.Row(spacing=4, controls=[
                ft.Text(low_label, size=9, color=ft.Colors.GREY_500),
                ft.Slider(
                    min=1, max=10, divisions=9, value=value,
                    on_change=_make_slider_handler(attr_name, label),
                    expand=True,
                    active_color=theme.ACCENT,
                ),
                ft.Text(high_label, size=9, color=ft.Colors.GREY_500),
            ]),
        ])

    # Mentality indicator
    mentality_color = {
        Mentality.ULTRA_DEFENSIVE: ft.Colors.BLUE_400,
        Mentality.DEFENSIVE: ft.Colors.LIGHT_BLUE_400,
        Mentality.CAUTIOUS: ft.Colors.CYAN_400,
        Mentality.BALANCED: ft.Colors.GREEN_400,
        Mentality.POSITIVE: ft.Colors.YELLOW_400,
        Mentality.ATTACKING: ft.Colors.ORANGE_400,
        Mentality.ULTRA_ATTACKING: ft.Colors.RED_400,
    }.get(club.mentality, ft.Colors.GREEN_400)

    # Preset cards
    preset_cards = []
    for key, preset in PRESETS.items():
        is_active = (preset.formation == club.formation and
                     preset.mentality == club.mentality)
        # Use t() for preset name and description
        preset_name = t(key) if t(key) != f"[{key}]" else preset.name
        preset_desc = t(f"{key}_desc") if t(f"{key}_desc") != f"[{key}_desc]" else preset.description
        preset_cards.append(
            ft.Card(
                content=ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.PLAY_ARROW,
                            color=ft.Colors.GREEN_400 if is_active else ft.Colors.GREY_500,
                        ),
                        title=ft.Text(preset_name, weight=ft.FontWeight.W_500,
                                      size=13),
                        subtitle=ft.Text(
                            f"{preset.formation} | {preset_desc[:50]}",
                            size=10, color=ft.Colors.GREY_400,
                        ),
                        on_click=make_preset_handler(key),
                    ),
                    padding=ft.padding.symmetric(vertical=0),
                    bgcolor=theme.CARD_GLASS_STRONG if is_active else ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.GREEN) if is_active else theme.GOLD_BORDER),
                    border_radius=10,
                ),
            )
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    spacing=10,
                    controls=[
                        theme.header_bar(
                            title=t("tactics"),
                            subtitle=(
                                f"{gs.user_club_name} — {club.formation} | "
                                f"{club.mentality.name.replace('_', ' ').title()}"
                            ),
                            icon=ft.Icons.TUNE,
                            page=page,
                        ),
                        # Dropdowns
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Dropdown(
                                    label=t("formation"),
                                    value=club.formation,
                                    options=[ft.dropdown.Option(f) for f in formations],
                                    on_select=on_formation_change,
                                    expand=True,
                                ),
                                ft.Dropdown(
                                    label=t("mentality"),
                                    value=club.mentality.name.replace("_", " ").title(),
                                    options=mentality_options,
                                    on_select=on_mentality_change,
                                    expand=True,
                                ),
                            ],
                        ),
                        # Pitch
                        ft.Text(t("formation"), size=14, weight=ft.FontWeight.W_500),
                        pitch,

                        # Tactical Sliders (collapsible, expanded by default)
                        collapsible_section(
                            f"🎛️ {t('tactical_sliders')}",
                            [
                                _slider_row(t("pressing_intensity"), club.pressing_intensity,
                                            "pressing_intensity", t("passive"), t("aggressive")),
                                _slider_row(t("tempo"), club.tempo,
                                            "tempo", t("slow"), t("fast")),
                                _slider_row(t("width"), club.width,
                                            "width", t("narrow"), t("wide")),
                                _slider_row(t("defensive_line"), club.defensive_line,
                                            "defensive_line", t("deep"), t("high")),
                            ],
                            initially_expanded=True,
                            title_color=ft.Colors.CYAN_400,
                        ),

                        # Quick Presets (collapsed by default)
                        collapsible_section(
                            "⚡ Quick Presets",
                            preset_cards,
                            initially_expanded=False,
                            title_color=theme.ACCENT,
                            subtitle=t("tap_to_apply_preset"),
                        ),
                    ],
                ),
            ),
        ],
    )


def _build_formation_pitch(formation: str, page: ft.Page = None) -> ft.Container:
    """Build a visual pitch showing player positions for the given formation."""
    pass
    pw = theme.pitch_width(page) if page else 280
    ph = theme.pitch_height(page) if page else 360

    positions = FORMATION_TEMPLATES.get(formation, FORMATION_TEMPLATES["4-2-3-1"])

    # Count occurrences of each position to spread duplicates symmetrically
    pos_count: dict[Position, int] = {}
    for pos in positions:
        pos_count[pos] = pos_count.get(pos, 0) + 1

    # Track which index we're at for each position
    pos_index: dict[Position, int] = {}

    # Create position markers
    markers = []
    for pos in positions:
        idx = pos_index.get(pos, 0)
        pos_index[pos] = idx + 1
        count = pos_count[pos]

        base_x, base_y = _POSITION_COORDS.get(pos, (50, 50))

        if count > 1:
            offset = (idx - (count - 1) / 2) * _SPREAD_GAP
            x = base_x + offset
        else:
            x = base_x
        y = base_y

        # Clamp to pitch bounds
        x = max(8, min(92, x))
        y = max(5, min(95, y))

        # Marker style
        is_gk = pos == Position.GK
        marker_color = theme.ACCENT if is_gk else ft.Colors.WHITE
        marker_bg = ft.Colors.with_opacity(0.9, theme.ACCENT_DARK if is_gk else ft.Colors.BLUE_GREY_700)
        marker_size = 32

        markers.append(
            ft.Container(
                content=ft.Text(pos.value, size=9, weight=ft.FontWeight.BOLD,
                                color=marker_color, text_align=ft.TextAlign.CENTER),
                width=marker_size, height=marker_size,
                border_radius=marker_size // 2,
                bgcolor=marker_bg,
                alignment=ft.Alignment(0, 0),
                border=ft.border.all(2, ft.Colors.with_opacity(0.5, theme.ACCENT)),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=6,
                    color=ft.Colors.with_opacity(0.25, theme.ACCENT if is_gk else ft.Colors.WHITE),
                ),
                left=x / 100 * pw - marker_size // 2,
                top=y / 100 * ph - marker_size // 2,
            )
        )

    # Center circle size
    cc_size = max(40, int(pw * 0.2))

    # Pitch background with lines
    pitch = ft.Stack(
        controls=[
            # Pitch background with grass gradient
            ft.Container(
                width=pw, height=ph,
                gradient=ft.LinearGradient(
                    colors=["#1B5E20", "#2E7D32", "#1B5E20", "#2E7D32", "#1B5E20"],
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                ),
                border_radius=10,
                border=ft.border.all(2, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=12,
                    color=ft.Colors.with_opacity(0.15, ft.Colors.GREEN),
                ),
            ),
            # Center line
            ft.Container(
                width=pw, height=1,
                bgcolor=ft.Colors.with_opacity(0.35, ft.Colors.WHITE),
                left=0, top=ph // 2,
            ),
            # Center circle
            ft.Container(
                width=cc_size, height=cc_size,
                border_radius=cc_size // 2,
                border=ft.border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                left=(pw - cc_size) // 2, top=(ph - cc_size) // 2,
            ),
            # Penalty area top
            ft.Container(
                width=int(pw * 0.5), height=int(ph * 0.14),
                border=ft.border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                left=int(pw * 0.25), top=0,
            ),
            # Penalty area bottom
            ft.Container(
                width=int(pw * 0.5), height=int(ph * 0.14),
                border=ft.border.all(1, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                left=int(pw * 0.25), top=ph - int(ph * 0.14),
            ),
            # Player markers
            *markers,
        ],
        width=pw,
        height=ph,
    )

    return ft.Container(
        content=pitch,
        alignment=ft.Alignment(0, 0),
        padding=5,
    )
