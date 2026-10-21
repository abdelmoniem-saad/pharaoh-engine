"""
Settings screen -- match speed, difficulty, auto-save, language.
"""
from __future__ import annotations
import logging
import flet as ft
from src.ui import theme

log = logging.getLogger(__name__)


def build_settings_screen(page: ft.Page) -> ft.Column:
    from src.ui.app import app_state, navigate, show_snackbar
    from src.utils.localization import get_language, set_language, is_rtl, t
    # from src.utils.audio import set_audio_enabled  # [SOUND DISABLED]

    page.navigation_bar = None

    # Opening Settings must not manufacture a blank legacy career.
    from src.utils.prefs import get_pref, set_pref
    conn = app_state.db_conn
    settings = _load_settings(conn) if conn else get_pref("gameplay_defaults", {})
    match_speed = settings.get("match_speed", 3)
    auto_save = settings.get("auto_save", 1)
    auto_save_interval = settings.get("auto_save_interval", 7)
    difficulty = settings.get("difficulty", "normal")
    # sound_enabled = settings.get("sound_enabled", 1)  # [SOUND DISABLED]

    speed_dd = ft.Dropdown(
        label=t("match_speed"), value=str(match_speed), expand=True,
        options=[ft.dropdown.Option(str(i), text=f"{i} - {t(n)}")
                 for i, n in [(1, "slow"), (2, "normal"), (3, "fast"), (4, "very_fast"), (5, "instant")]],
    )
    diff_dd = ft.Dropdown(
        label=t("difficulty"), value=difficulty, expand=True,
        options=[ft.dropdown.Option(k, text=t(k)) for k in ("easy", "normal", "hard")],
    )
    auto_save_switch = ft.Switch(label=t("auto_save"), value=bool(auto_save))
    # sound_switch = ft.Switch(label="Sound Effects", value=bool(sound_enabled))  # [SOUND DISABLED]
    interval_dd = ft.Dropdown(
        label=t("auto_save_interval"), value=str(auto_save_interval), expand=True,
        options=[ft.dropdown.Option(str(d), text=t("every_n_days").format(days=d)) for d in (3, 7, 14, 30)],
    )

    def save_click(e):
        s = {
            "match_speed": int(speed_dd.value or 3),
            "auto_save": 1 if auto_save_switch.value else 0,
            "auto_save_interval": int(interval_dd.value or 7),
            "difficulty": diff_dd.value or "normal",
            # "sound_enabled": 1 if sound_switch.value else 0,  # [SOUND DISABLED]
        }
        set_pref("gameplay_defaults", s)
        if conn:
            _save_settings(conn, s)
        # set_audio_enabled(bool(sound_switch.value))  # [SOUND DISABLED]
        show_snackbar(page, "✅ " + t("settings_saved"))

    def go_back(e):
        navigate(page, "/squad" if app_state.game_state else "/")

    def delete_save_click(e):
        def confirm_delete(e2):
            from src.data.database import delete_save
            active_slot = app_state.current_save_name or "slot1"
            page.pop_dialog()
            app_state.db_conn = None
            app_state.game_state = None
            delete_save(active_slot)
            navigate(page, "/")
            show_snackbar(page, f"🗑️ {t('save_deleted')}")

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"⚠️ {t('delete_save')}?"),
            content=ft.Text(t("delete_save_confirm")),
            actions=[
                ft.TextButton(t("cancel"), on_click=lambda e2: page.pop_dialog()),
                ft.ElevatedButton(t("delete"), on_click=confirm_delete,
                    style=theme.DANGER_BTN_STYLE),
            ],
        ))

    controls_list = [
        theme.header_bar(
            title=t("settings"),
            icon=ft.Icons.SETTINGS,
            page=page,
            back_route="/squad" if app_state.game_state else "/",
        ),

        # Gameplay section
        theme.glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("🎮 " + t("gameplay"), size=16, weight=ft.FontWeight.W_600, color=theme.GOLD),
                speed_dd,
                diff_dd,
            ]),
        ),

        # Save section
        theme.glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("💾 " + t("save"), size=16, weight=ft.FontWeight.W_600, color=theme.GOLD),
                auto_save_switch,
                interval_dd,
                # sound_switch,  # [SOUND DISABLED]
            ]),
        ),
    ]

    # Appearance is app-wide and independent of career saves.
    from src.utils.prefs import set_pref

    def on_theme_change(e):
        theme.configure(e.control.value)
        set_pref("ui_theme", theme.current_theme())
        theme.apply_to_page(page)
        navigate(page, "/settings")

    appearance = ft.RadioGroup(
        value=theme.current_theme(), on_change=on_theme_change,
        content=ft.Column(controls=[
            ft.Radio(value=key, label=names[1 if is_rtl() else 0])
            for key, names in theme.THEME_NAMES.items()
        ]),
    )
    controls_list.insert(1, theme.glass_card(ft.Column(spacing=10, controls=[
        ft.Text("المظهر" if is_rtl() else "Appearance", size=18,
                weight=ft.FontWeight.BOLD, color=theme.GOLD),
        appearance,
        ft.Text("المدرج: تصور مستوحى من ألوان ارزع، بدون شعار أو شراكة رسمية."
                if is_rtl() else "Supporter: an Erza3-inspired concept. No logo or official partnership.",
                size=12, color=theme.TEXT_SECONDARY),
    ])))

    # Language section — use RadioGroup for reliable on_change
    current_lang = get_language()

    def on_lang_change(e):
        new_lang = e.control.value or "en"
        set_language(new_lang)
        set_pref("language", new_lang)
        # Persist to DB
        if conn:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO game_settings (id) VALUES (1)"
                )
                conn.execute(
                    "UPDATE game_settings SET language=? WHERE id=1", (new_lang,)
                )
                conn.commit()
            except Exception as ex:
                log.warning("Language save failed: %a", ex)
        # Toggle RTL
        page.rtl = is_rtl()
        # Rebuild the screen with new language labels
        navigate(page, "/settings")

    lang_radio = ft.RadioGroup(
        value=current_lang,
        on_change=on_lang_change,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Radio(value="en", label="🇬🇧 English"),
                ft.Radio(value="ar", label="🇪🇬 العربية"),
            ],
        ),
    )

    controls_list.append(
        theme.glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("🌍 " + t("language"), size=16, weight=ft.FontWeight.W_600, color=theme.GOLD),
                lang_radio,
                ft.Text(
                    t("language_help"),
                    size=11, color=theme.TEXT_MUTED, italic=True,
                ),
            ]),
        ),
    )

    controls_list.extend([
        ft.Container(height=10),
        ft.ElevatedButton("💾 " + t("save") + " " + t("settings"), width=280, height=48,
            style=theme.PRIMARY_BTN_STYLE,
            on_click=save_click),
        ft.Container(height=16),

        # Danger zone
        theme.glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("⚠️ " + t("danger_zone"), size=16, weight=ft.FontWeight.W_600, color=theme.TEXT_DANGER),
                ft.OutlinedButton("🗑️ " + t("delete_save"), width=250, height=42,
                    style=theme.DANGER_BTN_STYLE,
                    on_click=delete_save_click),
            ]),
            border_color=ft.Colors.with_opacity(0.2, ft.Colors.RED),
        ),
    ])

    return ft.Column(
        expand=True, scroll=ft.ScrollMode.AUTO,
        controls=[ft.Container(
            padding=ft.padding.all(theme.PAGE_PADDING),
            content=ft.Column(spacing=14, controls=controls_list),
        )],
    )


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
