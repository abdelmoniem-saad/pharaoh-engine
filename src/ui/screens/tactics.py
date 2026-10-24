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
from src.utils.localization import t, t_format, display_name


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
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("no_game_loaded"), rtl=theme.rtl())])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("club_not_found_msg"), rtl=theme.rtl())])

    formations = get_available_formations()
    mentality_options = [
        ft.dropdown.Option(m.name, text=t(m.name.lower())) for m in Mentality
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
    pitch = _build_formation_pitch(club.formation, page, queries.get_players_by_club(conn, club.id))

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
        return ft.Column(rtl=theme.rtl(), spacing=2, controls=[
            ft.Row(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(label, rtl=theme.rtl(), size=14, weight=ft.FontWeight.W_500),
                    ft.Text(str(value), rtl=theme.rtl(), size=12, color=theme.ACCENT,
                            weight=ft.FontWeight.BOLD),
                ],
            ),
            ft.Row(rtl=theme.rtl(), spacing=4, controls=[
                ft.Text(low_label, rtl=theme.rtl(), size=11, color=theme.TEXT_MUTED),
                ft.Slider(
                    rtl=theme.rtl(), min=1, max=10, divisions=9, value=value,
                    on_change_end=_make_slider_handler(attr_name, label),
                    expand=True,
                    active_color=theme.ACCENT,
                ),
                ft.Text(high_label, rtl=theme.rtl(), size=11, color=theme.TEXT_MUTED),
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
                     preset.mentality == club.mentality and
                     all(getattr(preset, field) == getattr(club, field) for field in
                         ("pressing_intensity", "tempo", "width", "defensive_line")))
        # Use t() for preset name and description
        preset_name = t(key) if t(key) != f"[{key}]" else preset.name
        preset_desc = t(f"{key}_desc") if t(f"{key}_desc") != f"[{key}_desc]" else preset.description
        preset_cards.append(
            ft.Card(
                rtl=theme.rtl(), content=ft.Container(
                    rtl=theme.rtl(), content=ft.ListTile(
                        rtl=theme.rtl(), leading=ft.Icon(
                            ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.PLAY_ARROW,
                            rtl=theme.rtl(), color=ft.Colors.GREEN_400 if is_active else ft.Colors.GREY_500,
                        ),
                        title=ft.Text(preset_name, rtl=theme.rtl(), weight=ft.FontWeight.W_500,
                                      size=13),
                        subtitle=ft.Text(
                            f"{preset.formation} · {preset_desc}",
                            rtl=theme.rtl(), size=12, color=theme.TEXT_SECONDARY,
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
        rtl=theme.rtl(), expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                rtl=theme.rtl(), padding=theme.PAGE_PADDING,
                content=ft.Column(
                    rtl=theme.rtl(), spacing=22,
                    controls=[
                        theme.header_bar(
                            title=t("tactics"),
                            subtitle=(
                                display_name(club) + " · " + t("tactical_identity")
                            ),
                            icon=ft.Icons.TUNE,
                            page=page,
                        ),
                        # Dropdowns
                        ft.Row(
                            rtl=theme.rtl(), spacing=22,
                            controls=[
                                ft.Dropdown(
                                    border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=t("formation"),
                                    value=club.formation,
                                    options=[ft.dropdown.Option(f) for f in formations],
                                    on_select=on_formation_change,
                                    expand=True,
                                ),
                                ft.Dropdown(
                                    border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=t("mentality"),
                                    value=club.mentality.name,
                                    options=mentality_options,
                                    on_select=on_mentality_change,
                                    expand=True,
                                ),
                            ],
                        ),
                        # Pitch
                        ft.Text(t("projected_lineup"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
                        pitch,

                        # Tactical Sliders (collapsible, expanded by default)
                        collapsible_section(
                            t("tactical_sliders"),
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
                            t("quick_presets"),
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


def _build_formation_pitch(formation: str, page: ft.Page = None, squad=None) -> ft.Container:
    """Projected XI. Final team selection remains in the pre-match screen."""
    from src.core.tactics import auto_select_xi
    from src.core.player import calculate_overall_rating
    pw = theme.pitch_width(page) if page else 280
    ph = int(pw * 1.27)
    positions = FORMATION_TEMPLATES.get(formation, FORMATION_TEMPLATES["4-2-3-1"])
    selected = []
    if squad:
        xi, _ = auto_select_xi(squad, formation)
        lookup = {p.id: p for p in squad}
        selected = [lookup.get(pid) for pid in xi]
    counts = {pos: positions.count(pos) for pos in positions}
    seen = {}
    lines = "#47635F"
    markers = []
    for i, pos in enumerate(positions):
        idx = seen.get(pos, 0)
        seen[pos] = idx + 1
        x, y = _POSITION_COORDS.get(pos, (50, 50))
        x += (idx - (counts[pos] - 1) / 2) * _SPREAD_GAP
        x, y = max(12, min(88, x)), max(10, min(88, y))
        player = selected[i] if i < len(selected) else None
        label = display_name(player).split()[-1] if player else pos.value
        def details(e, p=player):
            if p and page:
                from src.ui.screens.squad import _show_player_detail
                _show_player_detail(page, p, calculate_overall_rating(p))
        markers.append(ft.Container(rtl=theme.rtl(), left=x / 100 * pw - 34, top=y / 100 * ph - 24,
            width=68, on_click=details if player else None,
            tooltip=display_name(player) if player else pos.value,
            content=ft.Column(rtl=theme.rtl(), spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                ft.Container(rtl=theme.rtl(), width=32, height=32, border_radius=9,
                    bgcolor=theme.ACCENT if pos == Position.GK else "#F1F3ED",
                    alignment=ft.Alignment(0, 0),
                    content=ft.Text(str(player.shirt_number or i+1) if player else pos.value,
                                    rtl=theme.rtl(), size=13, color="#142921", weight=ft.FontWeight.BOLD)),
                ft.Container(rtl=theme.rtl(), padding=ft.padding.symmetric(horizontal=4, vertical=2),
                    bgcolor="#122A26", border_radius=3,
                    content=ft.Text(label, rtl=theme.rtl(), size=10, color="#FFFFFF", max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS)),
            ])))
    cc = pw * .22
    return ft.Container(rtl=theme.rtl(), alignment=ft.Alignment(0, 0), content=ft.Container(
        rtl=theme.rtl(), padding=12, border_radius=16, bgcolor="#142E2A",
        content=ft.Stack(rtl=theme.rtl(), width=pw, height=ph, controls=[
            ft.Container(rtl=theme.rtl(), left=0, top=0, width=pw, height=ph,
                         border=ft.border.all(1, lines), border_radius=4),
            *[ft.Container(rtl=theme.rtl(), left=0, top=ph*i/8, width=pw, height=ph/8,
                           bgcolor="#14332D") for i in (0,2,4,6)],
            ft.Container(rtl=theme.rtl(), left=0, top=ph/2, width=pw, height=1, bgcolor=lines),
            ft.Container(rtl=theme.rtl(), left=(pw-cc)/2, top=(ph-cc)/2, width=cc, height=cc,
                         border_radius=cc/2, border=ft.border.all(1, lines)),
            *[ft.Container(rtl=theme.rtl(), left=pw*.22, top=y, width=pw*.56, height=ph*.15,
                           border=ft.border.all(1, lines)) for y in (0,ph*.85)],
            *markers,
        ])))
