"""
Pre-Match screen — review and edit starting XI before playing.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.core.tactics import auto_select_xi, get_formation_positions
from src.core.player import calculate_overall_rating
from src.core.calendar import simulate_user_match
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.theme import (
    pitch_width as pw_fn, pitch_height as ph_fn, PAGE_PADDING,
    header_bar, GOLD_BORDER, CARD_GLASS, PRIMARY_BTN_STYLE,
)
from src.utils.config import Position
from src.utils.localization import t


# Pitch coordinates for position markers
_POS_COORDS: dict[Position, tuple[float, float]] = {
    Position.GK:  (50, 90),
    Position.CB:  (50, 72),
    Position.LB:  (15, 68),
    Position.RB:  (85, 68),
    Position.CDM: (50, 55),
    Position.CM:  (50, 45),
    Position.CAM: (50, 32),
    Position.LM:  (12, 45),
    Position.RM:  (88, 45),
    Position.LW:  (18, 25),
    Position.RW:  (82, 25),
    Position.ST:  (50, 15),
}
_SPREAD_GAP = 17


def build_pre_match_screen(page: ft.Page) -> ft.Column:
    """Build the pre-match starting XI selection screen."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = build_nav_bar(page, 2)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    squad = queries.get_players_by_club(conn, club.id)
    fixture = queries.get_user_next_fixture(conn, gs.user_club_id)
    if not fixture:
        return ft.Column(controls=[ft.Text("No upcoming match")])

    is_home = fixture.home_club_id == gs.user_club_id
    opp_name = fixture.away_club_name if is_home else fixture.home_club_name

    # Count unavailable players
    injured_players = [p for p in squad if p.injury_days_remaining > 0]
    suspended_players = [p for p in squad if p.suspension_matches > 0]

    # Auto-select starting XI
    xi_ids, bench_ids = auto_select_xi(squad, club.formation)
    player_map = {p.id: p for p in squad}

    # Mutable state for swaps
    current_xi = list(xi_ids)
    current_bench = list(bench_ids)

    # Swap logic
    selected_starter_idx = [None]  # index into current_xi
    selected_bench_idx = [None]    # index into current_bench

    # Responsive pitch dimensions
    _pw = pw_fn(page)
    _ph = int(_pw * 0.875)  # slightly shorter for pre-match view

    def _rebuild_ui():
        """Rebuild the pitch and bench display."""
        pitch_stack.controls.clear()
        bench_col.controls.clear()

        # Pitch background
        pitch_stack.controls.append(
            ft.Container(
                width=_pw, height=_ph,
                border_radius=10,
                gradient=ft.LinearGradient(
                    colors=["#1B5E20", "#2E7D32", "#1B5E20", "#2E7D32", "#1B5E20"],
                    begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
                ),
                border=ft.border.all(2, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
                shadow=ft.BoxShadow(
                    spread_radius=0, blur_radius=10,
                    color=ft.Colors.with_opacity(0.12, ft.Colors.GREEN),
                ),
            )
        )

        # Place player markers
        positions = get_formation_positions(club.formation)

        # Pre-count positions for symmetric spreading
        total_pos_count: dict[Position, int] = {}
        for pos in positions:
            total_pos_count[pos] = total_pos_count.get(pos, 0) + 1
        pos_index: dict[Position, int] = {}

        for i, pid in enumerate(current_xi):
            if i >= len(positions):
                break
            pos = positions[i]
            p = player_map.get(pid)
            if not p:
                continue

            idx = pos_index.get(pos, 0)
            pos_index[pos] = idx + 1
            count = total_pos_count[pos]

            base_x, base_y = _POS_COORDS.get(pos, (50, 50))
            # Symmetric spreading
            if count > 1:
                offset = (idx - (count - 1) / 2) * _SPREAD_GAP
                x = max(8, min(92, base_x + offset))
            else:
                x = base_x

            ovr = calculate_overall_rating(p)
            fit_ok = p.fitness >= 70
            is_selected = selected_starter_idx[0] == i

            border = ft.border.all(2, ft.Colors.AMBER_400) if is_selected else None

            def make_starter_click(idx=i):
                def handler(e):
                    if selected_bench_idx[0] is not None:
                        # Swap starter with bench
                        bi = selected_bench_idx[0]
                        current_xi[idx], current_bench[bi] = current_bench[bi], current_xi[idx]
                        selected_bench_idx[0] = None
                        selected_starter_idx[0] = None
                        _rebuild_ui()
                        page.update()
                    else:
                        selected_starter_idx[0] = idx
                        selected_bench_idx[0] = None
                        _rebuild_ui()
                        page.update()
                return handler

            marker = ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    controls=[
                        ft.Container(
                            content=ft.Text(str(ovr), size=10, weight=ft.FontWeight.BOLD,
                                             color=ft.Colors.WHITE),
                            width=28, height=28, border_radius=14,
                            bgcolor=ft.Colors.GREEN_700 if fit_ok else ft.Colors.RED_700,
                            alignment=ft.Alignment(0, 0),
                            border=border,
                        ),
                        ft.Text(p.name.split()[-1][:8], size=8,
                                 color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                    ],
                ),
                left=x / 100 * _pw - 20,
                top=base_y / 100 * _ph - 20,
                on_click=make_starter_click(),
            )
            pitch_stack.controls.append(marker)

        # Build bench row
        for bi, pid in enumerate(current_bench):
            p = player_map.get(pid)
            if not p:
                continue
            ovr = calculate_overall_rating(p)
            is_selected = selected_bench_idx[0] == bi

            def make_bench_click(idx=bi):
                def handler(e):
                    if selected_starter_idx[0] is not None:
                        # Swap bench with starter
                        si = selected_starter_idx[0]
                        current_xi[si], current_bench[idx] = current_bench[idx], current_xi[si]
                        selected_starter_idx[0] = None
                        selected_bench_idx[0] = None
                        _rebuild_ui()
                        page.update()
                    else:
                        selected_bench_idx[0] = idx
                        selected_starter_idx[0] = None
                        _rebuild_ui()
                        page.update()
                return handler

            bench_label_parts = [p.name]
            if p.injury_days_remaining > 0:
                bench_label_parts.append("🏥")
            if p.suspension_matches > 0:
                bench_label_parts.append("🚫")
            bench_display = " ".join(bench_label_parts)

            bench_col.controls.append(
                ft.Container(
                    content=ft.Row(
                        spacing=6,
                        controls=[
                            ft.Container(
                                content=ft.Text(str(ovr), size=10,
                                                 weight=ft.FontWeight.BOLD,
                                                 color=ft.Colors.WHITE),
                                width=26, height=26, border_radius=13,
                                bgcolor=ft.Colors.GREY_700,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Text(bench_display, size=11, expand=True),
                            ft.Text(p.position.value, size=10, color=ft.Colors.AMBER_300),
                            ft.Text(f"{p.fitness}%", size=10,
                                     color=ft.Colors.GREEN_400 if p.fitness >= 70 else ft.Colors.RED_400),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=8),
                    border_radius=8,
                    bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER) if is_selected else CARD_GLASS,
                    border=ft.border.all(1, ft.Colors.AMBER_400 if is_selected else GOLD_BORDER),
                    on_click=make_bench_click(),
                    ink=True,
                )
            )

    # Mutable containers
    pitch_stack = ft.Stack(width=_pw, height=_ph)
    bench_col = ft.Column(spacing=2)

    _rebuild_ui()

    # Play match button
    def play_match(e):
        # Simulate the full match
        outcome = simulate_user_match(conn, gs)
        if outcome:
            # Navigate to live match screen for FIFA-style replay
            from src.ui.screens.live_match import build_live_match_screen
            page.navigation_bar = None
            page.controls.clear()
            live_content = build_live_match_screen(page, outcome)
            safe = ft.SafeArea(
                content=live_content,
                avoid_intrusions_top=True,
                avoid_intrusions_bottom=True,
                avoid_intrusions_left=True,
                avoid_intrusions_right=True,
                minimum_padding=ft.Padding(top=4, bottom=0, left=0, right=0),
            )
            page.controls.append(safe)
            page.update()
        else:
            show_snackbar(page, "Could not simulate match!", bgcolor=ft.Colors.RED_800)

    venue = "🏟️ HOME" if is_home else "✈️ AWAY"

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        header_bar(
                            title="Starting XI",
                            subtitle=f"vs {opp_name} {venue}  •  {club.formation}",
                            icon=ft.Icons.FORMAT_LIST_NUMBERED,
                            page=page,
                            back_route="/match_day",
                        ),
                        # Unavailable warning
                        *(
                            [ft.Container(
                                content=ft.Column(spacing=2, controls=[
                                    *(
                                        [ft.Text(
                                            f"🏥 {len(injured_players)} injured: " +
                                            ", ".join(p.name for p in injured_players[:3]) +
                                            ("..." if len(injured_players) > 3 else ""),
                                            size=10, color=ft.Colors.RED_400,
                                        )] if injured_players else []
                                    ),
                                    *(
                                        [ft.Text(
                                            f"🚫 {len(suspended_players)} suspended: " +
                                            ", ".join(p.name for p in suspended_players[:3]) +
                                            ("..." if len(suspended_players) > 3 else ""),
                                            size=10, color=ft.Colors.ORANGE_400,
                                        )] if suspended_players else []
                                    ),
                                ]),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=6,
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED),
                            )] if (injured_players or suspended_players) else []
                        ),
                        ft.Text("Tap a starter, then tap a bench player to swap",
                                 size=10, color=ft.Colors.GREY_600, italic=True),
                        ft.Divider(height=1),
                        # Pitch
                        pitch_stack,
                        ft.Divider(height=1),
                        # Bench
                        ft.Text("🪑 Bench", size=14, weight=ft.FontWeight.W_500),
                        bench_col,
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            "⚽ Confirm & Play",
                            width=280, height=56,
                            style=PRIMARY_BTN_STYLE,
                            on_click=play_match,
                        ),
                        ft.Container(height=10),
                    ],
                ),
            ),
        ],
    )

