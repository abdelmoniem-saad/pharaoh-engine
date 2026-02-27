"""
Tactics screen — formation and mentality selection.
"""
from __future__ import annotations

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.app import App

from src.data import queries
from src.core.tactics import (
    get_available_formations, PRESETS, preset_to_tactics,
)
from src.utils.config import Mentality


class TacticsScreen(Screen):
    """Tactical setup — choose formation, mentality, and presets."""

    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()

        if not app.db_conn or not app.game_state:
            self.add_widget(Label(text="No game loaded"))
            return

        conn = app.db_conn
        club = queries.get_club(conn, app.game_state.user_club_id)
        if not club:
            return

        layout = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(10))

        # Title
        layout.add_widget(Label(
            text="⚙️ Tactics",
            font_size=dp(22), bold=True,
            size_hint_y=None, height=dp(45),
        ))

        # Formation picker
        layout.add_widget(Label(
            text="Formation:", font_size=dp(15),
            size_hint_y=None, height=dp(25),
            halign="left",
        ))

        formations = get_available_formations()
        formation_spinner = Spinner(
            text=club.formation,
            values=formations,
            size_hint_y=None, height=dp(45),
            font_size=dp(16),
        )
        formation_spinner.bind(text=lambda inst, val: self._update_formation(val))
        layout.add_widget(formation_spinner)

        # Mentality picker
        layout.add_widget(Label(
            text="Mentality:", font_size=dp(15),
            size_hint_y=None, height=dp(25),
            halign="left",
        ))

        mentality_names = [m.name.replace("_", " ").title() for m in Mentality]
        mentality_spinner = Spinner(
            text=club.mentality.name.replace("_", " ").title(),
            values=mentality_names,
            size_hint_y=None, height=dp(45),
            font_size=dp(16),
        )
        mentality_spinner.bind(text=lambda inst, val: self._update_mentality(val))
        layout.add_widget(mentality_spinner)

        # Presets section
        layout.add_widget(Label(
            text="Quick Presets:", font_size=dp(15),
            size_hint_y=None, height=dp(30),
            halign="left",
        ))

        for key, preset in PRESETS.items():
            btn = Button(
                text=f"{preset.name}\n{preset.description[:50]}...",
                size_hint_y=None, height=dp(55),
                font_size=dp(12),
                halign="center",
            )
            btn.preset_key = key
            btn.bind(on_press=lambda inst: self._apply_preset(inst.preset_key))
            layout.add_widget(btn)

        # Back button
        back_btn = Button(
            text="← Back to Squad",
            size_hint_y=None, height=dp(45),
            font_size=dp(15),
        )
        back_btn.bind(on_press=lambda inst: setattr(self.manager, 'current', 'squad'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def _update_formation(self, formation: str):
        app = App.get_running_app()
        club = queries.get_club(app.db_conn, app.game_state.user_club_id)
        if club:
            club.formation = formation
            queries.update_club(app.db_conn, club)

    def _update_mentality(self, mentality_name: str):
        app = App.get_running_app()
        club = queries.get_club(app.db_conn, app.game_state.user_club_id)
        if club:
            mentality_key = mentality_name.upper().replace(" ", "_")
            try:
                club.mentality = Mentality[mentality_key]
                queries.update_club(app.db_conn, club)
            except KeyError:
                pass

    def _apply_preset(self, preset_key: str):
        app = App.get_running_app()
        preset = PRESETS.get(preset_key)
        if not preset:
            return

        club = queries.get_club(app.db_conn, app.game_state.user_club_id)
        if club:
            club.formation = preset.formation
            club.mentality = preset.mentality
            queries.update_club(app.db_conn, club)
            self.on_enter()  # Refresh screen

