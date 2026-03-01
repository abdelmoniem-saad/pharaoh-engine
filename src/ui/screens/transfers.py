"""
Transfer Market screen — search, scout, buy, and sell players.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.data.models import InboxMessage
from src.core.transfers import estimate_player_value, can_sign_player, negotiate_fee
from src.core.player import calculate_overall_rating
from src.ui.widgets.nav_bar import build_nav_bar
from src.utils.config import Position


def build_transfers_screen(page: ft.Page) -> ft.Column:
    """Build the transfer market screen."""
    from src.ui.app import app_state, navigate, show_snackbar

    page.navigation_bar = build_nav_bar(page, 0)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    club = queries.get_club(conn, gs.user_club_id)
    if not club:
        return ft.Column(controls=[ft.Text("Club not found")])

    # ── Search controls ──────────────────────────────────────────────────
    name_field = ft.TextField(label="Name", width=140, text_size=13)
    pos_dd = ft.Dropdown(
        label="Position", width=100,
        options=[ft.dropdown.Option("Any")] + [ft.dropdown.Option(p.value) for p in Position],
        value="Any",
    )
    max_age_field = ft.TextField(label="Max Age", width=70, value="35", text_size=13)

    results_list = ft.Column(spacing=4)

    def do_search(e):
        pos = pos_dd.value if pos_dd.value != "Any" else ""
        try:
            max_age = int(max_age_field.value) if max_age_field.value else 99
        except ValueError:
            max_age = 99
        name = name_field.value or ""

        players = queries.search_players(
            conn, name=name, position=pos, max_age=max_age,
            exclude_club_id=gs.user_club_id, limit=30,
        )
        results_list.controls.clear()

        if not players:
            results_list.controls.append(
                ft.Text("No players found.", size=13, color=ft.Colors.GREY_500))
        else:
            results_list.controls.append(
                ft.Text(f"Found {len(players)} players", size=11, color=ft.Colors.GREY_500))
            for p in players:
                ovr = calculate_overall_rating(p)
                value = estimate_player_value(p)
                p_club = queries.get_club(conn, p.club_id) if p.club_id else None
                club_name = p_club.short_name if p_club else "Free"

                def make_handler(player=p, val=value):
                    def handler(e):
                        _show_buy_dialog(page, conn, gs, club, player, val)
                    return handler

                results_list.controls.append(
                    ft.Container(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=0, expand=True,
                                    controls=[
                                        ft.Text(p.name, size=12, weight=ft.FontWeight.W_500),
                                        ft.Text(
                                            f"{p.position.value} | Age {p.age} | OVR {ovr} | {club_name}",
                                            size=10, color=ft.Colors.GREY_400,
                                        ),
                                    ],
                                ),
                                ft.Column(
                                    spacing=0,
                                    horizontal_alignment=ft.CrossAxisAlignment.END,
                                    controls=[
                                        ft.Text(f"{value:,}", size=11,
                                                 weight=ft.FontWeight.BOLD,
                                                 color=ft.Colors.AMBER_300),
                                        ft.Text("EGP", size=9, color=ft.Colors.GREY_600),
                                    ],
                                ),
                            ],
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        border_radius=6,
                        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                        on_click=make_handler(),
                    )
                )
        page.update()

    # ── My Squad (sell list) ─────────────────────────────────────────────
    my_players = queries.get_players_by_club(conn, gs.user_club_id)
    sell_list = ft.Column(spacing=4)

    for p in my_players:
        ovr = calculate_overall_rating(p)
        value = estimate_player_value(p)
        status = "🔴 Listed" if p.transfer_listed else ""

        def make_sell_handler(player=p, val=value):
            def handler(e):
                _show_sell_dialog(page, conn, gs, club, player, val)
            return handler

        sell_list.controls.append(
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=0, expand=True,
                            controls=[
                                ft.Row(spacing=5, controls=[
                                    ft.Text(p.name, size=12, weight=ft.FontWeight.W_500),
                                    ft.Text(status, size=10, color=ft.Colors.RED_400) if status else ft.Container(),
                                ]),
                                ft.Text(
                                    f"{p.position.value} | Age {p.age} | OVR {ovr}",
                                    size=10, color=ft.Colors.GREY_400,
                                ),
                            ],
                        ),
                        ft.Text(f"{value:,} EGP", size=11, color=ft.Colors.AMBER_300),
                    ],
                ),
                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                border_radius=6,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.RED) if p.transfer_listed else ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                on_click=make_sell_handler(),
            )
        )

    # Budget info
    budget_bar = ft.Container(
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Text("💰 Transfer Budget", size=12, color=ft.Colors.GREY_400),
                ft.Text(f"{club.finances.transfer_budget:,} EGP", size=13,
                         weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400),
            ],
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=6),
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.GREEN),
        border_radius=6,
    )

    # ── Tab switching via buttons (Flet 0.80 has no simple Tabs) ─────────
    search_content = ft.Column(
        spacing=8, visible=True,
        controls=[
            ft.Row(spacing=6, wrap=True, controls=[
                name_field, pos_dd, max_age_field,
            ]),
            ft.ElevatedButton("Search", on_click=do_search, width=120),
            ft.Divider(height=1),
            results_list,
        ],
    )

    sell_content = ft.Column(
        spacing=4, visible=False,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Text("Tap a player to list/unlist for transfer", size=11,
                     color=ft.Colors.GREY_500, italic=True),
            sell_list,
        ],
    )

    search_btn = ft.ElevatedButton("🔍 Search Players", width=150)
    sell_btn = ft.OutlinedButton("💰 My Squad", width=150)

    def show_search(e):
        search_content.visible = True
        sell_content.visible = False
        page.update()

    def show_sell(e):
        search_content.visible = False
        sell_content.visible = True
        page.update()

    search_btn.on_click = show_search
    sell_btn.on_click = show_sell

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.only(left=12, right=12, top=10, bottom=10),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("🏪 Transfer Market", size=22,
                                         weight=ft.FontWeight.BOLD),
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    tooltip="Back to Squad",
                                    on_click=lambda e: navigate(page, "/squad"),
                                ),
                            ],
                        ),
                        budget_bar,
                        ft.Row(spacing=8, controls=[search_btn, sell_btn]),
                        ft.Divider(height=1),
                        search_content,
                        sell_content,
                    ],
                ),
            ),
        ],
    )


def _show_buy_dialog(page, conn, gs, user_club, player, estimated_value):
    """Show dialog to make an offer for a player."""
    from src.ui.app import navigate, show_snackbar

    ovr = calculate_overall_rating(player)
    selling_club = queries.get_club(conn, player.club_id) if player.club_id else None
    selling_name = selling_club.name if selling_club else "Free Agent"

    offer_field = ft.TextField(
        label="Your Offer (EGP)", value=str(estimated_value),
        width=200, text_size=14,
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

        accepted, counter = negotiate_fee(estimated_value, offer)
        if accepted:
            queries.transfer_player(
                conn, player.id, player.club_id or 0, gs.user_club_id,
                fee=offer, wage=player.contract.wage_weekly,
            )
            page.pop_dialog()
            queries.insert_message(conn, InboxMessage(
                date=gs.current_date,
                subject=f"✅ Transfer Complete: {player.name}",
                body=f"{player.name} has joined {gs.user_club_name} from {selling_name} for {offer:,} EGP.",
                category="transfer",
            ))
            show_snackbar(page, f"✅ {player.name} signed!", bgcolor=ft.Colors.GREEN_800)
            navigate(page, "/transfers")
        else:
            offer_field.value = str(counter)
            page.update()
            show_snackbar(page, f"❌ Rejected! Counter-offer: {counter:,} EGP")

    dlg = ft.AlertDialog(
        title=ft.Text(f"📝 Sign {player.name}"),
        content=ft.Container(
            content=ft.Column(
                spacing=8, tight=True,
                controls=[
                    ft.Text(f"{player.position.value} | Age {player.age} | OVR {ovr}",
                             size=12, color=ft.Colors.GREY_400),
                    ft.Text(f"Club: {selling_name}", size=12),
                    ft.Text(f"Estimated Value: {estimated_value:,} EGP", size=12,
                             color=ft.Colors.AMBER_300),
                    ft.Text(f"Wage: {player.contract.wage_weekly:,} EGP/wk", size=12),
                    ft.Divider(height=1),
                    offer_field,
                ],
            ),
            width=300, height=220,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton("Submit Offer", on_click=submit_offer),
        ],
    )
    page.show_dialog(dlg)


def _show_sell_dialog(page, conn, gs, user_club, player, estimated_value):
    """Toggle transfer list or accept AI offer."""
    from src.ui.app import navigate, show_snackbar

    if player.transfer_listed:
        queries.set_transfer_listed(conn, player.id, False)
        show_snackbar(page, f"{player.name} removed from transfer list.")
        navigate(page, "/transfers")
    else:
        queries.set_transfer_listed(conn, player.id, True)
        show_snackbar(page, f"🔴 {player.name} listed for {estimated_value:,} EGP.")
        navigate(page, "/transfers")
