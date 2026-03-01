"""
Inbox screen — game messages with expandable detail view.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar


def build_inbox_screen(page: ft.Page) -> ft.Column:
    """Build the inbox/messages content."""
    from src.ui.app import app_state, navigate

    page.navigation_bar = build_nav_bar(page, 4)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    gs = app_state.game_state
    messages = queries.get_inbox(conn, limit=30)
    unread = queries.get_unread_count(conn)

    cat_icons = {
        "match": ft.Icons.SPORTS_SOCCER,
        "media": ft.Icons.NEWSPAPER,
        "board": ft.Icons.ACCOUNT_BALANCE,
        "transfer": ft.Icons.ATTACH_MONEY,
        "general": ft.Icons.MAIL,
    }
    cat_colors = {
        "match": ft.Colors.GREEN_400,
        "media": ft.Colors.BLUE_400,
        "board": ft.Colors.PURPLE_400,
        "transfer": ft.Colors.AMBER_400,
        "general": ft.Colors.GREY_400,
    }

    msg_tiles = []
    if not messages:
        msg_tiles.append(
            ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.INBOX, size=48, color=ft.Colors.GREY_600),
                        ft.Container(height=8),
                        ft.Text("No messages yet.", size=14, color=ft.Colors.GREY_500),
                        ft.Text("Play some matches to receive updates!",
                                size=12, color=ft.Colors.GREY_600),
                    ],
                ),
                padding=40,
                alignment=ft.Alignment(0, 0),
            )
        )
    else:
        for msg in messages:
            icon = cat_icons.get(msg.category, ft.Icons.MAIL)
            icon_color = cat_colors.get(msg.category, ft.Colors.GREY_400) if not msg.is_read else ft.Colors.GREY_700
            title_weight = ft.FontWeight.BOLD if not msg.is_read else ft.FontWeight.NORMAL
            bg_color = ft.Colors.with_opacity(0.05, ft.Colors.AMBER) if not msg.is_read else None

            def make_handler(m=msg):
                def handler(e):
                    _show_message_detail(page, conn, m)
                return handler

            title_controls = [
                ft.Text(msg.subject, size=13, weight=title_weight, expand=True),
            ]
            if not msg.is_read:
                title_controls.append(
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
                    content=ft.ListTile(
                        leading=ft.Icon(icon, color=icon_color, size=22),
                        title=ft.Row(controls=title_controls, spacing=5),
                        subtitle=ft.Text(
                            f"{msg.date.strftime('%d %b')} — {msg.body}",
                            size=11, color=ft.Colors.GREY_400,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        on_click=make_handler(),
                    ),
                    bgcolor=bg_color,
                    border_radius=4,
                )
            )

    # Header with unread count
    header_controls = [
        ft.Text("📥 Inbox", size=22, weight=ft.FontWeight.BOLD, expand=True),
    ]
    if unread > 0:
        header_controls.append(
            ft.Container(
                content=ft.Text(f"{unread} unread", size=11,
                                color=ft.Colors.AMBER_300, weight=ft.FontWeight.W_500),
                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.AMBER),
            )
        )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=15,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(controls=header_controls),
                        ft.Divider(height=1),
                        *msg_tiles,
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
                                         fee=fee, wage=wage)
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
            width=320,
            height=250,
        ),
        actions=actions,
    )
    page.show_dialog(dlg)
