"""
Tactics screen — formation selector, mentality, visual pitch, and presets.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.tactics import get_available_formations, PRESETS
from src.utils.config import Mentality, Position, FORMATION_TEMPLATES
from src.ui.widgets.nav_bar import build_nav_bar


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
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

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
            show_snackbar(page, f"Formation set to {e.control.value}")

    def on_mentality_change(e):
        club_obj = queries.get_club(conn, gs.user_club_id)
        if club_obj:
            key = e.control.value.upper().replace(" ", "_")
            try:
                club_obj.mentality = Mentality[key]
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")
                show_snackbar(page, f"Mentality set to {e.control.value}")
            except KeyError:
                pass

    def make_preset_handler(preset_key):
        def handler(e):
            preset = PRESETS[preset_key]
            club_obj = queries.get_club(conn, gs.user_club_id)
            if club_obj:
                club_obj.formation = preset.formation
                club_obj.mentality = preset.mentality
                queries.update_club(conn, club_obj)
                navigate(page, "/tactics")
                show_snackbar(page, f"Preset applied: {preset.name}")
        return handler

    # Visual pitch
    pitch = _build_formation_pitch(club.formation)

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
        preset_cards.append(
            ft.Card(
                content=ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(
                            ft.Icons.CHECK_CIRCLE if is_active else ft.Icons.PLAY_ARROW,
                            color=ft.Colors.GREEN_400 if is_active else ft.Colors.GREY_500,
                        ),
                        title=ft.Text(preset.name, weight=ft.FontWeight.W_500,
                                      size=13),
                        subtitle=ft.Text(
                            f"{preset.formation} | {preset.description[:50]}",
                            size=10, color=ft.Colors.GREY_400,
                        ),
                        on_click=make_preset_handler(key),
                    ),
                    padding=ft.padding.symmetric(vertical=0),
                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREEN) if is_active else None,
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
                        ft.Text("⚙️ Tactics", size=22, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            f"{gs.user_club_name} — {club.formation} | "
                            f"{club.mentality.name.replace('_', ' ').title()}",
                            size=13, color=ft.Colors.GREY_400,
                        ),
                        ft.Divider(height=1),
                        # Dropdowns
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Dropdown(
                                    label="Formation",
                                    value=club.formation,
                                    options=[ft.dropdown.Option(f) for f in formations],
                                    on_select=on_formation_change,
                                    width=160,
                                ),
                                ft.Dropdown(
                                    label="Mentality",
                                    value=club.mentality.name.replace("_", " ").title(),
                                    options=mentality_options,
                                    on_select=on_mentality_change,
                                    width=160,
                                ),
                            ],
                        ),
                        # Mentality bar
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Text("Mentality: ", size=11, color=ft.Colors.GREY_500),
                                    ft.Container(
                                        width=int(club.mentality) / 7 * 200,
                                        height=6, bgcolor=mentality_color,
                                        border_radius=3,
                                    ),
                                ],
                            ),
                        ),
                        # Pitch
                        ft.Text("Formation View", size=14, weight=ft.FontWeight.W_500),
                        pitch,
                        ft.Divider(height=1),
                        # Presets
                        ft.Text("⚡ Quick Presets", size=14, weight=ft.FontWeight.W_500),
                        *preset_cards,
                    ],
                ),
            ),
        ],
    )


def _build_formation_pitch(formation: str) -> ft.Container:
    """Build a visual pitch showing player positions for the given formation."""
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

        # Symmetric spreading: distribute N markers evenly around base_x
        # For count=1: offset=0  For count=2: offsets=[-gap/2, +gap/2]
        # For count=3: offsets=[-gap, 0, +gap]  etc.
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
        marker_color = ft.Colors.AMBER_400 if is_gk else ft.Colors.WHITE
        marker_bg = ft.Colors.with_opacity(0.9, ft.Colors.AMBER_800 if is_gk else ft.Colors.BLUE_GREY_700)

        markers.append(
            ft.Container(
                content=ft.Text(pos.value, size=9, weight=ft.FontWeight.BOLD,
                                color=marker_color, text_align=ft.TextAlign.CENTER),
                width=32, height=32,
                border_radius=16,
                bgcolor=marker_bg,
                alignment=ft.Alignment(0, 0),
                left=x / 100 * 280 - 16,  # center the 32px marker
                top=y / 100 * 360 - 16,
            )
        )

    # Pitch background with lines
    pitch = ft.Stack(
        controls=[
            # Pitch background
            ft.Container(
                width=280, height=360,
                bgcolor=ft.Colors.GREEN_900,
                border_radius=8,
                border=ft.border.all(2, ft.Colors.WHITE24),
            ),
            # Center line
            ft.Container(
                width=280, height=1, bgcolor=ft.Colors.WHITE24,
                left=0, top=180,
            ),
            # Center circle (approximation)
            ft.Container(
                width=60, height=60,
                border_radius=30,
                border=ft.border.all(1, ft.Colors.WHITE24),
                left=110, top=150,
            ),
            # Penalty area top
            ft.Container(
                width=140, height=50,
                border=ft.border.all(1, ft.Colors.WHITE24),
                left=70, top=0,
            ),
            # Penalty area bottom
            ft.Container(
                width=140, height=50,
                border=ft.border.all(1, ft.Colors.WHITE24),
                left=70, top=310,
            ),
            # Player markers
            *markers,
        ],
        width=280,
        height=360,
    )

    return ft.Container(
        content=pitch,
        alignment=ft.Alignment(0, 0),
        padding=5,
    )
