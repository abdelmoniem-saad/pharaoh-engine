"""Settings expose only working controls and save changes immediately."""
from __future__ import annotations
import logging
import flet as ft
from src.ui import theme
from src.utils.localization import get_language, set_language, is_rtl, t
from src.utils.prefs import get_pref, set_pref
from src.ui.widgets.cards import section_card, kv_row

log = logging.getLogger(__name__)


def build_settings_screen(page):
    from src.ui.app import app_state, navigate, show_snackbar
    page.navigation_bar = None
    conn = app_state.db_conn
    active = bool(conn and app_state.game_state and app_state.current_save_name)
    settings = _load_settings(conn) if conn else get_pref("gameplay_defaults", {})
    status = ft.Text(t("settings_apply_immediately"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED)

    def persist_speed(e):
        previous = settings.get("match_speed", 3)
        updated = {"match_speed": int(e.control.value or 3),
                   "auto_save": settings.get("auto_save", 1),
                   "auto_save_interval": settings.get("auto_save_interval", 7),
                   "difficulty": settings.get("difficulty", "normal")}
        try:
            if conn:
                _save_settings(conn, updated)
            set_pref("gameplay_defaults", updated)
            settings.update(updated)
            status.value, status.color = t("settings_saved"), theme.TEXT_SUCCESS
        except Exception as ex:
            log.warning("Settings save failed: %a", ex)
            e.control.value = str(previous)
            status.value, status.color = t("settings_save_failed"), theme.TEXT_DANGER
        page.update()

    def change_language(e):
        language = e.control.value or "en"
        # Store before rebuilding so a change cannot discard other edits.
        if conn:
            conn.execute("INSERT OR IGNORE INTO game_settings (id) VALUES (1)")
            conn.execute("UPDATE game_settings SET language=? WHERE id=1", (language,))
            conn.commit()
        set_pref("language", language)
        set_language(language)
        page.rtl = is_rtl()
        theme.apply_to_page(page)
        navigate(page, "/settings")

    def change_theme(e):
        theme.configure(e.control.value)
        set_pref("ui_theme", theme.current_theme())
        theme.apply_to_page(page)
        navigate(page, "/settings")

    def backup(e):
        from src.data.database import backup_save
        from src.data import queries
        try:
            queries.save_game_state(conn, app_state.game_state)
            path = backup_save(app_state.current_save_name, label="manual")
        except Exception as ex:
            log.warning("Backup failed: %a", ex)
            path = None
        show_snackbar(page, t("backup_created") if path else t("backup_failed"),
                      bgcolor=theme.TEXT_SUCCESS if path else theme.TEXT_DANGER)

    def delete_click(e):
        slot = app_state.current_save_name
        def confirm(e):
            from src.data.database import delete_save
            page.pop_dialog()
            delete_save(slot)
            app_state.db_conn = None
            app_state.game_state = None
            app_state.current_save_name = None
            navigate(page, "/")
            show_snackbar(page, t("save_deleted"))
        page.show_dialog(ft.AlertDialog(rtl=theme.rtl(),
            title=ft.Text(t("delete_save"), rtl=theme.rtl()),
            content=ft.Text(t("delete_active_career_confirm").format(slot=slot), rtl=theme.rtl()),
            actions=[ft.TextButton(t("cancel"), rtl=theme.rtl(), on_click=lambda e: page.pop_dialog()),
                     ft.TextButton(t("delete"), rtl=theme.rtl(), style=theme.DANGER_BTN_STYLE, on_click=confirm)]))

    language = ft.RadioGroup(rtl=theme.rtl(), value=get_language(), on_change=change_language,
        content=ft.Row(rtl=theme.rtl(), wrap=True, spacing=20, controls=[
            ft.Radio(rtl=False, value="en", label="English"),
            ft.Radio(rtl=True, value="ar", label="العربية"),
        ]))
    appearance = ft.RadioGroup(rtl=theme.rtl(), value=theme.current_theme(), on_change=change_theme,
        content=ft.Column(rtl=theme.rtl(), spacing=10, controls=[
            ft.Container(rtl=theme.rtl(), padding=12, border_radius=12,
                bgcolor=theme.BG_DARK, border=ft.border.all(1,theme.ACCENT if key==theme.current_theme() else theme.GOLD_BORDER),
                content=ft.Row(rtl=theme.rtl(), controls=[
                    ft.Radio(rtl=theme.rtl(), value=key, label=names[1 if is_rtl() else 0], expand=True),
                    *[ft.Container(rtl=theme.rtl(), width=16, height=24, border_radius=4, bgcolor=color)
                      for color in (("#202833", "#DDC08A") if key=="classic" else ("#69C5DD", "#FFAC7A"))],
                ])) for key,names in theme.THEME_NAMES.items()]))
    speed = ft.Dropdown(rtl=theme.rtl(), label=t("match_speed"), value=str(settings.get("match_speed",3)),
        border_radius=10, border_color=theme.GOLD_BORDER, focused_border_color=theme.ACCENT,
        filled=True, fill_color=theme.BG_DARK, on_select=persist_speed,
        options=[ft.dropdown.Option(str(i), text=t(key)) for i,key in
                 [(1,"slow"),(2,"normal"),(3,"fast"),(4,"very_fast"),(5,"instant")]])
    sections = [
        theme.header_bar(t("settings"), subtitle=t("settings_personalize"), page=page,
            back_route="/squad" if app_state.game_state else "/", show_notification_bell=False),
        status,
        section_card(t("language"), [language, ft.Text(t("language_help"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED)]),
        section_card(t("appearance"), [appearance]),
        section_card(t("match_playback"), [speed, ft.Text(t("playback_help"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED)]),
    ]
    if active:
        sections.append(section_card(t("your_career"), [
            kv_row(t("team"), app_state.game_state.user_club_name_ar if is_rtl() and app_state.game_state.user_club_name_ar else app_state.game_state.user_club_name),
            ft.Text(t("progress_saved_help"), rtl=theme.rtl(), size=13, color=theme.TEXT_SECONDARY),
            ft.OutlinedButton(t("create_backup"), rtl=theme.rtl(), icon=ft.Icons.SAVE_ALT, height=46, on_click=backup),
        ]))
    sections.append(section_card(t("about_game"), [
        ft.Text("Pharaoh Engine · 0.3.0", rtl=False, size=14, color=theme.TEXT_PRIMARY),
        ft.Text(t("supporter_concept_note"), rtl=theme.rtl(), size=12, color=theme.TEXT_MUTED),
    ]))
    if active:
        sections.append(ft.ExpansionTile(rtl=theme.rtl(), title=ft.Text(t("manage_career"), rtl=theme.rtl(), color=theme.TEXT_MUTED),
            controls=[ft.TextButton(t("delete_save"), rtl=theme.rtl(), style=theme.DANGER_BTN_STYLE, on_click=delete_click)]))
    return ft.Column(rtl=theme.rtl(), expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(rtl=theme.rtl(), padding=theme.PAGE_PADDING,
            content=ft.Column(rtl=theme.rtl(), spacing=24, controls=sections))])


def _load_settings(conn) -> dict:
    try:
        # Ensure a settings row exists
        conn.execute("INSERT OR IGNORE INTO game_settings (id) VALUES (1)")
        conn.commit()
        row = conn.execute("SELECT * FROM game_settings WHERE id = 1").fetchone()
        if row:
            d = dict(
                match_speed=row["match_speed"],
                auto_save=row["auto_save"],
                auto_save_interval=row["auto_save_interval"],
                difficulty=row["difficulty"],
                # sound_enabled=row["sound_enabled"] if "sound_enabled" in row.keys() else 1,  # [SOUND DISABLED]
            )
            return d
    except Exception as ex:
        log.warning("Settings load failed: %a", ex)
    return {}


def _save_settings(conn, s: dict) -> None:
    try:
        from src.utils.localization import get_language
        lang = get_language()
        conn.execute("INSERT OR IGNORE INTO game_settings (id) VALUES (1)")
        conn.execute("""UPDATE game_settings SET
            match_speed=?, auto_save=?, auto_save_interval=?, difficulty=?, language=?
            WHERE id=1
        """, (s["match_speed"], s["auto_save"], s["auto_save_interval"], s["difficulty"], lang))
        conn.commit()
    except Exception as ex:
        log.warning("Settings save failed: %a", ex)
        raise
