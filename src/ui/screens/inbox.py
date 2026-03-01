"""
Inbox screen — game messages with card-based mobile layout.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.ui.theme import (
    ACCENT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    CARD_BG, CARD_RADIUS, CARD_RADIUS_SM, PAGE_PADDING, SECTION_SPACING,
    TITLE_SIZE, BODY_SIZE, CAPTION_SIZE, TINY_SIZE, ACCENT_BG,
)


# Category styling
_CAT_COLORS = {
    "match": ft.Colors.GREEN_400,
    "media": ft.Colors.BLUE_400,
    "board": ft.Colors.PURPLE_400,
    "transfer": ft.Colors.AMBER_400,
    "general": ft.Colors.GREY_400,
}
_CAT_ICONS = {
    "match": ft.Icons.SPORTS_SOCCER,
    "media": ft.Icons.NEWSPAPER,
    "board": ft.Icons.ACCOUNT_BALANCE,
    "transfer": ft.Icons.ATTACH_MONEY,
    "general": ft.Icons.MAIL,
}


def build_inbox_screen(page: ft.Page) -> ft.Column:
    """Build the inbox/messages content with mobile card layout."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 4)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    messages = queries.get_inbox(conn, limit=30)
    unread = queries.get_unread_count(conn)

    msg_tiles = []
    if not messages:
        msg_tiles.append(
            ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.INBOX, size=48, color=TEXT_MUTED),
                        ft.Container(height=8),
                        ft.Text("No messages yet.", size=BODY_SIZE, color=TEXT_SECONDARY),
                        ft.Text("Play some matches to receive updates!",
                                size=CAPTION_SIZE, color=TEXT_MUTED),
                    ],
                ),
                padding=40,
            )
        )
    else:
        for msg in messages:
            cat_color = _CAT_COLORS.get(msg.category, ft.Colors.GREY_400)
            cat_icon = _CAT_ICONS.get(msg.category, ft.Icons.MAIL)
            icon_color = cat_color if not msg.is_read else TEXT_MUTED
            title_weight = ft.FontWeight.W_600 if not msg.is_read else ft.FontWeight.NORMAL
            bg = ft.Colors.with_opacity(0.04, ft.Colors.AMBER) if not msg.is_read else CARD_BG

            def make_handler(m=msg):
                def handler(e):
                    _show_message_detail(page, conn, m)
                return handler

            # Badge for unread
            unread_badge = []
            if not msg.is_read:
                unread_badge.append(
                    ft.Container(
                        content=ft.Text("NEW", size=8, color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.RED_400,
                        padding=ft.padding.symmetric(horizontal=5, vertical=2),
                        border_radius=4,
                    )
                )

            msg_tiles.append(
                ft.Container(
                    content=ft.Row(
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            # Category icon
                            ft.Container(
                                content=ft.Icon(cat_icon, size=18, color=icon_color),
                                width=36, height=36, border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.1, cat_color),
                                alignment=ft.Alignment(0, 0),
                            ),
                            # Content
                            ft.Column(spacing=2, expand=True, controls=[
                                ft.Row(spacing=4, tight=True, controls=[
                                    ft.Text(msg.subject, size=BODY_SIZE, weight=title_weight,
                                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                            expand=True),
                                    *unread_badge,
                                ]),
                                ft.Text(
                                    f"{msg.date.strftime('%d %b')} — {msg.body}",
                                    size=CAPTION_SIZE, color=TEXT_SECONDARY,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ]),
                            # Chevron
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=16, color=TEXT_MUTED),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=CARD_RADIUS_SM,
                    bgcolor=bg,
                    border=ft.border.only(left=ft.BorderSide(3, cat_color)),
                    on_click=make_handler(),
                    ink=True,
                )
            )

    # Header controls
    header_controls = [
        ft.Text("📥 Inbox", size=TITLE_SIZE, weight=ft.FontWeight.BOLD, expand=True),
    ]
    if unread > 0:
        def mark_all_read(e):
            from src.ui.app import show_snackbar
            count = queries.mark_all_messages_read(conn)
            show_snackbar(page, f"✅ {count} message(s) marked as read")
            navigate(page, "/inbox")

        header_controls.append(
            ft.TextButton("Mark all read", icon=ft.Icons.DONE_ALL,
                          on_click=mark_all_read)
        )

    # Unread pill
    unread_pill = []
    if unread > 0:
        unread_pill.append(
            ft.Container(
                content=ft.Text(f"{unread} unread", size=CAPTION_SIZE,
                                color=ACCENT, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                border_radius=12,
                bgcolor=ACCENT_BG,
            )
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=ft.padding.all(PAGE_PADDING),
                content=ft.Column(
                    spacing=SECTION_SPACING,
                    controls=[
                        ft.Row(controls=header_controls),
                        *unread_pill,
                        ft.Column(spacing=4, controls=msg_tiles),
                    ],
                ),
            ),
        ],
    )


def _show_message_detail(page: ft.Page, conn, msg):
    """Show the full message in a dialog, then mark as read."""
    from src.ui.app import navigate, show_snackbar

    cat_icons = {
        "match": "⚽", "media": "📰", "board": "🏛️",
        "transfer": "💰", "general": "📧",
    }
    cat_emoji = cat_icons.get(msg.category, "📧")

    def close_handler(e):
        if not msg.is_read:
            queries.mark_message_read(conn, msg.id)
        page.pop_dialog()
        navigate(page, "/inbox")

    # Check if this is a transfer offer with parseable data
    actions = [ft.TextButton("Close", on_click=close_handler)]
    display_body = msg.body

    if msg.category == "transfer" and "TRANSFER_OFFER|" in msg.body:
        # Parse transfer offer: TRANSFER_OFFER|player_id|from_club|to_club|fee|wage
        try:
            parts = msg.body.split("TRANSFER_OFFER|")[1].split("|")
            player_id = int(parts[0])
            from_club_id = int(parts[1])
            to_club_id = int(parts[2])
            fee = int(parts[3])
            wage = int(parts[4])

            # Show body without the parseable line
            display_body = msg.body.split("\nTRANSFER_OFFER|")[0]

            def accept_offer(e):
                queries.transfer_player(conn, player_id, from_club_id, to_club_id,
                                         fee=fee, wage=wage,
                                         current_date=gs.current_date)
                if not msg.is_read:
                    queries.mark_message_read(conn, msg.id)
                page.pop_dialog()
                show_snackbar(page, f"✅ Transfer accepted! Fee: {fee:,} EGP")
                navigate(page, "/inbox")

            def decline_offer(e):
                if not msg.is_read:
                    queries.mark_message_read(conn, msg.id)
                page.pop_dialog()
                show_snackbar(page, "❌ Offer declined.")
                navigate(page, "/inbox")

            actions = [
                ft.TextButton("❌ Decline", on_click=decline_offer),
                ft.ElevatedButton("✅ Accept", on_click=accept_offer),
            ]
        except (IndexError, ValueError):
            pass  # Not a valid offer format, show normally

    dlg = ft.AlertDialog(
        title=ft.Text(f"{cat_emoji} {msg.subject}", size=16,
                      weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        msg.date.strftime("%A, %d %B %Y"),
                        size=11, color=ft.Colors.GREY_500,
                    ),
                    ft.Text(
                        msg.category.title(),
                        size=10, color=ft.Colors.AMBER_400,
                        weight=ft.FontWeight.W_500,
                    ),
                    ft.Divider(height=1),
                    ft.Container(height=5),
                    ft.Text(
                        display_body,
                        size=14,
                    ),
                ],
                spacing=4,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=290,
            height=250,
        ),
        actions=actions,
    )
    page.show_dialog(dlg)
