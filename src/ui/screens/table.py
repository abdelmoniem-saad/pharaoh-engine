"""
League Table screen — standings display.
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


class TableScreen(Screen):
    """Display the Egyptian Premier League standings."""

    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()
        if not app.db_conn or not app.game_state:
            self.add_widget(Label(text="No game loaded"))
            return

        conn = app.db_conn
        gs = app.game_state
        standings = queries.get_standings(conn)

        layout = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(3))
        layout.add_widget(Label(
            text="Egyptian Premier League", font_size=dp(18), bold=True,
            size_hint_y=None, height=dp(40),
        ))

        headers = GridLayout(cols=9, size_hint_y=None, height=dp(28), spacing=dp(1))
        for h in ["#", "Team", "P", "W", "D", "L", "GF", "GA", "Pts"]:
            headers.add_widget(Label(text=h, font_size=dp(10), bold=True,
                color=(0.9, 0.8, 0.3, 1), size_hint_x=0.25 if h == "Team" else 0.08))
        layout.add_widget(headers)

        scroll = ScrollView(size_hint=(1, 1))
        table = GridLayout(cols=9, size_hint_y=None, spacing=dp(1), padding=dp(1))
        table.bind(minimum_height=table.setter("height"))

        for pos, s in enumerate(standings, 1):
            is_user = s.club_id == gs.user_club_id
            color = (0.3, 1.0, 0.3, 1) if is_user else (1, 1, 1, 1)
            rh = dp(30)
            table.add_widget(Label(text=str(pos), font_size=dp(11),
                size_hint_y=None, height=rh, size_hint_x=0.08, color=color))
            table.add_widget(Label(text=s.club_name[:15], font_size=dp(11),
                size_hint_y=None, height=rh, size_hint_x=0.25, color=color,
                halign="left", text_size=(dp(90), None)))
            for val in [s.played, s.won, s.drawn, s.lost, s.goals_for, s.goals_against]:
                table.add_widget(Label(text=str(val), font_size=dp(11),
                    size_hint_y=None, height=rh, size_hint_x=0.08, color=color))
            table.add_widget(Label(text=str(s.points), font_size=dp(12), bold=True,
                size_hint_y=None, height=rh, size_hint_x=0.08, color=color))

        scroll.add_widget(table)
        layout.add_widget(scroll)

        nav = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        for target, text in [("squad", "Squad"), ("match_day", "Match"), ("inbox", "Inbox")]:
            btn = Button(text=text, font_size=dp(13))
            btn.screen_target = target
            btn.bind(on_press=lambda inst: setattr(self.manager, 'current', inst.screen_target))
            nav.add_widget(btn)
        layout.add_widget(nav)
        self.add_widget(layout)

