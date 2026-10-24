"""
Transfer Market screen — search, scout, buy, sell, and loan players.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.data.models import InboxMessage
from src.core.transfers import estimate_player_value, can_sign_player
from src.core.player import calculate_overall_rating
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.widgets.stat_bar import stat_bar
from src.utils.config import Position
from src.utils.localization import t, t_format, display_name


def build_transfers_screen(page: ft.Page) -> ft.Column:
    """Build the transfer market screen."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = build_nav_bar(page, 0)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("no_game_loaded"), rtl=theme.rtl())])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("club_not_found_msg"), rtl=theme.rtl())])

    # ── Shortlist (in-memory for session) ────────────────────────────
    if not hasattr(app_state, "_shortlist"):
        app_state._shortlist = set()
    shortlist: set = app_state._shortlist

    # ── Search controls ──────────────────────────────────────────────
    name_field = ft.TextField(border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=t("name"), expand=True, text_size=13,
                               hint_text=t("search_by_name"))
    pos_dd = ft.Dropdown(
        border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=t("position"), width=112,
        options=[ft.dropdown.Option(key="", text=t("any"))] + [ft.dropdown.Option(p.value) for p in Position],
        value="",
    )
    max_age_field = ft.TextField(border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=f"{t('age')} ≤", width=80, value="35", text_size=13)
    min_ovr_field = ft.TextField(border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label=f"{t('overall')} ≥", width=80, value="", text_size=13)

    results_list = ft.Column(rtl=theme.rtl(), spacing=4)

    def _player_row(p, value, club_name, is_shortlisted=False, show_star=True):
        """Build a compact player row for search results."""
        from src.data import queries as _q
        ovr = calculate_overall_rating(p)
        scouted = _q.is_player_scouted(conn, p.id)

        # Unscouted targets are only known by rough scouting range — the
        # number you see could be off by up to 5 in either direction.
        if scouted:
            ovr_display = str(ovr)
            ovr_color = ft.Colors.GREEN_300 if ovr >= 70 else ft.Colors.WHITE
        else:
            # Unscouted reports give a rough BAND, deliberately off-centre:
            # averaging the two numbers must NOT reveal the true ability.
            _lean = (((p.id * 73) % 8) + 1) * (1 if p.id % 2 else -1)  # ±1..4
            _half = 5 + ((p.id >> 3) % 3)      # band width 10–14, varies too
            lo = max(35, ovr - _half + _lean)
            hi = min(99, ovr + _half + _lean)
            if ovr < lo:                       # clamps must never hide truth
                lo = ovr
            elif ovr > hi:
                hi = ovr
            ovr_display = f"🔍 {lo}–{hi}"
            ovr_color = ft.Colors.GREY_300

        age_color = ft.Colors.GREEN_400 if p.age <= 23 else ft.Colors.GREY_400

        badges = []
        if p.injury_days_remaining > 0:
            badges.append("🏥")
        if p.transfer_listed:
            badges.append("📤")
        badge_text = " ".join(badges)

        def make_handler(player=p, val=value):
            def handler(e):
                _show_buy_dialog(page, conn, gs, club, player, val, shortlist)
            return handler

        star_icon = ft.Icons.STAR if is_shortlisted else ft.Icons.STAR_BORDER

        SCOUT_FEE = 25_000

        def send_scout(e, pid=p.id):
            buyer = queries.get_club(conn, gs.user_club_id)
            if not buyer or buyer.finances.balance < SCOUT_FEE:
                show_snackbar(page, "❌ Not enough balance to send a scout.",
                              bgcolor=ft.Colors.RED_800)
                return
            buyer.finances.balance -= SCOUT_FEE
            queries.update_club(conn, buyer)
            queries.mark_player_scouted(conn, pid, gs.current_date)
            show_snackbar(page, f"🔍 Scout report filed on {p.name} (-{SCOUT_FEE:,} EGP)")
            navigate(page, "/transfers")

        def toggle_shortlist(e, pid=p.id):
            if pid in shortlist:
                shortlist.discard(pid)
            else:
                shortlist.add(pid)
            navigate(page, "/transfers")

        return ft.Container(
            rtl=theme.rtl(), content=ft.Row(
                rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        rtl=theme.rtl(), spacing=0, expand=True,
                        controls=[
                            ft.Row(rtl=theme.rtl(), spacing=4, tight=True, controls=[
                                ft.Text(display_name(p), rtl=theme.rtl(), size=14, weight=ft.FontWeight.W_600, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(badge_text, rtl=theme.rtl(), size=10) if badge_text else ft.Container(rtl=theme.rtl()),
                            ]),
                            ft.Row(rtl=theme.rtl(), spacing=8, wrap=True, controls=[
                                ft.Text(p.position.value, rtl=theme.rtl(), size=10, color=theme.GOLD),
                                ft.Text(f"{t('age')} {p.age}", rtl=theme.rtl(), size=10, color=age_color),
                                ft.Text(ovr_display, rtl=theme.rtl(), size=10,
                                        weight=ft.FontWeight.BOLD, color=ovr_color),
                                ft.Text(club_name, rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                            ]),
                        ],
                    ),
                    ft.Row(rtl=theme.rtl(), spacing=4, tight=True, controls=[
                        ft.Column(rtl=theme.rtl(), spacing=0, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[
                            ft.Text(f"{value:,}", rtl=theme.rtl(), size=11, weight=ft.FontWeight.BOLD, color=theme.GOLD),
                            ft.Text("EGP", rtl=theme.rtl(), size=11, color=ft.Colors.GREY_600),
                        ]),
                        ft.IconButton(
                            rtl=theme.rtl(), icon=star_icon, icon_size=16,
                            icon_color=theme.ACCENT if is_shortlisted else ft.Colors.GREY_600,
                            on_click=toggle_shortlist, tooltip=t("shortlist"),
                        ) if show_star else ft.Container(rtl=theme.rtl()),
                        ft.IconButton(
                            rtl=theme.rtl(), icon=ft.Icons.TRAVEL_EXPLORE, icon_size=16,
                            icon_color=ft.Colors.BLUE_300,
                            tooltip=f"Send scout ({25_000:,} EGP)",
                            on_click=send_scout,
                        ) if not scouted else ft.Container(rtl=theme.rtl()),
                    ]),
                ],
            ),
            padding=ft.padding.symmetric(horizontal=14, vertical=16),
            border_radius=theme.CARD_RADIUS_SM,
            bgcolor=theme.CARD_GLASS,
            border=ft.border.all(1, theme.GOLD_BORDER),
            on_click=make_handler(),
            ink=True,
        )

    # ── Auto-load top players on first visit ─────────────────────────
    def _auto_load_results():
        """Pre-populate results with top available players."""
        players = queries.search_players(
            conn, exclude_club_id=gs.user_club_id, limit=20,
        )
        results_list.controls.clear()
        if not players:
            results_list.controls.append(
                ft.Text(t("no_players_available"), rtl=theme.rtl(), size=13, color=ft.Colors.GREY_500))
        else:
            results_list.controls.append(
                ft.Text(f"{len(players)} {t('available')}", rtl=theme.rtl(), size=11,
                         color=ft.Colors.GREY_500))
            for p in players:
                value = estimate_player_value(p, current_date=gs.current_date)
                p_club = queries.get_club(conn, p.club_id) if p.club_id else None
                club_name = p_club.short_name if p_club else "Free Agent"
                results_list.controls.append(
                    _player_row(p, value, club_name, p.id in shortlist))

    _auto_load_results()

    def do_search(e):
        pos = pos_dd.value or ""
        try:
            max_age = int(max_age_field.value) if max_age_field.value else 99
        except ValueError:
            max_age = 99
        try:
            min_ovr = int(min_ovr_field.value) if min_ovr_field.value else 0
        except ValueError:
            min_ovr = 0
        name = name_field.value or ""

        players = queries.search_players(
            conn, name=name, position=pos, max_age=max_age,
            min_ability=min_ovr, exclude_club_id=gs.user_club_id, limit=30,
        )
        results_list.controls.clear()

        if not players:
            from src.ui.widgets.cards import empty_state
            results_list.controls.append(
                empty_state(ft.Icons.SEARCH_OFF, t("no_players_found")))
        else:
            results_list.controls.append(
                ft.Text(f"{len(players)} {t('available')}", rtl=theme.rtl(), size=11, color=ft.Colors.GREY_500))
            for p in players:
                value = estimate_player_value(p, current_date=gs.current_date)
                p_club = queries.get_club(conn, p.club_id) if p.club_id else None
                club_name = p_club.short_name if p_club else "Free Agent"
                results_list.controls.append(
                    _player_row(p, value, club_name, p.id in shortlist))
        page.update()

    # ── Shortlist tab ────────────────────────────────────────────────
    def _build_shortlist_content():
        items = []
        if not shortlist:
            from src.ui.widgets.cards import empty_state
            items.append(empty_state(ft.Icons.PLAYLIST_ADD,
                                     t("no_players_shortlisted")))
        else:
            for pid in list(shortlist):
                # Look up player from DB
                try:
                    row = conn.execute("SELECT * FROM players WHERE id=?", (pid,)).fetchone()
                    if not row:
                        shortlist.discard(pid)
                        continue
                    from src.data.queries import _row_to_player
                    p = _row_to_player(row)
                    value = estimate_player_value(p, current_date=gs.current_date)
                    p_club = queries.get_club(conn, p.club_id) if p.club_id else None
                    club_name = p_club.short_name if p_club else "Free Agent"
                    items.append(_player_row(p, value, club_name, True))
                except Exception:
                    shortlist.discard(pid)
        return items

    # ── My Squad (sell list) ─────────────────────────────────────────
    my_players = queries.get_players_by_club(conn, gs.user_club_id)
    sell_list = ft.Column(rtl=theme.rtl(), spacing=4)

    # Sort: listed first, then by OVR desc
    my_players.sort(key=lambda p: (-int(p.transfer_listed), -calculate_overall_rating(p)))

    for p in my_players:
        ovr = calculate_overall_rating(p)
        value = estimate_player_value(p, current_date=gs.current_date)
        listed = p.transfer_listed

        badges_parts = []
        if listed:
            badges_parts.append("📤 Listed")
        if p.injury_days_remaining > 0:
            badges_parts.append("🏥")
        if p.suspension_matches > 0:
            badges_parts.append("🚫")
        if p.is_captain:
            badges_parts.append("©")

        def make_sell_handler(player=p, val=value):
            def handler(e):
                _show_sell_dialog(page, conn, gs, club, player, val)
            return handler

        sell_list.controls.append(
            ft.Container(
                rtl=theme.rtl(), content=ft.Row(
                    rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            rtl=theme.rtl(), spacing=0, expand=True,
                            controls=[
                                ft.Row(rtl=theme.rtl(), spacing=5, tight=True, controls=[
                                    ft.Text(display_name(p), rtl=theme.rtl(), size=14, weight=ft.FontWeight.W_600, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Text(" ".join(badges_parts), rtl=theme.rtl(), size=10,
                                             color=ft.Colors.RED_400 if listed else ft.Colors.GREY_500)
                                    if badges_parts else ft.Container(rtl=theme.rtl()),
                                ]),
                                ft.Row(rtl=theme.rtl(), spacing=8, wrap=True, controls=[
                                    ft.Text(p.position.value, rtl=theme.rtl(), size=10, color=theme.GOLD),
                                    ft.Text(f"{t('age')} {p.age}", rtl=theme.rtl(), size=10, color=ft.Colors.GREY_400),
                                    ft.Text(f"OVR {ovr}", rtl=theme.rtl(), size=10, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"💰 {p.contract.wage_weekly:,}/wk", rtl=theme.rtl(), size=11,
                                             color=ft.Colors.GREY_500),
                                ]),
                            ],
                        ),
                        ft.Text(f"{value:,} EGP", rtl=theme.rtl(), size=11, color=theme.GOLD),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.RED) if listed
                else theme.CARD_GLASS,
                border=ft.border.all(1, theme.GOLD_BORDER),
                on_click=make_sell_handler(),
            )
        )

    # ── Free agents tab ──────────────────────────────────────────────
    free_agents_list = ft.Column(rtl=theme.rtl(), spacing=4)

    def load_free_agents(e=None):
        free_agents_list.controls.clear()
        frees = queries.search_players(conn, exclude_club_id=-1, limit=30)
        # exclude_club_id=-1 won't match, so filter manually
        frees = [p for p in queries.search_players(conn, limit=200) if p.club_id == 0 or p.club_id is None]
        if not frees:
            free_agents_list.controls.append(
                ft.Text(t("no_players_available"), rtl=theme.rtl(), size=13, color=ft.Colors.GREY_500))
        else:
            free_agents_list.controls.append(
                ft.Text(f"{len(frees)} free agent(s)", rtl=theme.rtl(), size=11, color=ft.Colors.GREY_500))
            for p in frees[:20]:
                ovr = calculate_overall_rating(p)
                value = estimate_player_value(p, current_date=gs.current_date)

                def make_free_handler(player=p):
                    def handler(e):
                        _show_free_agent_dialog(page, conn, gs, club, player)
                    return handler

                free_agents_list.controls.append(
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Row(
                            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(rtl=theme.rtl(), spacing=0, expand=True, controls=[
                                    ft.Text(display_name(p), rtl=theme.rtl(), size=14, weight=ft.FontWeight.W_600, expand=True, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Row(rtl=theme.rtl(), spacing=8, wrap=True, controls=[
                                        ft.Text(p.position.value, rtl=theme.rtl(), size=10, color=theme.GOLD),
                                        ft.Text(f"{t('age')} {p.age}", rtl=theme.rtl(), size=10),
                                        ft.Text(f"OVR {ovr}", rtl=theme.rtl(), size=10, weight=ft.FontWeight.BOLD),
                                    ]),
                                ]),
                                ft.Text(t("free"), rtl=theme.rtl(), size=11, color=ft.Colors.GREEN_400,
                                         weight=ft.FontWeight.BOLD),
                            ],
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        border_radius=theme.CARD_RADIUS_SM,
                        bgcolor=theme.CARD_GLASS,
                        border=ft.border.all(1, theme.GOLD_BORDER),
                        on_click=make_free_handler(),
                    )
                )
        page.update()

    # ── Budget info ──────────────────────────────────────────────────
    from src.core.transfers import get_window_status, is_transfer_window_open
    window_status = get_window_status(gs.current_date)
    window_open = is_transfer_window_open(gs.current_date)

    weekly_wage = sum(p.contract.wage_weekly for p in my_players)
    # ── Negotiations tab ───────────────────────────────────────────────
    from src.core.transfers import (
        get_user_negotiations, submit_counter_response,
        submit_wage_offer, cancel_negotiation, negotiation_pacing_hint,
    )

    negotiations_content = ft.Column(rtl=theme.rtl(), spacing=4, visible=False)

    def _build_negotiations_list():
        items = []
        negs = get_user_negotiations(conn, gs.user_club_id)
        if not negs:
            items.append(ft.Text("No active negotiations.\nMake an offer from the Search tab.",
                                  rtl=theme.rtl(), size=13, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER))
            return items

        for neg in negs:
            # Status badge
            if neg.status == "pending":
                badge = ft.Container(
                    rtl=theme.rtl(), content=ft.Text("⏳ Waiting", rtl=theme.rtl(), size=11, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.BLUE_700, padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                )
                action_btn = ft.Text(
                    negotiation_pacing_hint(neg, gs.current_date),
                    rtl=theme.rtl(), size=10,
                    color=ft.Colors.GREY_500,
                    italic=True,
                )
            elif neg.status == "countered":
                badge = ft.Container(
                    rtl=theme.rtl(), content=ft.Text("↩️ Countered", rtl=theme.rtl(), size=11, color=ft.Colors.WHITE),
                    bgcolor=theme.ACCENT_DARK, padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                )

                def make_counter_handler(n=neg):
                    def handler(e):
                        _show_counter_dialog(page, conn, gs, n)
                    return handler
                action_btn = ft.ElevatedButton("Respond", rtl=theme.rtl(), on_click=make_counter_handler(), height=30,
                                                style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                                      color=ft.Colors.WHITE,
                                                                      text_style=ft.TextStyle(size=11)))
            elif neg.status == "fee_agreed":
                badge = ft.Container(
                    rtl=theme.rtl(), content=ft.Text("✅ Fee Agreed", rtl=theme.rtl(), size=11, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREEN_700, padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    border_radius=4,
                )

                def make_wage_handler(n=neg):
                    def handler(e):
                        _show_wage_dialog(page, conn, gs, n)
                    return handler
                action_btn = ft.ElevatedButton("Offer Wage", rtl=theme.rtl(), on_click=make_wage_handler(), height=30,
                                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700,
                                                                      color=ft.Colors.WHITE,
                                                                      text_style=ft.TextStyle(size=11)))
            else:
                badge = ft.Container(
                    rtl=theme.rtl(), content=ft.Text(neg.status.title(), rtl=theme.rtl(), size=11, color=ft.Colors.GREY_400),
                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                )
                action_btn = ft.Container(rtl=theme.rtl())

            # Cancel button
            def make_cancel(n_id=neg.id):
                def handler(e):
                    cancel_negotiation(conn, n_id)
                    show_snackbar(page, "Negotiation withdrawn.")
                    navigate(page, "/transfers")
                return handler

            phase_text = "Fee" if neg.phase == "fee" else "Wage"
            offer_text = f"Your offer: {neg.current_offer:,} EGP"
            if neg.status == "countered":
                offer_text += f" → Counter: {neg.counter_price:,} EGP"
            if neg.status == "fee_agreed" and neg.phase == "wage":
                offer_text = f"Fee: {neg.current_offer:,} EGP (agreed)"
                if neg.wage_offer > 0:
                    offer_text += f"\nWage offer: {neg.wage_offer:,}/wk"

            items.append(
                ft.Container(
                    rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=4, controls=[
                        ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                            ft.Text(neg.player_name, rtl=theme.rtl(), size=13, weight=ft.FontWeight.BOLD, expand=True),
                            badge,
                        ]),
                        ft.Text(f"{neg.from_club_name} → {neg.to_club_name}", rtl=theme.rtl(), size=10,
                                 color=ft.Colors.GREY_500),
                        ft.Text(offer_text, rtl=theme.rtl(), size=11, color=theme.GOLD),
                        ft.Text(f"Attempt {neg.attempt}/{neg.max_attempts} | {phase_text} phase",
                                 rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                        ft.Text(negotiation_pacing_hint(neg, gs.current_date),
                                rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                        ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                            action_btn,
                            ft.TextButton("✖ Withdraw", rtl=theme.rtl(), on_click=make_cancel(),
                                           style=ft.ButtonStyle(color=ft.Colors.RED_400)),
                        ]),
                    ]),
                    padding=ft.padding.all(10),
                    border_radius=theme.CARD_RADIUS_SM,
                    bgcolor=theme.CARD_GLASS_STRONG,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.15, ft.Colors.AMBER)),
                )
            )

        return items

    # ── Tab content containers ───────────────────────────────────────
    search_content = ft.Column(
        rtl=theme.rtl(), spacing=8, visible=True,
        controls=[
            # Row 1: Name + Position (expand fills remaining space)
            ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                name_field, pos_dd,
            ]),
            # Row 2: Age + OVR + Search button
            ft.Row(rtl=theme.rtl(), spacing=6, controls=[
                max_age_field, min_ovr_field,
                ft.ElevatedButton(f"🔍 {t('search')}", rtl=theme.rtl(), on_click=do_search,
                                   expand=True, height=44),
            ]),
            ft.Divider(rtl=theme.rtl(), height=1),
            results_list,
        ],
    )

    sell_content = ft.Column(
        rtl=theme.rtl(), spacing=4, visible=False,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text(t("tap_to_list"), rtl=theme.rtl(), size=11,
                     color=ft.Colors.GREY_500, italic=True),
            sell_list,
        ],
    )

    shortlist_content = ft.Column(rtl=theme.rtl(), spacing=4, visible=False)

    free_content = ft.Column(
        rtl=theme.rtl(), spacing=4, visible=False,
        controls=[
            ft.ElevatedButton(f"🔄 {t('free_agent')}", rtl=theme.rtl(), on_click=load_free_agents, width=180),
            free_agents_list,
        ],
    )

    # ── Tab buttons ──────────────────────────────────────────────────
    active_negs = get_user_negotiations(conn, gs.user_club_id)
    active_tab = [0]

    _active_style = ft.ButtonStyle(
        bgcolor=theme.ACCENT_DARK, color=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=10),
    )
    _inactive_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=10),
        side=ft.BorderSide(1, theme.GOLD_BORDER),
    )

    tab_contents = [search_content, sell_content, shortlist_content,
                    free_content, negotiations_content]

    neg_label = f"{t('negotiations')} ({len(active_negs)})"
    tab_labels = [t("search"), t("sell"), f"{t('shortlist')} ({len(shortlist)})",
                  t("free_agent"), neg_label]
    tab_btns = []
    for i, lbl in enumerate(tab_labels):
        tab_btns.append(
            ft.ElevatedButton(lbl, rtl=theme.rtl(), on_click=None, height=44,
                               style=_active_style if i == 0 else _inactive_style)
        )

    def switch_tab(idx):
        def handler(e):
            active_tab[0] = idx
            for i, tc in enumerate(tab_contents):
                tc.visible = (i == idx)
            for i, btn in enumerate(tab_btns):
                btn.style = _active_style if i == idx else _inactive_style
            if idx == 2:
                shortlist_content.controls.clear()
                shortlist_content.controls.extend(_build_shortlist_content())
            if idx == 3:
                load_free_agents()
            if idx == 4:
                negotiations_content.controls.clear()
                negotiations_content.controls.extend(_build_negotiations_list())
            page.update()
        return handler

    for i, btn in enumerate(tab_btns):
        btn.on_click = switch_tab(i)

    tab_row = ft.Row(rtl=theme.rtl(), spacing=4, wrap=True, controls=tab_btns)

    # ── Budget summary (collapsible) ─────────────────────────────────
    from src.ui.widgets.cards import collapsible_section

    from src.ui.widgets.cards import kv_row
    budget_section = ft.Container(rtl=theme.rtl(), padding=20, border_radius=14,
        bgcolor=theme.CARD_GLASS_STRONG, border=ft.border.all(1, theme.GOLD_BORDER),
        content=ft.Column(rtl=theme.rtl(), spacing=12, controls=[
            ft.Row(rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
                ft.Text(t("transfer_budget"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
                ft.Icon(ft.Icons.LOCK_OPEN if window_open else ft.Icons.LOCK_OUTLINED,
                        rtl=theme.rtl(), size=18, color=theme.TEXT_SUCCESS if window_open else theme.TEXT_WARNING),
            ]),
            ft.Text(f"{club.finances.transfer_budget:,}", rtl=False, size=36, font_family=theme.display_font()),
            ft.Text("EGP · " + (t("open_window") if window_open else t("closed_window")), rtl=theme.rtl(), size=12, color=theme.TEXT_SECONDARY),
            kv_row(t("weekly_wage_bill"), f"{weekly_wage:,} EGP"),
        ]))


    return ft.Column(
        rtl=theme.rtl(), expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                rtl=theme.rtl(), padding=theme.PAGE_PADDING,
                content=ft.Column(
                    rtl=theme.rtl(), spacing=24,
                    controls=[
                        theme.header_bar(
                            title=t("transfer_market"),
                            icon=ft.Icons.STORE,
                            page=page,
                            back_route="/squad",
                        ),
                        budget_section,
                        tab_row,
                        search_content,
                        sell_content,
                        shortlist_content,
                        free_content,
                        negotiations_content,
                    ],
                ),
            ),
        ],
    )


def _show_buy_dialog(page, conn, gs, user_club, player, estimated_value, shortlist=None):
    """Show dialog to submit a transfer offer (fee only — wage negotiated later)."""
    from src.ui.app import navigate, show_snackbar
    from src.core.transfers import submit_transfer_offer, is_transfer_window_open

    # Check transfer window
    if not is_transfer_window_open(gs.current_date):
        show_snackbar(page, "❌ Transfer window is closed! Wait for the next window.",
                      bgcolor=ft.Colors.RED_800)
        return

    ovr = calculate_overall_rating(player)
    a = player.attributes
    selling_club = queries.get_club(conn, player.club_id) if player.club_id else None
    selling_name = selling_club.name if selling_club else "Free Agent"

    suggested_offer = int(estimated_value * 0.85)

    offer_field = ft.TextField(
        border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label="Transfer Fee Offer (EGP)", value=str(suggested_offer),
        width=220, text_size=14,
    )

    def submit_offer(e):
        try:
            offer = int(offer_field.value)
        except ValueError:
            show_snackbar(page, "Enter a valid number!", bgcolor=ft.Colors.RED_800)
            return

        can_buy, reason = can_sign_player(user_club, player, offer)
        if not can_buy:
            show_snackbar(page, f"❌ {reason}", bgcolor=ft.Colors.RED_800)
            return

        if offer < estimated_value * 0.3:
            show_snackbar(page, "❌ Offer too low — they won't even consider it.", bgcolor=ft.Colors.RED_800)
            return

        # Submit async offer — response comes next day
        submit_transfer_offer(conn, gs, player, offer)
        page.pop_dialog()
        if shortlist and player.id in shortlist:
            shortlist.discard(player.id)
        show_snackbar(page, f"📨 Offer submitted! {selling_name} will respond tomorrow.")
        navigate(page, "/transfers")

    # Key stats preview
    key_stats = []
    if player.position.value == "GK":
        key_stats = [
            stat_bar("Reflexes", a.gk_reflexes),
            stat_bar("Handling", a.gk_handling),
            stat_bar("Positioning", a.gk_positioning),
        ]
    elif player.position.value in ("ST", "LW", "RW", "CAM"):
        key_stats = [
            stat_bar("Finishing", a.finishing),
            stat_bar("Pace", a.pace),
            stat_bar("Dribbling", a.dribbling),
        ]
    elif player.position.value in ("CB", "LB", "RB"):
        key_stats = [
            stat_bar("Tackling", a.tackling),
            stat_bar("Marking", a.marking),
            stat_bar("Strength", a.strength),
        ]
    else:
        key_stats = [
            stat_bar("Passing", a.passing),
            stat_bar("Vision", a.vision),
            stat_bar("Stamina", a.stamina),
        ]

    expiry = player.contract.contract_expiry
    expiry_str = expiry.strftime("%b %Y") if expiry else "N/A"

    dlg = ft.AlertDialog(
        rtl=theme.rtl(), title=ft.Text(f"📝 Sign {player.name}", rtl=theme.rtl(), color=theme.GOLD),
        content=ft.Container(
            rtl=theme.rtl(), content=ft.Column(
                rtl=theme.rtl(), spacing=6, scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                        ft.Text(f"📍 {player.position.value}", rtl=theme.rtl(), size=12, color=theme.GOLD),
                        ft.Text(f"{t('age')} {player.age}", rtl=theme.rtl(), size=12),
                        ft.Container(
                            rtl=theme.rtl(), content=ft.Text(str(ovr), rtl=theme.rtl(), size=14, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREEN),
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=6,
                        ),
                    ]),
                    ft.Text(f"Club: {selling_name}", rtl=theme.rtl(), size=12),
                    ft.Row(rtl=theme.rtl(), spacing=12, controls=[
                        ft.Text(f"💰 Value: {estimated_value:,} EGP", rtl=theme.rtl(), size=11, color=theme.GOLD),
                        ft.Text(f"📅 Contract: {expiry_str}", rtl=theme.rtl(), size=11, color=ft.Colors.GREY_400),
                    ]),
                    ft.Text(f"Current wage: {player.contract.wage_weekly:,} EGP/wk", rtl=theme.rtl(), size=11,
                             color=ft.Colors.GREY_500),
                    ft.Divider(rtl=theme.rtl(), height=1),
                    ft.Text("📊 Key Stats", rtl=theme.rtl(), size=12, weight=ft.FontWeight.W_500,
                             color=theme.GOLD),
                    *key_stats,
                    ft.Divider(rtl=theme.rtl(), height=1),
                    ft.Text("💼 Step 1: Offer Transfer Fee", rtl=theme.rtl(), size=12, weight=ft.FontWeight.W_500),
                    ft.Text("The club will respond the next day.\n"
                             "If accepted, you'll negotiate wages with the player.",
                             rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                    offer_field,
                ],
            ),
            width=290, height=380,
        ),
        actions=[
            ft.TextButton("Cancel", rtl=theme.rtl(), on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("📨 Submit Offer", rtl=theme.rtl(), on_click=submit_offer,
                              style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                    color=ft.Colors.WHITE,
                                                    shape=ft.RoundedRectangleBorder(radius=10))),
        ],
    )
    page.show_dialog(dlg)


def _show_sell_dialog(page, conn, gs, user_club, player, estimated_value):
    """Show sell dialog with asking price and list/unlist toggle."""
    from src.ui.app import navigate, show_snackbar

    ovr = calculate_overall_rating(player)

    if player.transfer_listed:
        # Already listed — offer to unlist
        dlg = ft.AlertDialog(
            rtl=theme.rtl(), title=ft.Text(f"📤 {player.name}", rtl=theme.rtl(), color=theme.GOLD),
            content=ft.Container(
                rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=6, controls=[
                    ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                        ft.Text(f"{player.position.value}", rtl=theme.rtl(), size=12, color=theme.GOLD),
                        ft.Text(f"{t('age')} {player.age}", rtl=theme.rtl(), size=12),
                        ft.Text(f"OVR {ovr}", rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Text(f"Currently listed at {estimated_value:,} EGP", rtl=theme.rtl(), size=12,
                             color=ft.Colors.RED_400),
                    ft.Text("Remove from the transfer list?", rtl=theme.rtl(), size=12),
                ]),
                width=280,
            ),
            actions=[
                ft.TextButton("Keep Listed", rtl=theme.rtl(), on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton("Remove Listing", rtl=theme.rtl(), on_click=lambda e: (
                    queries.set_transfer_listed(conn, player.id, False),
                    page.pop_dialog(),
                    show_snackbar(page, f"{player.name} removed from transfer list."),
                    navigate(page, "/transfers"),
                )),
            ],
        )
    else:
        # Not listed — offer to list with asking price
        asking_field = ft.TextField(
            border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label="Asking Price (EGP)", value=str(estimated_value),
            width=200, text_size=14,
        )

        def list_player(e):
            queries.set_transfer_listed(conn, player.id, True)
            page.pop_dialog()
            show_snackbar(page, f"📤 {player.name} listed for transfer.")
            navigate(page, "/transfers")

        dlg = ft.AlertDialog(
            rtl=theme.rtl(), title=ft.Text(f"💰 Sell {player.name}?", rtl=theme.rtl(), color=theme.GOLD),
            content=ft.Container(
                rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=6, controls=[
                    ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                        ft.Text(f"{player.position.value}", rtl=theme.rtl(), size=12, color=theme.GOLD),
                        ft.Text(f"{t('age')} {player.age}", rtl=theme.rtl(), size=12),
                        ft.Text(f"OVR {ovr}", rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Text(f"Wage: {player.contract.wage_weekly:,} EGP/wk", rtl=theme.rtl(), size=11,
                             color=ft.Colors.GREY_500),
                    ft.Text(f"Estimated value: {estimated_value:,} EGP", rtl=theme.rtl(), size=12,
                             color=theme.GOLD),
                    ft.Divider(rtl=theme.rtl(), height=1),
                    ft.Text("AI clubs will make offers once listed.\n"
                             "Higher-value players attract more interest.", rtl=theme.rtl(), size=11,
                             color=ft.Colors.GREY_500),
                    asking_field,
                ]),
                width=280,
            ),
            actions=[
                ft.TextButton("Cancel", rtl=theme.rtl(), on_click=lambda e: page.pop_dialog()),
                ft.ElevatedButton("📤 List for Transfer", rtl=theme.rtl(), on_click=list_player,
                                  style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                        color=ft.Colors.WHITE,
                                                        shape=ft.RoundedRectangleBorder(radius=10))),
            ],
        )

    page.show_dialog(dlg)


def _show_free_agent_dialog(page, conn, gs, user_club, player):
    """Show dialog to sign a free agent (no transfer fee)."""
    from src.ui.app import navigate, show_snackbar
    from src.core.finance import can_afford_wage

    ovr = calculate_overall_rating(player)
    suggested_wage = max(5000, int(player.current_ability * 200))

    wage_field = ft.TextField(
        border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label="Weekly Wage Offer", value=str(suggested_wage),
        width=200, text_size=14,
    )

    def sign_free(e):
        try:
            wage = int(wage_field.value)
        except ValueError:
            show_snackbar(page, "Enter a valid wage!", bgcolor=ft.Colors.RED_800)
            return

        if not can_afford_wage(user_club, wage):
            show_snackbar(page, "❌ Cannot afford this wage!", bgcolor=ft.Colors.RED_800)
            return

        # Free agents accept if wage is reasonable
        min_acceptable = max(3000, int(player.current_ability * 150))
        if wage < min_acceptable:
            show_snackbar(page, f"❌ Player wants at least {min_acceptable:,} EGP/wk")
            return

        queries.transfer_player(conn, player.id, 0, gs.user_club_id, fee=0, wage=wage,
                               current_date=gs.current_date)
        page.pop_dialog()
        queries.insert_message(conn, InboxMessage(
            date=gs.current_date,
            subject=f"✅ Free Agent Signed: {player.name}",
            body=f"{player.name} has signed for {gs.user_club_name} on a free transfer.\nWage: {wage:,} EGP/wk.",
            category="transfer",
        ))
        show_snackbar(page, f"✅ {player.name} signed on a free!", bgcolor=ft.Colors.GREEN_800)
        try:
            from src.ui.app import show_breaking_news
            show_breaking_news(page, f"{player.name} signs for {gs.user_club_name}!",
                               body=f"Free transfer — Wage: {wage:,} EGP/wk",
                               category="transfer")
        except Exception:
            pass
        navigate(page, "/transfers")

    dlg = ft.AlertDialog(
        rtl=theme.rtl(), title=ft.Text(f"🆓 Sign {player.name}", rtl=theme.rtl(), color=theme.GOLD),
        content=ft.Container(
            rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=6, controls=[
                ft.Row(rtl=theme.rtl(), spacing=8, controls=[
                    ft.Text(f"{player.position.value}", rtl=theme.rtl(), size=12, color=theme.GOLD),
                    ft.Text(f"{t('age')} {player.age}", rtl=theme.rtl(), size=12),
                    ft.Text(f"OVR {ovr}", rtl=theme.rtl(), size=12, weight=ft.FontWeight.BOLD),
                ]),
                ft.Text("Free Agent — No transfer fee required", rtl=theme.rtl(), size=12,
                         color=ft.Colors.GREEN_400),
                ft.Divider(rtl=theme.rtl(), height=1),
                ft.Text("Offer a weekly wage to sign this player:", rtl=theme.rtl(), size=12),
                wage_field,
            ]),
            width=280,
        ),
        actions=[
            ft.TextButton("Cancel", rtl=theme.rtl(), on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("✅ Sign Player", rtl=theme.rtl(), on_click=sign_free,
                              style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_800,
                                                    color=ft.Colors.WHITE,
                                                    shape=ft.RoundedRectangleBorder(radius=10))),
        ],
    )
    page.show_dialog(dlg)


def _show_counter_dialog(page, conn, gs, neg):
    """Show dialog to respond to a counter-offer."""
    from src.ui.app import navigate, show_snackbar
    from src.core.transfers import submit_counter_response, cancel_negotiation

    offer_field = ft.TextField(
        border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label="Your Revised Offer (EGP)", value=str(neg.counter_price),
        width=220, text_size=14,
    )

    def submit_revised(e):
        try:
            new_offer = int(offer_field.value)
        except ValueError:
            show_snackbar(page, "Enter a valid number!", bgcolor=ft.Colors.RED_800)
            return

        if new_offer <= 0:
            show_snackbar(page, "Offer must be positive!", bgcolor=ft.Colors.RED_800)
            return

        submit_counter_response(conn, gs, neg.id, new_offer)
        page.pop_dialog()
        show_snackbar(page, f"📨 Revised offer sent. Response tomorrow.")
        navigate(page, "/transfers")

    def accept_counter(e):
        """Accept the counter-offer price as-is."""
        submit_counter_response(conn, gs, neg.id, neg.counter_price)
        page.pop_dialog()
        show_snackbar(page, f"📨 Accepted counter-offer of {neg.counter_price:,} EGP. Response tomorrow.")
        navigate(page, "/transfers")

    def walk_away(e):
        cancel_negotiation(conn, neg.id)
        page.pop_dialog()
        show_snackbar(page, "❌ Negotiation withdrawn.")
        navigate(page, "/transfers")

    dlg = ft.AlertDialog(
        rtl=theme.rtl(), title=ft.Text(f"↩️ Counter-Offer: {neg.player_name}", rtl=theme.rtl(), color=theme.GOLD),
        content=ft.Container(
            rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=6, controls=[
                ft.Text(f"From: {neg.from_club_name}", rtl=theme.rtl(), size=12, color=ft.Colors.GREY_400),
                ft.Divider(rtl=theme.rtl(), height=1),
                ft.Text(f"Your offer: {neg.current_offer:,} EGP", rtl=theme.rtl(), size=12),
                ft.Text(f"Their counter: {neg.counter_price:,} EGP",
                         rtl=theme.rtl(), size=13, weight=ft.FontWeight.BOLD, color=theme.GOLD),
                ft.Text(f"Attempt {neg.attempt}/{neg.max_attempts}", rtl=theme.rtl(), size=11,
                         color=ft.Colors.GREY_500),
                ft.Divider(rtl=theme.rtl(), height=1),
                ft.Text("You can accept their price, submit a new offer,\nor walk away.",
                         rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                offer_field,
            ]),
            width=300,
        ),
        actions=[
            ft.TextButton("❌ Walk Away", rtl=theme.rtl(), on_click=walk_away),
            ft.OutlinedButton("✅ Accept Counter", rtl=theme.rtl(), on_click=accept_counter),
            ft.ElevatedButton("📨 New Offer", rtl=theme.rtl(), on_click=submit_revised,
                              style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                    color=ft.Colors.WHITE,
                                                    shape=ft.RoundedRectangleBorder(radius=10))),
        ],
    )
    page.show_dialog(dlg)


def _show_wage_dialog(page, conn, gs, neg):
    """Show dialog to offer wages after fee is agreed."""
    from src.ui.app import navigate, show_snackbar
    from src.core.transfers import submit_wage_offer, cancel_negotiation

    suggested_wage = int(neg.current_wage * 1.1)  # 10% raise as suggestion

    wage_field = ft.TextField(
        border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT, filled=True, fill_color=theme.BG_MID, rtl=theme.rtl(), label="Weekly Wage Offer (EGP)", value=str(suggested_wage),
        width=220, text_size=14,
    )

    def submit_wage(e):
        try:
            wage = int(wage_field.value)
        except ValueError:
            show_snackbar(page, "Enter a valid number!", bgcolor=ft.Colors.RED_800)
            return

        if wage <= 0:
            show_snackbar(page, "Wage must be positive!", bgcolor=ft.Colors.RED_800)
            return

        submit_wage_offer(conn, gs, neg.id, wage)
        page.pop_dialog()
        show_snackbar(page, f"📨 Wage offer sent to {neg.player_name}. Response tomorrow.")
        navigate(page, "/transfers")

    def walk_away(e):
        cancel_negotiation(conn, neg.id)
        page.pop_dialog()
        show_snackbar(page, "❌ Deal abandoned.")
        navigate(page, "/transfers")

    dlg = ft.AlertDialog(
        rtl=theme.rtl(), title=ft.Text(f"💰 Personal Terms: {neg.player_name}", rtl=theme.rtl(), color=theme.GOLD),
        content=ft.Container(
            rtl=theme.rtl(), content=ft.Column(rtl=theme.rtl(), spacing=6, controls=[
                ft.Text(f"✅ Transfer fee agreed: {neg.current_offer:,} EGP", rtl=theme.rtl(), size=12,
                         color=ft.Colors.GREEN_400),
                ft.Divider(rtl=theme.rtl(), height=1),
                ft.Text(f"Player's current wage: {neg.current_wage:,} EGP/wk", rtl=theme.rtl(), size=12),
                *(
                    [ft.Text(f"Last rejected offer: {neg.wage_offer:,} EGP/wk", rtl=theme.rtl(), size=11,
                              color=ft.Colors.RED_400)]
                    if neg.wage_offer > 0 else []
                ),
                *(
                    [ft.Text(f"Player wants at least: ~{neg.counter_price:,} EGP/wk", rtl=theme.rtl(), size=11,
                              color=theme.GOLD)]
                    if neg.counter_price > 0 and neg.phase == "wage" else []
                ),
                ft.Divider(rtl=theme.rtl(), height=1),
                ft.Text("Step 2: Agree personal terms with the player.\n"
                         "The player will respond the next day.",
                         rtl=theme.rtl(), size=10, color=ft.Colors.GREY_500),
                wage_field,
            ]),
            width=300,
        ),
        actions=[
            ft.TextButton("❌ Walk Away", rtl=theme.rtl(), on_click=walk_away),
            ft.ElevatedButton("📨 Offer Wage", rtl=theme.rtl(), on_click=submit_wage,
                              style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                    color=ft.Colors.WHITE,
                                                    shape=ft.RoundedRectangleBorder(radius=10))),
        ],
    )
    page.show_dialog(dlg)

