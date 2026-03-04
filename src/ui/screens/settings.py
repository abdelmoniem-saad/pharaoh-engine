"""
Settings screen -- match speed, difficulty, auto-save, language.
"""
from __future__ import annotations
import flet as ft
from src.ui.theme import (
    header_bar, golden_divider, glass_card,
    GOLD, GOLD_BORDER, TEXT_SECONDARY, TEXT_MUTED,
    TEXT_DANGER, ACCENT, ACCENT_DARK,
    PRIMARY_BTN_STYLE, SECONDARY_BTN_STYLE, DANGER_BTN_STYLE,
    CARD_GLASS, CARD_GLASS_STRONG, CARD_RADIUS, CARD_RADIUS_SM,
    PAGE_PADDING,
)


def build_settings_screen(page: ft.Page) -> ft.Column:
    from src.ui.app import app_state, navigate, show_snackbar
    from src.utils.localization import get_language, set_language, is_rtl, t

    page.navigation_bar = None

    # Get a DB connection — either the game's or a standalone one for settings
    conn = app_state.db_conn
    if conn is None:
        try:
            from src.data.database import connect
            conn = connect()
        except Exception:
            conn = None

    settings = _load_settings(conn) if conn else {}
    match_speed = settings.get("match_speed", 3)
    auto_save = settings.get("auto_save", 1)
    auto_save_interval = settings.get("auto_save_interval", 7)
    difficulty = settings.get("difficulty", "normal")

    speed_dd = ft.Dropdown(
        label="Match Speed", value=str(match_speed), expand=True,
        options=[ft.dropdown.Option(str(i), text=f"{i} - {n}")
                 for i, n in [(1, "Slow"), (2, "Normal"), (3, "Fast"), (4, "Very Fast"), (5, "Instant")]],
    )
    diff_dd = ft.Dropdown(
        label="Difficulty", value=difficulty, expand=True,
        options=[ft.dropdown.Option(k, text=k.title()) for k in ("easy", "normal", "hard")],
    )
    auto_save_switch = ft.Switch(label="Auto-Save", value=bool(auto_save))
    interval_dd = ft.Dropdown(
        label="Auto-Save Interval", value=str(auto_save_interval), expand=True,
        options=[ft.dropdown.Option(str(d), text=f"Every {d} days") for d in (3, 7, 14, 30)],
    )

    def save_click(e):
        s = {
            "match_speed": int(speed_dd.value or 3),
            "auto_save": 1 if auto_save_switch.value else 0,
            "auto_save_interval": int(interval_dd.value or 7),
            "difficulty": diff_dd.value or "normal",
        }
        if conn:
            _save_settings(conn, s)
        show_snackbar(page, "✅ Settings saved!")

    def go_back(e):
        navigate(page, "/squad" if app_state.game_state else "/")

    def delete_save_click(e):
        def confirm_delete(e2):
            from src.data.database import delete_save
            page.pop_dialog()
            app_state.db_conn = None
            app_state.game_state = None
            delete_save("default")
            navigate(page, "/")
            show_snackbar(page, f"🗑️ {t('save_deleted')}")

        page.show_dialog(ft.AlertDialog(
            title=ft.Text(f"⚠️ {t('delete_save')}?"),
            content=ft.Text(t("delete_save_confirm")),
            actions=[
                ft.TextButton(t("cancel"), on_click=lambda e2: page.pop_dialog()),
                ft.ElevatedButton(t("delete"), on_click=confirm_delete,
                    style=DANGER_BTN_STYLE),
            ],
        ))

    controls_list = [
        header_bar(
            title=t("settings"),
            icon=ft.Icons.SETTINGS,
            page=page,
            back_route="/squad" if app_state.game_state else "/",
        ),

        # Gameplay section
        glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("🎮 " + t("gameplay"), size=16, weight=ft.FontWeight.W_600, color=GOLD),
                speed_dd,
                diff_dd,
            ]),
        ),

        # Save section
        glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("💾 " + t("save"), size=16, weight=ft.FontWeight.W_600, color=GOLD),
                auto_save_switch,
                interval_dd,
            ]),
        ),
    ]

    # Language section — use RadioGroup for reliable on_change
    current_lang = get_language()

    def on_lang_change(e):
        new_lang = e.control.value or "en"
        print(f"DEBUG: Language toggle fired → '{new_lang}' (was '{get_language()}')")
        set_language(new_lang)
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
                print(f"DEBUG: Language '{new_lang}' saved to DB ✅")
            except Exception as ex:
                print(f"DEBUG: language save failed: {ex}")
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
        glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("🌍 " + t("language"), size=16, weight=ft.FontWeight.W_600, color=GOLD),
                lang_radio,
                ft.Text(
                    "Switch between English and Arabic (العربية). "
                    "Arabic enables right-to-left layout.",
                    size=11, color=TEXT_MUTED, italic=True,
                ),
            ]),
        ),
    )

    controls_list.extend([
        ft.Container(height=10),
        ft.ElevatedButton("💾 " + t("save") + " " + t("settings"), width=280, height=48,
            style=PRIMARY_BTN_STYLE,
            on_click=save_click),
        ft.Container(height=16),

        # Danger zone
        glass_card(
            content=ft.Column(spacing=10, controls=[
                ft.Text("⚠️ " + t("danger_zone"), size=16, weight=ft.FontWeight.W_600, color=TEXT_DANGER),
                ft.OutlinedButton("🗑️ " + t("delete_save"), width=250, height=42,
                    style=DANGER_BTN_STYLE,
                    on_click=delete_save_click),
            ]),
            border_color=ft.Colors.with_opacity(0.2, ft.Colors.RED),
        ),
    ])

    return ft.Column(
        expand=True, scroll=ft.ScrollMode.AUTO,
        controls=[ft.Container(
            padding=ft.padding.all(PAGE_PADDING),
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
            )
            return d
    except Exception as ex:
        print(f"DEBUG: _load_settings error: {ex}")
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
        print(f"DEBUG: _save_settings error: {ex}")
