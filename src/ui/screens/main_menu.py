"""
Main Menu screen — New Game, Continue, Settings.
"""
from __future__ import annotations

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp

from src.data.database import connect, init_schema, close, delete_save
from src.data.seed import seed_database
from src.data import queries
from src.core.league import create_league_season
from src.utils import rng


class MainMenuScreen(Screen):
    """Main menu with New Game, Continue, and Settings options."""

    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        # Title
        title = Label(
            text="⚽ PHARAOH ENGINE ⚽",
            font_size=dp(28),
            bold=True,
            size_hint_y=0.3,
            halign="center",
        )
        layout.add_widget(title)

        subtitle = Label(
            text="Egyptian Football Manager",
            font_size=dp(16),
            size_hint_y=0.1,
            halign="center",
            color=(0.8, 0.7, 0.3, 1),
        )
        layout.add_widget(subtitle)

        # Buttons
        btn_style = {
            "size_hint_y": None,
            "height": dp(55),
            "font_size": dp(18),
        }

        new_game_btn = Button(text="New Game", **btn_style)
        new_game_btn.bind(on_press=self._show_club_selection)
        layout.add_widget(new_game_btn)

        continue_btn = Button(text="Continue", **btn_style)
        continue_btn.bind(on_press=self._continue_game)
        layout.add_widget(continue_btn)

        settings_btn = Button(text="Settings", **btn_style)
        settings_btn.bind(on_press=self._open_settings)
        layout.add_widget(settings_btn)

        # Version
        version = Label(
            text="v0.1.0 — MVP",
            font_size=dp(12),
            size_hint_y=0.1,
            color=(0.5, 0.5, 0.5, 1),
        )
        layout.add_widget(version)

        self.add_widget(layout)

    def _show_club_selection(self, instance):
        """Show a popup to pick a club for a new game."""
        # Seed the database
        delete_save("default")
        conn = connect("default")
        game_state = seed_database(conn, game_seed=rng.randint(1, 999999))

        # Generate league fixtures
        clubs = queries.get_all_clubs(conn)
        create_league_season(conn, clubs, game_state.season_year)

        # Show club picker
        content = BoxLayout(orientation="vertical", spacing=dp(5))
        scroll = ScrollView(size_hint=(1, 0.9))
        club_list = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(5))
        club_list.bind(minimum_height=club_list.setter("height"))

        popup = Popup(
            title="Choose Your Club",
            size_hint=(0.9, 0.8),
        )

        for club in clubs:
            btn = Button(
                text=f"{club.name} ({club.city}) — Rep: {club.reputation}",
                size_hint_y=None,
                height=dp(45),
                font_size=dp(14),
            )
            btn.club_id = club.id
            btn.club_name = club.name
            btn.bind(on_press=lambda inst: self._select_club(inst, conn, game_state, popup))
            club_list.add_widget(btn)

        scroll.add_widget(club_list)
        content.add_widget(scroll)

        cancel_btn = Button(text="Cancel", size_hint_y=None, height=dp(45))
        cancel_btn.bind(on_press=popup.dismiss)
        content.add_widget(cancel_btn)

        popup.content = content
        popup.open()

    def _select_club(self, instance, conn, game_state, popup):
        """Handle club selection."""
        game_state.user_club_id = instance.club_id
        game_state.user_club_name = instance.club_name
        queries.save_game_state(conn, game_state)

        # Mark club as user controlled
        club = queries.get_club(conn, instance.club_id)
        if club:
            club.is_user_controlled = True
            queries.update_club(conn, club)

        app = self.manager.parent if hasattr(self.manager, 'parent') else None
        if hasattr(self.manager, '_app'):
            self.manager._app.db_conn = conn
            self.manager._app.game_state = game_state

        # Store on the app
        from kivy.app import App
        app = App.get_running_app()
        app.db_conn = conn
        app.game_state = game_state

        popup.dismiss()
        self.manager.current = "squad"

    def _continue_game(self, instance):
        """Load an existing save game."""
        from kivy.app import App
        try:
            conn = connect("default")
            game_state = queries.load_game_state(conn)
            if game_state:
                app = App.get_running_app()
                app.db_conn = conn
                app.game_state = game_state
                self.manager.current = "squad"
            else:
                self._show_error("No save game found. Start a New Game!")
        except Exception as e:
            self._show_error(f"Error loading save: {e}")

    def _open_settings(self, instance):
        """Open settings popup. Placeholder."""
        popup = Popup(
            title="Settings",
            content=Label(text="Settings coming in Phase 2!"),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def _show_error(self, message: str):
        popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.8, 0.3),
        )
        popup.open()

