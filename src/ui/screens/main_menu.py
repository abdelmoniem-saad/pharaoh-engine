"""
Main Menu screen — New Game, Continue, Settings.
"""
from __future__ import annotations

import flet as ft
from src.ui import theme

from src.data.models import Club
from src.data.database import SAVE_SLOTS, connect, delete_save, peek_save_info
from src.data.seed import seed_database
from src.data import queries
from src.core.league import create_league_season
from src.utils import rng
from src.utils.config import APP_VERSION, expectation_display
from src.utils.localization import t, t_format, display_name
from src.utils.logging_util import get_logger

log = get_logger("ui")


def build_main_menu(page: ft.Page) -> ft.Column:
    """Build the main menu content."""

    # One-time upgrade: surface a legacy default.db career as Slot 1.
    from src.data.database import migrate_legacy_default_slot
    migrate_legacy_default_slot()

    def new_game_click(e):
        _show_new_game_slot_dialog(page)

    def continue_click(e):
        _continue_game(page)

    def settings_click(e):
        from src.ui.app import navigate
        navigate(page, "/settings")

    # No navigation bar on main menu
    page.navigation_bar = None

    # Title block
    title_block = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=4,
        controls=[
            ft.Container(
                content=ft.Icon(ft.Icons.SHIELD, size=56, color=theme.GOLD),
                width=80, height=80, border_radius=40,
                bgcolor=ft.Colors.with_opacity(0.10, theme.GOLD),
                alignment=ft.Alignment(0, 0),
                shadow=ft.BoxShadow(
                    spread_radius=2, blur_radius=20,
                    color=ft.Colors.with_opacity(0.15, theme.GOLD),
                ),
            ),
            ft.Container(height=8),
            ft.Text(
                t("app_title").upper(),
                size=34, weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.CENTER,
                color=theme.GOLD,
            ),
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Container(width=30, height=1, bgcolor=theme.GOLD_BORDER_STRONG),
                        ft.Text("⚽", size=12),
                        ft.Container(width=30, height=1, bgcolor=theme.GOLD_BORDER_STRONG),
                    ],
                ),
            ),
            ft.Text(
                t("egyptian_football_manager"),
                size=15,
                color=theme.TEXT_SECONDARY,
                text_align=ft.TextAlign.CENTER,
                italic=True,
            ),
        ],
    )

    if theme.current_theme() == "supporter":
        from src.utils.localization import is_rtl
        title_block = ft.Container(
            padding=24, margin=ft.margin.symmetric(horizontal=20),
            bgcolor=theme.BG_SURFACE, border_radius=theme.CARD_RADIUS,
            border=ft.border.only(top=ft.BorderSide(4, theme.SECONDARY_ACCENT)),
            content=ft.Column(spacing=14, horizontal_alignment=ft.CrossAxisAlignment.START, controls=[
                ft.Text("موسمك. ناديك. حكايتك." if is_rtl() else "YOUR CLUB. YOUR SEASON.",
                        size=12, weight=ft.FontWeight.BOLD, color=theme.SECONDARY_ACCENT),
                ft.Text(t("app_title"), size=34, weight=ft.FontWeight.W_900,
                        color=theme.TEXT_PRIMARY),
                ft.Text("من المدرج لدكة المدير الفني" if is_rtl() else "From the stands to the touchline.",
                        size=19, weight=ft.FontWeight.BOLD, color=theme.GOLD),
                ft.Text(t("egyptian_football_manager"), size=14, color=theme.TEXT_SECONDARY),
            ]),
        )

    # Buttons
    button_block = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        controls=[
            ft.ElevatedButton(
                "⚽  " + t("new_game"),
                width=280, height=56,
                style=theme.PRIMARY_BTN_STYLE,
                on_click=new_game_click,
            ),
            ft.ElevatedButton(
                "📂  " + t("continue_game"),
                width=280, height=52,
                style=theme.SECONDARY_BTN_STYLE,
                on_click=continue_click,
            ),
            ft.OutlinedButton(
                "⚙️  " + t("settings"),
                width=280, height=48,
                style=ft.ButtonStyle(
                    color=theme.TEXT_SECONDARY,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    side=ft.BorderSide(1, theme.GOLD_BORDER),
                ),
                on_click=settings_click,
            ),
        ],
    )

    return ft.Column(
        expand=True,
        controls=[
            ft.Container(
                expand=True,
                gradient=theme.gradient_bg(
                    colors=[theme.BG_DARK, theme.BG_MID, theme.BG_MID, theme.BG_TEAL],
                ),
                padding=0,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    controls=[
                        ft.Container(expand=2),
                        title_block,
                        ft.Container(expand=1),
                        button_block,
                        ft.Container(expand=2),
                        ft.Text(
                            f"v{APP_VERSION}",
                            size=11, color=theme.TEXT_MUTED,
                        ),
                        ft.Container(height=16),
                    ],
                ),
            ),
        ],
    )


# ── Multi-Slot Save System ──────────────────────────────────────────────────

def _slot_badge(i: int) -> ft.Container:
    """Small golden circular badge showing the slot number."""
    return ft.Container(
        content=ft.Text(str(i), size=11, weight=ft.FontWeight.BOLD,
                        color=theme.BG_DARK, text_align=ft.TextAlign.CENTER),
        width=24, height=24, border_radius=12, bgcolor=theme.GOLD,
        alignment=ft.Alignment(0, 0),
    )


def _confirm_overwrite_then(page: ft.Page, slot: str, info: dict, on_yes):
    """Ask for confirmation before replacing an occupied slot, then run on_yes."""
    club = info.get("user_club_name") or "?"
    manager = info.get("manager_name") or "Manager"

    def _yes(e):
        page.pop_dialog()
        on_yes()

    page.show_dialog(ft.AlertDialog(
        title=ft.Text("⚠️ " + t("overwrite_confirm_title")),
        content=ft.Text(t_format("overwrite_confirm_msg",
                                manager=manager, club=club)),
        actions=[
            ft.TextButton(t("cancel"), on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton(t("confirm"), on_click=_yes),
        ],
    ))


def _show_new_game_slot_dialog(page: ft.Page):
    """Let the player choose which career slot to start the new game in."""

    tiles = []
    for i, slot in enumerate(SAVE_SLOTS, start=1):
        info = peek_save_info(slot)

        if info is None:
            title_line = t_format("slot_label", n=i)
            sub_rows = [ft.Text(t("empty_slot"), size=11,
                                color=theme.TEXT_SECONDARY)]

            def on_pick(e, s=slot):
                page.pop_dialog()
                _show_manager_name_dialog(page, s)
        else:
            year = int(info.get("season_year") or 2025)
            club_nm = info.get("user_club_name") or "?"
            mgr = info.get("manager_name") or "Manager"
            title_line = club_nm
            sub_rows = [
                ft.Row(spacing=4, tight=True, controls=[
                    ft.Text("👤", size=10),
                    ft.Text(f"{t('manager_label')}: {mgr}",
                            size=11, color=theme.TEXT_SECONDARY, expand=True,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS),
                ]),
                ft.Row(spacing=4, tight=True, controls=[
                    ft.Text("📅", size=10),
                    ft.Text(f"{t('season_short')} {year}/{year + 1}",
                            size=11, color=theme.TEXT_SECONDARY),
                ]),
            ]

            def on_pick(e, s=slot, inf=info):
                page.pop_dialog()
                _confirm_overwrite_then(
                    page, s, inf,
                    lambda s=s: _show_manager_name_dialog(page, s))

        tiles.append(ft.ListTile(
            leading=_slot_badge(i),
            title=ft.Text(title_line,
                          weight=ft.FontWeight.W_600, color=theme.GOLD,
                          max_lines=1,
                          overflow=ft.TextOverflow.ELLIPSIS),
            subtitle=ft.Column(spacing=1, controls=sub_rows),
            on_click=on_pick,
        ))

    page.show_dialog(ft.AlertDialog(
        bgcolor=theme.BG_MID,
        title=ft.Text("🆕 " + t("save_slots"), color=theme.GOLD,
                      weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(controls=tiles, spacing=4, tight=True),
            width=340,
        ),
        actions=[ft.TextButton(t("cancel"),
                               on_click=lambda e: page.pop_dialog())],
    ))


def _show_load_game_dialog(page: ft.Page):
    """List all career slots and let the player load or delete one."""

    tiles = []
    any_save = False

    for i, slot in enumerate(SAVE_SLOTS, start=1):
        info = peek_save_info(slot)

        if info:
            any_save = True
            year = int(info.get("season_year") or 2025)
            club_nm = info.get("user_club_name") \
                or info.get("manager_name") or t("load")
            mgr = info.get("manager_name") or "Manager"

            def _load(e, s=slot):
                page.pop_dialog()
                _load_slot(page, s)

            def _ask_delete(e, s=slot):
                page.pop_dialog()
                _confirm_delete_slot(page, s)

            tiles.append(ft.ListTile(
                leading=_slot_badge(i),
                title=ft.Text(club_nm, size=14,
                              weight=ft.FontWeight.W_600,
                              max_lines=1,
                              overflow=ft.TextOverflow.ELLIPSIS),
                subtitle=ft.Column(
                    spacing=1,
                    controls=[
                        ft.Row(spacing=4, tight=True, controls=[
                            ft.Text("👤", size=10),
                            ft.Text(f"{t('manager_label')}: {mgr}",
                                    size=11, color=theme.TEXT_MUTED, expand=True,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                        ]),
                        ft.Row(spacing=4, tight=True, controls=[
                            ft.Text("📅", size=10),
                            ft.Text(f"{t('season_short')} {year}/{year + 1}",
                                    size=11, color=theme.TEXT_MUTED),
                        ]),
                    ],
                ),
                trailing=ft.IconButton(ft.Icons.DELETE_OUTLINE,
                                       icon_size=16,
                                       icon_color="#EF5350",
                                       tooltip=t("delete_save"),
                                       on_click=_ask_delete),
                on_click=_load,
            ))
        else:
            tiles.append(ft.ListTile(
                disabled=True,
                leading=_slot_badge(i),
                title=ft.Text(t_format("slot_label", n=i), color=theme.TEXT_MUTED),
                subtitle=ft.Text(t("empty_slot"), size=12, color=theme.TEXT_MUTED),
            ))

    if not any_save:
        tiles.insert(0, ft.Container(
            content=ft.Text(t("no_saves_yet"), size=13,
                            color=theme.TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            padding=10,
        ))

    page.show_dialog(ft.AlertDialog(
        bgcolor=theme.BG_MID,
        title=ft.Text("📂 " + t("load_game"), color=theme.GOLD,
                      weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.Column(controls=tiles, spacing=4,
                              scroll=ft.ScrollMode.AUTO),
            width=350,
        ),
        actions=[ft.TextButton(t("cancel"),
                               on_click=lambda e: page.pop_dialog())],
    ))


def _confirm_delete_slot(page: ft.Page, slot: str) -> None:
    """Confirm deletion of a career slot (an automatic backup is kept)."""

    def do_delete(e):
        delete_save(slot)
        log.info("Deleted save slot '%s'", slot)
        page.pop_dialog()
        _show_load_game_dialog(page)  # refresh list

    page.show_dialog(ft.AlertDialog(
        title=ft.Text("🗑️ " + t("delete_save") + "?"),
        content=ft.Text(t("delete_save_confirm")),
        actions=[
            ft.TextButton(t("cancel"),
                          on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton(t("delete"), on_click=do_delete),
        ],
    ))


def _show_manager_name_dialog(page: ft.Page, save_name: str = "slot1"):
    """Show a dialog to enter the manager name before club selection."""

    name_field = ft.TextField(
        label=t("manager_name"),
        value="",
        hint_text=t("enter_your_name"),
        width=280,
        autofocus=True,
        text_size=16,
    )

    def on_confirm(e):
        manager_name = name_field.value.strip() if name_field.value else "Manager"
        if not manager_name:
            manager_name = "Manager"
        page.pop_dialog()
        _show_club_selection(page, manager_name, save_name)

    dlg = ft.AlertDialog(
        title=ft.Text("👤 " + t("your_identity"), color=theme.GOLD),
        content=ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(t("what_should_board_call_you"),
                            size=13, color=theme.TEXT_SECONDARY),
                    ft.Container(height=10),
                    name_field,
                ],
                spacing=5,
                tight=True,
            ),
            width=300,
            height=120,
        ),
        actions=[
            ft.TextButton(t("cancel"), on_click=lambda e: page.pop_dialog()),
            ft.ElevatedButton(t("confirm") + " ➡️", on_click=on_confirm,
                              style=ft.ButtonStyle(bgcolor=theme.ACCENT_DARK,
                                                    color=ft.Colors.WHITE,
                                                    shape=ft.RoundedRectangleBorder(radius=10))),
        ],
    )
    page.show_dialog(dlg)


def _show_club_selection(page: ft.Page, manager_name: str,
                         save_name: str = "slot1"):
    """Create a new game in *save_name*, then show club selection dialog.

    Seeding is CPU-heavy, so it runs on a worker thread behind a busy overlay
    instead of freezing the UI.
    """
    from src.ui.app import app_state, run_busy_task

    holder: dict = {}

    def build_career():
        delete_save(save_name)  # keeps an automatic pre-delete backup
        conn = connect(save_name)
        game_state = seed_database(conn, game_seed=rng.randint(1, 999999))
        game_state.manager_name = manager_name
        try:
            game_state.save_name = save_name
        except Exception:
            pass
        app_state.current_save_name = save_name
        holder["conn"] = conn
        holder["game_state"] = game_state

    def done(error):
        if error is not None or "conn" not in holder:
            page.show_dialog(ft.AlertDialog(
                title=ft.Text("⚠️ Could not create a new game"),
                content=ft.Text(
                    "Something went wrong while setting up your career.\n"
                    "Your previous save (if any) was backed up automatically."
                ),
                actions=[ft.TextButton("OK",
                                       on_click=lambda e: page.pop_dialog())],
            ))
            return
        _open_club_picker(page, holder["conn"], holder["game_state"])

    run_busy_task(page, "⚽ Creating new career…", build_career, on_done=done)


def _open_club_picker(page: ft.Page, conn, game_state):
    """Build and open the club-selection dialog for a freshly created career."""
    from src.ui.app import app_state, navigate, show_snackbar

    # Generate league fixtures
    clubs = queries.get_all_clubs(conn)
    create_league_season(conn, clubs, game_state.season_year)

    # Build club list
    club_buttons = []
    for club in clubs:
        def make_handler(c=club):
            def handler(e):
                _select_club(page, conn, game_state, c, dlg)
            return handler

        # Color indicator dot
        club_buttons.append(
            ft.ListTile(
                leading=ft.Container(
                    width=32, height=32,
                    bgcolor=club.primary_color,
                    border_radius=16,
                    content=ft.Icon(ft.Icons.SPORTS_SOCCER, size=16, color=ft.Colors.WHITE),
                ),
                title=ft.Text(display_name(club), weight=ft.FontWeight.W_500),
                subtitle=ft.Text(
                    f"{club.city} — ⭐ {club.reputation} — 🎯 {expectation_display(club.season_expectation)}",
                    size=12, color=ft.Colors.GREY_400,
                ),
                on_click=make_handler(),
            )
        )

    dlg = ft.AlertDialog(
        title=ft.Text("🏟️ " + t("choose_your_club"),
                       color=theme.GOLD, weight=ft.FontWeight.BOLD),
        content=ft.Container(
            content=ft.ListView(
                controls=club_buttons,
                spacing=2,
            ),
            width=300,
            height=450,
        ),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.pop_dialog()),
        ],
    )
    page.show_dialog(dlg)


def _select_club(page: ft.Page, conn, game_state, club: Club, dlg: ft.AlertDialog):
    """Handle club selection."""
    from src.ui.app import app_state, navigate, show_snackbar
    from src.data.database import get_active_save_name

    game_state.user_club_id = club.id
    game_state.user_club_name = club.name
    game_state.user_club_name_ar = club.name_ar
    queries.save_game_state(conn, game_state)

    active_slot = get_active_save_name()
    if active_slot:
        app_state.current_save_name = active_slot

    # Mark club as user controlled
    if club:
        club.is_user_controlled = True
        queries.update_club(conn, club)

        # Send initial board objectives message
        from src.core.board import generate_season_objectives
        from src.data.models import InboxMessage
        from datetime import date
        objectives = generate_season_objectives(club)
        exp_name = expectation_display(club.season_expectation)
        obj_text = "\n".join(f"• {o.description} ({o.priority})" for o in objectives)
        queries.insert_message(conn, InboxMessage(
            date=date(2025, 8, 15),
            subject="📋 " + t("board_objectives"),
            body=(
                f"Welcome, {game_state.manager_name}!\n\n"
                f"The board expects you to achieve the following this season:\n\n"
                f"🎯 Season Target: {exp_name}\n\n{obj_text}\n\n"
                f"Good luck!"
            ),
            category="board",
        ))

    # Apply menu preferences to a newly created career.
    from src.utils.prefs import get_pref
    from src.ui.screens.settings import _save_settings
    defaults = {"match_speed": 3, "auto_save": 1, "auto_save_interval": 7, "difficulty": "normal"}
    defaults.update(get_pref("gameplay_defaults", {}))
    _save_settings(conn, defaults)

    # Store in shared state
    app_state.db_conn = conn
    app_state.game_state = game_state

    # Ensure Cup is initialized (it might have failed in seed_database due to FKs)
    try:
        from src.core.competition import ensure_cup_initialized
        if ensure_cup_initialized(conn, game_state):
            log.info("Egypt Cup initialized during club selection.")
    except Exception:
        log.exception("Cup initialization failed during club selection")

    page.pop_dialog()
    navigate(page, "/match_day")
    show_snackbar(page, f"🎉 Welcome to {display_name(club)}, {game_state.manager_name}!")

    # ── First-Time Manager Tutorial Overlay ──
    from src.ui.app import show_tutorial_overlay
    show_tutorial_overlay(page)


def _load_slot(page: ft.Page, save_name: str):
    """Load an existing career from a specific slot."""
    from src.ui.app import app_state, navigate, show_snackbar

    try:
        conn = connect(save_name)
        game_state = queries.load_game_state(conn)
        if game_state:
            app_state.db_conn = conn
            app_state.game_state = game_state
            app_state.current_save_name = save_name

            # Repair/Ensure Cup (for existing saves after schema update)
            try:
                from src.core.competition import ensure_cup_initialized
                if ensure_cup_initialized(conn, game_state):
                    log.info("Egypt Cup repaired/initialized successfully.")
            except Exception:
                log.exception("Cup repair failed on load")

            navigate(page, "/squad")
            show_snackbar(page, f"📂 Welcome back, {game_state.manager_name}!")
        else:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text(t("no_save_found")),
                    content=ft.Text(t("no_save_found_msg")),
                    actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
                )
            )
    except Exception as e:
        log.exception("Failed to load save '%s'", save_name)
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("⚠️ Couldn't load your save"),
                content=ft.Text(
                    f"The save file couldn't be loaded ({e}).\n\n"
                    "It may be corrupted — automatic backup copies are kept "
                    "in the saves/backups folder and can be restored manually."
                ),
                actions=[ft.TextButton("OK", on_click=lambda e: page.pop_dialog())],
            )
        )


def _continue_game(page: ft.Page):
    """Open the slot picker; loads straight away when only one career exists."""
    infos = [peek_save_info(s) for s in SAVE_SLOTS]
    occupied = [(s, i) for s, i in zip(SAVE_SLOTS, infos) if i]
    if len(occupied) == 1:
        _load_slot(page, occupied[0][0])
        return
    _show_load_game_dialog(page)
