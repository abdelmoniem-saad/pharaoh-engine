"""
Settings screen -- match speed, difficulty, auto-save, language.
"""
from __future__ import annotations
import flet as ft


def build_settings_screen(page: ft.Page) -> ft.Column:
    from src.ui.app import app_state, navigate, show_snackbar
    page.navigation_bar = None
    conn = app_state.db_conn
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
            show_snackbar(page, "🗑️ Save deleted!")

        page.show_dialog(ft.AlertDialog(
            title=ft.Text("⚠️ Delete Save?"),
            content=ft.Text("This will permanently delete your current save game.\nAre you sure?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e2: page.pop_dialog()),
                ft.ElevatedButton("Delete", on_click=confirm_delete,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE)),
            ],
        ))

    controls_list = [
        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[
            ft.Text("⚙️ Settings", size=24, weight=ft.FontWeight.BOLD),
            ft.IconButton(icon=ft.Icons.ARROW_BACK, tooltip="Back", on_click=go_back),
        ]),
        ft.Divider(height=1),
        ft.Text("🎮 Gameplay", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_300),
        speed_dd, diff_dd,
        ft.Divider(height=1),
        ft.Text("💾 Save Settings", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_300),
        auto_save_switch, interval_dd,
        ft.Divider(height=1),
        ft.Text("🌍 Language", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.AMBER_300),
        ft.Dropdown(label="Language", value="English", expand=True,
                    options=[ft.dropdown.Option("English")], disabled=True),
        ft.Text("Arabic support coming soon!", size=11, color=ft.Colors.GREY_600, italic=True),
        ft.Divider(height=1),
        ft.Container(height=10),
        ft.ElevatedButton("💾 Save Settings", width=250, height=45,
            style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_700, color=ft.Colors.WHITE,
                text_style=ft.TextStyle(size=16, weight=ft.FontWeight.BOLD)),
            on_click=save_click),
        ft.Container(height=8),
        ft.Text("⚠️ Danger Zone", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.RED_400),
        ft.OutlinedButton("🗑️ Delete Save Game", width=250, height=42,
            style=ft.ButtonStyle(color=ft.Colors.RED_400),
            on_click=delete_save_click),
    ]

    return ft.Column(
        expand=True, scroll=ft.ScrollMode.AUTO,
        controls=[ft.Container(
            padding=ft.padding.all(16),
            content=ft.Column(spacing=14, controls=controls_list),
        )],
    )


def _load_settings(conn) -> dict:
    try:
        row = conn.execute("SELECT * FROM game_settings WHERE id = 1").fetchone()
        if row:
            return dict(match_speed=row["match_speed"], auto_save=row["auto_save"],
                        auto_save_interval=row["auto_save_interval"], difficulty=row["difficulty"])
    except Exception:
        pass
    return {}


def _save_settings(conn, s: dict) -> None:
    try:
        conn.execute("""INSERT INTO game_settings (id,match_speed,auto_save,auto_save_interval,difficulty)
            VALUES (1,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
            match_speed=excluded.match_speed, auto_save=excluded.auto_save,
            auto_save_interval=excluded.auto_save_interval, difficulty=excluded.difficulty
        """, (s["match_speed"], s["auto_save"], s["auto_save_interval"], s["difficulty"]))
        conn.commit()
    except Exception:
        pass
