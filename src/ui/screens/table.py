"""
League Table screen — standings display with card-based mobile layout.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.cards import section_card, info_tile, action_card
from src.utils.localization import t, t_format


def build_table_screen(page: ft.Page) -> ft.Column:
    """Build the competition content (League or Cup)."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 3)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text(t("no_game_loaded"))])

    conn = app_state.db_conn
    gs = app_state.game_state
    
    # Simple state management for switching views
    active_view = getattr(page, "_comp_view", "league")

    def switch_view(view_name: str):
        page._comp_view = view_name
        # Force redraw by re-navigating (same route)
        navigate(page, "/table")

    # ── Comparison Toggle ───────────────────────────────────────────
    toggle = ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
            controls=[
                ft.TextButton(
                    t("egyptian_premier_league").upper() if len(t("egyptian_premier_league")) < 15 else "LEAGUE",
                    style=ft.ButtonStyle(
                        color=theme.ACCENT if active_view == "league" else theme.TEXT_SECONDARY,
                        bgcolor=ft.Colors.with_opacity(0.1, theme.ACCENT) if active_view == "league" else ft.Colors.TRANSPARENT,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: switch_view("league"),
                ),
                ft.Icon(ft.Icons.SWAP_HORIZ, size=16, color=theme.TEXT_MUTED),
                ft.TextButton(
                    t("egypt_cup").upper(),
                    style=ft.ButtonStyle(
                        color=theme.ACCENT if active_view == "cup" else theme.TEXT_SECONDARY,
                        bgcolor=ft.Colors.with_opacity(0.1, theme.ACCENT) if active_view == "cup" else ft.Colors.TRANSPARENT,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda _: switch_view("cup"),
                ),
            ],
        ),
        margin=ft.margin.only(bottom=10),
    )

    if active_view == "cup":
        content_view = _build_cup_view(page, conn, gs)
    else:
        content_view = _build_league_view(page, conn, gs)

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.all(theme.PAGE_PADDING),
                content=ft.Column(
                    spacing=theme.SECTION_SPACING,
                    controls=[
                        # Header
                        theme.header_bar(
                            title=t("competition"),
                            subtitle=f"{t_format('season_label', y1=gs.season_year, y2=gs.season_year + 1)}",
                            icon=ft.Icons.LEADERBOARD,
                            page=page,
                        ),
                        toggle,
                        content_view,
                    ],
                ),
            ),
        ],
    )


def _build_league_view(page: ft.Page, conn, gs) -> ft.Column:
    """Build the standard league table view."""
    from src.ui.app import navigate
    standings = queries.get_standings(conn)
    current_md = queries.get_current_matchday(conn)

    # Find user position
    user_pos = 0
    user_standing = None
    for i, s in enumerate(standings, 1):
        if s.club_id == gs.user_club_id:
            user_pos = i
            user_standing = s
            break

    # ── Table Header Row ────────────────────────────────────────────
    header_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text("#", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text(t("team"), size=theme.TINY_SIZE, color=theme.TEXT_MUTED, expand=True),
                ft.Text("P", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("W", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("D", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("L", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=22,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("GD", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=28,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("Pts", size=theme.TINY_SIZE, color=theme.TEXT_MUTED, width=28,
                        text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        bgcolor=theme.CARD_GLASS,
        border_radius=theme.CARD_RADIUS_SM,
    )

    # ── Table Rows ──────────────────────────────────────────────────
    table_rows = []
    for pos, s in enumerate(standings, 1):
        is_user = s.club_id == gs.user_club_id

        # Zone coloring
        if is_user:
            bg = theme.CARD_BG_HIGHLIGHT
            left_border = ft.border.only(
                left=ft.BorderSide(3, theme.TEXT_SUCCESS),
            )
        elif pos <= 2:
            bg = ft.Colors.with_opacity(0.08, ft.Colors.BLUE)
            left_border = ft.border.only(left=ft.BorderSide(3, ft.Colors.BLUE_400))
        elif pos == 3:
            bg = ft.Colors.with_opacity(0.08, ft.Colors.ORANGE)
            left_border = ft.border.only(left=ft.BorderSide(3, ft.Colors.ORANGE_400))
        elif pos >= len(standings) - 2:
            bg = ft.Colors.with_opacity(0.08, ft.Colors.RED)
            left_border = ft.border.only(left=ft.BorderSide(3, ft.Colors.RED_400))
        else:
            bg = theme.CARD_GLASS
            left_border = ft.border.all(1, theme.GOLD_BORDER)

        name_weight = ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL
        pts_color = theme.ACCENT if is_user else theme.TEXT_PRIMARY

        gd_val = s.goal_difference
        gd_color = theme.TEXT_SUCCESS if gd_val > 0 else theme.TEXT_DANGER if gd_val < 0 else theme.TEXT_MUTED

        from src.utils.localization import get_language, display_name
        club_display = display_name(s.club_name, getattr(s, "club_name_ar", ""))

        table_rows.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Text(str(pos), size=theme.CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD if is_user else ft.FontWeight.NORMAL,
                                color=theme.ACCENT if is_user else theme.TEXT_SECONDARY),
                        ft.Text(club_display[:16], size=12, expand=True,
                                weight=name_weight,
                                color=theme.TEXT_SUCCESS if is_user else theme.TEXT_PRIMARY,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(str(s.played), size=theme.CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=theme.TEXT_SECONDARY),
                        ft.Text(str(s.won), size=theme.CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=theme.TEXT_SUCCESS),
                        ft.Text(str(s.drawn), size=theme.CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=theme.TEXT_WARNING),
                        ft.Text(str(s.lost), size=theme.CAPTION_SIZE, width=22,
                                text_align=ft.TextAlign.CENTER, color=theme.TEXT_DANGER),
                        ft.Text(f"{gd_val:+d}", size=theme.CAPTION_SIZE, width=28,
                                text_align=ft.TextAlign.CENTER, color=gd_color),
                        ft.Text(str(s.points), size=theme.BODY_SIZE, width=28,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD, color=pts_color),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                border_radius=theme.CARD_RADIUS_SM,
                bgcolor=bg,
                border=left_border,
            )
        )

    # ── User Position Callout ───────────────────────────────────────
    pos_suffix = {1: "st", 2: "nd", 3: "rd"}.get(user_pos, "th")
    user_pts_text = ""
    if user_standing:
        user_pts_text = (
            f"{user_standing.points} pts  •  W{user_standing.won} D{user_standing.drawn} L{user_standing.lost}  •  "
            f"GD {user_standing.goal_difference:+d}"
        )

    return ft.Column(
        spacing=theme.SECTION_SPACING,
        controls=[
            ft.Text(f"{t('standings')} — {t('matchday')} {current_md}", size=14, color=theme.TEXT_SECONDARY),
            
            # User position callout
            *([ ft.Container(
                content=ft.Column(spacing=2, controls=[
                    ft.Text(f"📍 {t_format('you_are_pos', pos=f'{user_pos}{pos_suffix}')}", size=theme.BODY_SIZE,
                            weight=ft.FontWeight.W_600, color=theme.TEXT_SUCCESS),
                    ft.Text(user_pts_text, size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY),
                ]),
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                bgcolor=theme.CARD_GLASS_STRONG,
                border_radius=theme.CARD_RADIUS_SM,
                border=ft.border.only(
                    left=ft.BorderSide(3, theme.TEXT_SUCCESS),
                    top=ft.BorderSide(1, theme.GOLD_BORDER),
                    right=ft.BorderSide(1, theme.GOLD_BORDER),
                    bottom=ft.BorderSide(1, theme.GOLD_BORDER),
                ),
            )] if user_pos else []),

            # Table
            header_row,
            ft.Column(spacing=2, controls=table_rows),
            
            # Quick nav
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                ft.OutlinedButton(f"📅 {t('fixtures_btn')}", on_click=lambda e: navigate(page, "/fixtures"),
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, theme.GOLD_BORDER))),
            ]),
        ]
    )


def _build_cup_view(page: ft.Page, conn, gs) -> ft.Column:
    """Build the Egypt Cup overview/bracket view."""
    from src.ui.app import navigate
    from src.core.competition import get_cup_state, CUP_ROUNDS
    from src.utils.localization import get_language
    
    cup = get_cup_state(conn, gs.season_year)
    if not cup:
        return ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
            ft.Container(height=40),
            ft.Icon(ft.Icons.LOCK, size=48, color=theme.TEXT_MUTED),
            ft.Text(t("no_data"), color=theme.TEXT_MUTED),
        ])

    lang = get_language()
    round_cards = []
    
    for rnd_name in CUP_ROUNDS:
        if rnd_name not in cup.rounds:
            continue
            
        rnd = cup.rounds[rnd_name]
        is_current = cup.current_round == rnd_name
        
        matches_summary = []
        for fid in rnd.fixture_ids:
            row = conn.execute("SELECT * FROM fixtures WHERE id=?", (fid,)).fetchone()
            if not row: continue
            
            # Manual localization for sqlite row
            if lang == "ar" and row["home_club_name_ar"]:
                h_name = row["home_club_name_ar"]
            else:
                h_name = row["home_club_name"]
                
            if lang == "ar" and row["away_club_name_ar"]:
                a_name = row["away_club_name_ar"]
            else:
                a_name = row["away_club_name"]
                
            played = bool(row["played"])
            
            if played:
                score = f"{row['home_goals']} - {row['away_goals']}"
                if row['penalties_json']:
                    score += " (P)"
                score_color = theme.TEXT_PRIMARY
            else:
                score = "vs"
                score_color = theme.TEXT_MUTED
                
            is_user_match = row["home_club_id"] == gs.user_club_id or row["away_club_id"] == gs.user_club_id
            
            matches_summary.append(
                ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(h_name[:14], size=11, color=theme.TEXT_PRIMARY, expand=True, max_lines=1),
                            ft.Container(
                                content=ft.Text(score, size=10, weight=ft.FontWeight.BOLD, color=score_color),
                                bgcolor=theme.CARD_GLASS, padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                border_radius=4,
                            ),
                            ft.Text(a_name[:14], size=11, color=theme.TEXT_PRIMARY, expand=True, text_align=ft.TextAlign.RIGHT, max_lines=1),
                        ],
                    ),
                    padding=4,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.15, theme.ACCENT)) if is_user_match else None,
                    bgcolor=ft.Colors.with_opacity(0.08, theme.ACCENT) if is_user_match else None,
                    border_radius=4,
                )
            )

        # Localization for round name
        rnd_display = t(rnd_name.lower().replace(" ", "_"))
        if rnd_display == f"[{rnd_name.lower().replace(' ', '_')}]":
            rnd_display = rnd_name # fallback

        status_text = "Complete" if rnd.is_complete else ("In Progress" if is_current else "Upcoming")
        status_color = theme.TEXT_SUCCESS if rnd.is_complete else (theme.ACCENT if is_current else theme.TEXT_MUTED)

        card = section_card(
            title=rnd_display,
            controls=[
                ft.Row([ft.Text(status_text, size=10, color=status_color, weight=ft.FontWeight.W_500)]),
                ft.Column(spacing=4, controls=matches_summary),
            ]
        )
        round_cards.append(card)

    if cup.champion_id:
        # Get champion name from club_names dict (which stores names)
        champ_name = cup.club_names.get(cup.champion_id, "Unknown")
        round_cards.insert(0, action_card(
            title="🏆 " + t("champion").upper(),
            subtitle=f"{champ_name} won the Egypt Cup!",
            on_click=None
        ))

    return ft.Column(
        spacing=theme.SECTION_SPACING,
        controls=[
            *round_cards,
            # Quick nav
            ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[
                ft.OutlinedButton(f"📅 {t('fixtures_btn')}", on_click=lambda e: navigate(page, "/fixtures"),
                                  style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), side=ft.BorderSide(1, theme.GOLD_BORDER))),
            ]),
        ]
    )
