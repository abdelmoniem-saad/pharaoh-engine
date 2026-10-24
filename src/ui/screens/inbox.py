"""
Inbox screen — game messages with card-based mobile layout.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data import queries
from src.ui.widgets.nav_bar import build_nav_bar
from src.utils.localization import t, t_format


# Category styling
_CAT_COLORS = {
    "match": ft.Colors.GREEN_400,
    "media": ft.Colors.BLUE_400,
    "board": ft.Colors.PURPLE_400,
    "transfer": theme.ACCENT,
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
        return ft.Column(rtl=theme.rtl(), controls=[ft.Text(t("no_game_loaded"), rtl=theme.rtl())])

    conn = app_state.db_conn
    gs = app_state.game_state
    messages = queries.get_inbox(conn, limit=30)
    unread = queries.get_unread_count(conn)

    msg_tiles = []
    if not messages:
        msg_tiles.append(
            ft.Container(
                rtl=theme.rtl(), content=ft.Column(
                    rtl=theme.rtl(), horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.INBOX, rtl=theme.rtl(), size=48, color=theme.TEXT_MUTED),
                        ft.Container(rtl=theme.rtl(), height=8),
                        ft.Text(t("no_messages_yet"), rtl=theme.rtl(), size=theme.BODY_SIZE, color=theme.TEXT_SECONDARY),
                        ft.Text(t("play_matches_updates"),
                                rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_MUTED),
                    ],
                ),
                padding=40,
            )
        )
    else:
        for msg in messages:
            cat_color = _CAT_COLORS.get(msg.category, ft.Colors.GREY_400)
            cat_icon = _CAT_ICONS.get(msg.category, ft.Icons.MAIL)
            icon_color = cat_color if not msg.is_read else theme.TEXT_MUTED
            title_weight = ft.FontWeight.W_600 if not msg.is_read else ft.FontWeight.NORMAL
            bg = ft.Colors.with_opacity(0.04, ft.Colors.AMBER) if not msg.is_read else theme.CARD_BG

            def make_handler(m=msg):
                def handler(e):
                    _show_message_detail(page, conn, m)
                return handler

            # Badge for unread
            unread_badge = []
            if not msg.is_read:
                unread_badge.append(
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Text(t("new_label"), rtl=theme.rtl(), size=8, color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor=ft.Colors.RED_400,
                        padding=ft.padding.symmetric(horizontal=5, vertical=2),
                        border_radius=4,
                    )
                )

            msg_tiles.append(
                ft.Container(
                    rtl=theme.rtl(), content=ft.Row(
                        rtl=theme.rtl(), spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            # Category icon
                            ft.Container(
                                rtl=theme.rtl(), content=ft.Icon(cat_icon, rtl=theme.rtl(), size=18, color=icon_color),
                                width=36, height=36, border_radius=18,
                                bgcolor=ft.Colors.with_opacity(0.12, cat_color),
                                alignment=ft.Alignment(0, 0),
                            ),
                            # Content
                            ft.Column(rtl=theme.rtl(), spacing=2, expand=True, controls=[
                                ft.Row(rtl=theme.rtl(), spacing=4, tight=True, controls=[
                                    ft.Text(msg.subject, rtl=theme.rtl(), size=theme.BODY_SIZE, weight=title_weight,
                                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                            expand=True),
                                    *unread_badge,
                                ]),
                                ft.Text(
                                    f"{msg.date.strftime('%d %b')} — {msg.body}",
                                    rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                            ]),
                            # Chevron
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, rtl=theme.rtl(), size=16, color=theme.ACCENT),
                        ],
                    ),
                    padding=ft.padding.symmetric(horizontal=16, vertical=18),
                    border_radius=theme.CARD_RADIUS_SM,
                    bgcolor=theme.CARD_GLASS_STRONG if not msg.is_read else theme.CARD_GLASS,
                    border=theme.leading_border(cat_color, outline=True),
                    on_click=make_handler(),
                    ink=True,
                )
            )

    # Header controls
    header_extra = []
    if unread > 0:
        def mark_all_read(e):
            from src.ui.app import show_snackbar
            count = queries.mark_all_messages_read(conn)
            show_snackbar(page, f"✅ {t_format('messages_marked_read', n=count)}")
            navigate(page, "/inbox")

        header_extra.append(
            ft.TextButton(t("mark_all_read_btn"), rtl=theme.rtl(), icon=ft.Icons.DONE_ALL,
                          on_click=mark_all_read)
        )

    # Category filter chips
    active_filter = ["all"]
    msg_tiles_col = ft.Column(rtl=theme.rtl(), spacing=4, controls=msg_tiles)

    def _apply_filter(category):
        def handler(e):
            active_filter[0] = category
            msg_tiles_col.controls.clear()
            for msg in messages:
                if category != "all" and msg.category != category:
                    continue
                cat_color = _CAT_COLORS.get(msg.category, ft.Colors.GREY_400)
                cat_icon = _CAT_ICONS.get(msg.category, ft.Icons.MAIL)
                icon_color = cat_color if not msg.is_read else theme.TEXT_MUTED
                title_weight = ft.FontWeight.W_600 if not msg.is_read else ft.FontWeight.NORMAL

                def make_handler(m=msg):
                    def h(e):
                        _show_message_detail(page, conn, m)
                    return h

                unread_badge = []
                if not msg.is_read:
                    unread_badge.append(
                        ft.Container(
                            rtl=theme.rtl(), content=ft.Text(t("new_label"), rtl=theme.rtl(), size=8, color=ft.Colors.WHITE,
                                            weight=ft.FontWeight.BOLD),
                            bgcolor=ft.Colors.RED_400,
                            padding=ft.padding.symmetric(horizontal=5, vertical=2),
                            border_radius=4,
                        )
                    )

                msg_tiles_col.controls.append(
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Row(
                            rtl=theme.rtl(), spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Container(
                                    rtl=theme.rtl(), content=ft.Icon(cat_icon, rtl=theme.rtl(), size=18, color=icon_color),
                                    width=36, height=36, border_radius=18,
                                    bgcolor=ft.Colors.with_opacity(0.12, cat_color),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Column(rtl=theme.rtl(), spacing=2, expand=True, controls=[
                                    ft.Row(rtl=theme.rtl(), spacing=4, tight=True, controls=[
                                        ft.Text(msg.subject, rtl=theme.rtl(), size=theme.BODY_SIZE, weight=title_weight,
                                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                                expand=True),
                                        *unread_badge,
                                    ]),
                                    ft.Text(
                                        f"{msg.date.strftime('%d %b')} — {msg.body}",
                                        rtl=theme.rtl(), size=theme.CAPTION_SIZE, color=theme.TEXT_SECONDARY,
                                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ]),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, rtl=theme.rtl(), size=16, color=theme.ACCENT),
                            ],
                        ),
                        padding=ft.padding.symmetric(horizontal=16, vertical=18),
                        border_radius=theme.CARD_RADIUS_SM,
                        bgcolor=theme.CARD_GLASS_STRONG if not msg.is_read else theme.CARD_GLASS,
                        border=theme.leading_border(cat_color, outline=True),
                        on_click=make_handler(),
                        ink=True,
                    )
                )
            if not msg_tiles_col.controls:
                msg_tiles_col.controls.append(
                    ft.Text(t("no_messages_category"), rtl=theme.rtl(), size=12, color=theme.TEXT_SECONDARY))
            # Update chip styles
            for chip_cat, chip_ctrl in filter_chips:
                if chip_cat == category:
                    chip_ctrl.bgcolor = ft.Colors.with_opacity(0.15, theme.ACCENT)
                    chip_ctrl.border = ft.border.all(1, theme.ACCENT)
                else:
                    chip_ctrl.bgcolor = theme.CARD_GLASS
                    chip_ctrl.border = ft.border.all(1, theme.GOLD_BORDER)
            page.update()
        return handler

    # Build filter chip controls
    categories = ["all", "match", "board", "transfer", "media", "general"]
    cat_labels = {"all": t("all_filter"), "match": f"{t('match_filter')}", "board": f"{t('board_filter')}",
                  "transfer": f"{t('transfer_filter')}", "media": f"{t('media_filter')}", "general": f"{t('other_filter')}"}
    filter_chips = []
    for cat in categories:
        chip = ft.Container(
            rtl=theme.rtl(), content=ft.Text(cat_labels.get(cat, cat.title()), rtl=theme.rtl(), size=12,
                            weight=ft.FontWeight.W_500,
                            color=theme.ACCENT if cat == "all" else theme.TEXT_SECONDARY),
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            border_radius=12,
            bgcolor=ft.Colors.with_opacity(0.15, theme.ACCENT) if cat == "all" else theme.CARD_GLASS,
            border=ft.border.all(1, theme.ACCENT if cat == "all" else theme.GOLD_BORDER),
            on_click=_apply_filter(cat),
            ink=True,
        )
        filter_chips.append((cat, chip))

    filter_row = ft.Row(rtl=theme.rtl(), spacing=4, wrap=True,
                        controls=[c for _, c in filter_chips])

    return ft.Column(
        rtl=theme.rtl(), expand=True,
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.Container(
                rtl=theme.rtl(), padding=ft.padding.all(theme.PAGE_PADDING),
                content=ft.Column(
                    rtl=theme.rtl(), spacing=theme.SECTION_SPACING,
                    controls=[
                        theme.header_bar(
                            title=t("inbox"),
                            subtitle=f"{unread} {t('unread')}" if unread > 0 else t("all_caught_up"),
                            icon=ft.Icons.MAIL,
                            page=page,
                            extra_controls=header_extra,
                        ),
                        filter_row,
                        msg_tiles_col,
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
    actions = [ft.TextButton(t("close_btn"), rtl=theme.rtl(), on_click=close_handler)]
    display_body = msg.body

    if msg.category == "transfer" and "TRANSFER_OFFER|" in msg.body:
        # Parse transfer offer: TRANSFER_OFFER|player_id|from_club|to_club|fee|wage
        try:
            from src.ui.app import app_state
            gs = app_state.game_state
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
                show_snackbar(page, f"✅ {t_format('transfer_accepted', fee=f'{fee:,}')}")
                navigate(page, "/inbox")

            def decline_offer(e):
                if not msg.is_read:
                    queries.mark_message_read(conn, msg.id)
                page.pop_dialog()
                show_snackbar(page, f"❌ {t('offer_declined')}")
                navigate(page, "/inbox")

            actions = [
                ft.TextButton("❌ Decline", rtl=theme.rtl(), on_click=decline_offer),
                ft.ElevatedButton("✅ Accept", rtl=theme.rtl(), on_click=accept_offer),
            ]
        except (IndexError, ValueError):
            pass  # Not a valid offer format, show normally

    dlg = ft.AlertDialog(
        rtl=theme.rtl(), title=ft.Text(f"{cat_emoji} {msg.subject}", rtl=theme.rtl(), size=16,
                      weight=ft.FontWeight.BOLD, color=theme.GOLD),
        content=ft.Container(
            rtl=theme.rtl(), content=ft.Column(
                rtl=theme.rtl(), controls=[
                    ft.Container(
                        rtl=theme.rtl(), content=ft.Row(
                            rtl=theme.rtl(), alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(
                                    msg.date.strftime("%A, %d %B %Y"),
                                    rtl=theme.rtl(), size=11, color=ft.Colors.GREY_500,
                                ),
                                ft.Container(
                                    rtl=theme.rtl(), content=ft.Text(
                                        msg.category.title(),
                                        rtl=theme.rtl(), size=9, color=theme.ACCENT,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    padding=ft.padding.symmetric(horizontal=8, vertical=2),
                                    border_radius=6,
                                    bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.AMBER),
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        rtl=theme.rtl(), height=1,
                        bgcolor=ft.Colors.with_opacity(0.18, theme.GOLD),
                        margin=ft.margin.symmetric(vertical=4),
                    ),
                    ft.Container(rtl=theme.rtl(), height=3),
                    ft.Text(
                        display_body,
                        rtl=theme.rtl(), size=14,
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
