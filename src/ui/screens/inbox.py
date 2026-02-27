"""
Inbox screen — game messages and news feed.
"""
from __future__ import annotations

import flet as ft

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar


def build_inbox_screen(page: ft.Page) -> ft.Column:
    """Build the inbox/messages content."""
    from src.ui.app import app_state, navigate

    # Set the navigation bar
    page.navigation_bar = build_nav_bar(page, 4)

    if not app_state.db_conn or not app_state.game_state:
        return ft.Column(controls=[ft.Text("No game loaded")])

    conn = app_state.db_conn
    messages = queries.get_inbox(conn, limit=30)

    cat_icons = {
        "match": ft.Icons.SPORTS_SOCCER,
        "media": ft.Icons.NEWSPAPER,
        "board": ft.Icons.ACCOUNT_BALANCE,
        "transfer": ft.Icons.ATTACH_MONEY,
        "general": ft.Icons.MAIL,
    }

    msg_tiles = []
    if not messages:
        msg_tiles.append(
            ft.Container(
                content=ft.Text(
                    "No messages yet.",
                    size=14, color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=40,
                alignment="center",
            )
        )
    else:
        for msg in messages:
            icon = cat_icons.get(msg.category, ft.Icons.MAIL)
            icon_color = ft.Colors.AMBER_300 if not msg.is_read else ft.Colors.GREY_600
            title_weight = ft.FontWeight.BOLD if not msg.is_read else ft.FontWeight.NORMAL
            new_badge = ft.Text(" NEW", size=9, color=ft.Colors.RED_400) if not msg.is_read else None

            def make_handler(mid=msg.id):
                def handler(e):
                    queries.mark_message_read(conn, mid)
                    navigate(page, "/inbox")  # Refresh
                return handler

            title_row = ft.Row(
                controls=[
                    ft.Text(msg.subject, size=13, weight=title_weight, expand=True),
                ],
                spacing=5,
            )
            if new_badge:
                title_row.controls.append(new_badge)

            msg_tiles.append(
                ft.ListTile(
                    leading=ft.Icon(icon, color=icon_color, size=22),
                    title=title_row,
                    subtitle=ft.Text(
                        f"{msg.date.strftime('%d %b')} — {msg.body[:70]}",
                        size=11, color=ft.Colors.GREY_400,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    on_click=make_handler(),
                )
            )

    return ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                padding=10,
                content=ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text("📧 Inbox", size=22, weight=ft.FontWeight.BOLD),
                        ft.Divider(height=1),
                        *msg_tiles,
                    ],
                ),
            ),
        ],
    )
