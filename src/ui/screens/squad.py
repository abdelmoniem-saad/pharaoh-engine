"""
Squad management screen — view players, set starting XI.
"""
from __future__ import annotations

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.app import App

from src.data import queries
from src.core.player import calculate_overall_rating


class SquadScreen(Screen):
    """Display the user's squad with key attributes."""

    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()

        if not app.db_conn or not app.game_state:
            self.add_widget(Label(text="No game loaded"))
            return

        conn = app.db_conn
        game_state = app.game_state
        squad = queries.get_players_by_club(conn, game_state.user_club_id)

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(5))

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(50))
        header.add_widget(Label(
            text=f"📋 {game_state.user_club_name} — Squad",
            font_size=dp(20), bold=True, halign="left",
        ))
        layout.add_widget(header)

        # Date display
        date_label = Label(
            text=f"Date: {game_state.current_date.strftime('%d %b %Y')}",
            size_hint_y=None, height=dp(25), font_size=dp(13),
            color=(0.7, 0.7, 0.7, 1),
        )
        layout.add_widget(date_label)

        # Column headers
        col_header = GridLayout(cols=5, size_hint_y=None, height=dp(30), spacing=dp(2))
        for text in ["Name", "Pos", "Age", "OVR", "Fit"]:
            col_header.add_widget(Label(
                text=text, font_size=dp(12), bold=True,
                color=(0.9, 0.8, 0.3, 1),
            ))
        layout.add_widget(col_header)

        # Player list
        scroll = ScrollView(size_hint=(1, 1))
        player_list = GridLayout(
            cols=5, size_hint_y=None, spacing=dp(2), padding=dp(2),
        )
        player_list.bind(minimum_height=player_list.setter("height"))

        for player in squad:
            ovr = calculate_overall_rating(player)
            fit_color = (0, 1, 0, 1) if player.fitness >= 80 else \
                        (1, 1, 0, 1) if player.fitness >= 50 else (1, 0, 0, 1)

            player_list.add_widget(Label(
                text=player.name, font_size=dp(12),
                size_hint_y=None, height=dp(35),
                text_size=(dp(120), None), halign="left",
            ))
            player_list.add_widget(Label(
                text=player.position.value, font_size=dp(12),
                size_hint_y=None, height=dp(35),
            ))
            player_list.add_widget(Label(
                text=str(player.age), font_size=dp(12),
                size_hint_y=None, height=dp(35),
            ))
            player_list.add_widget(Label(
                text=str(ovr), font_size=dp(14), bold=True,
                size_hint_y=None, height=dp(35),
                color=(0.3, 1, 0.3, 1) if ovr >= 70 else (1, 1, 1, 1),
            ))
            player_list.add_widget(Label(
                text=f"{player.fitness}%", font_size=dp(12),
                size_hint_y=None, height=dp(35),
                color=fit_color,
            ))

        scroll.add_widget(player_list)
        layout.add_widget(scroll)

        # Navigation buttons
        nav = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))

        for screen_name, label_text in [
            ("tactics", "⚙ Tactics"),
            ("match_day", "⚽ Match"),
            ("table", "📊 Table"),
            ("inbox", "📧 Inbox"),
        ]:
            btn = Button(text=label_text, font_size=dp(13))
            btn.screen_target = screen_name
            btn.bind(on_press=lambda inst: setattr(self.manager, 'current', inst.screen_target))
            nav.add_widget(btn)

        layout.add_widget(nav)
        self.add_widget(layout)

