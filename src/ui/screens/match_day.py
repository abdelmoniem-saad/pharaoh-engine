"""
Match Day screen — pre-match info, simulate, and show results.
"""
from __future__ import annotations

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.app import App

from src.data import queries
from src.core.calendar import simulate_user_match, advance_to_next_match, advance_day
from src.core.league import is_season_complete, get_champion
from src.utils.config import MatchEventType


class MatchDayScreen(Screen):
    """Match day — view upcoming fixture, simulate, see results."""

    def on_enter(self):
        self.clear_widgets()
        app = App.get_running_app()

        if not app.db_conn or not app.game_state:
            self.add_widget(Label(text="No game loaded"))
            return

        conn = app.db_conn
        gs = app.game_state

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        # Header
        layout.add_widget(Label(
            text=f"⚽ Match Day",
            font_size=dp(22), bold=True,
            size_hint_y=None, height=dp(40),
        ))

        layout.add_widget(Label(
            text=f"Date: {gs.current_date.strftime('%d %b %Y')}",
            font_size=dp(14), size_hint_y=None, height=dp(25),
            color=(0.7, 0.7, 0.7, 1),
        ))

        # Check if season is complete
        if is_season_complete(conn):
            champ = get_champion(conn)
            if champ:
                layout.add_widget(Label(
                    text=f"🏆 Season Complete!\n{champ.club_name} are CHAMPIONS!\n{champ.points} points",
                    font_size=dp(20), bold=True,
                    color=(1, 0.85, 0, 1),
                ))
            back_btn = Button(text="← Back", size_hint_y=None, height=dp(45))
            back_btn.bind(on_press=lambda inst: setattr(self.manager, 'current', 'squad'))
            layout.add_widget(back_btn)
            self.add_widget(layout)
            return

        # Next fixture for user
        fixture = queries.get_user_next_fixture(conn, gs.user_club_id)

        if fixture:
            # Pre-match display
            is_home = fixture.home_club_id == gs.user_club_id
            venue = "HOME" if is_home else "AWAY"

            match_info = BoxLayout(orientation="vertical", spacing=dp(5),
                                    size_hint_y=None, height=dp(120))
            match_info.add_widget(Label(
                text=f"Matchday {fixture.matchday} — {venue}",
                font_size=dp(16), bold=True,
                color=(0.9, 0.8, 0.3, 1),
            ))
            match_info.add_widget(Label(
                text=f"{fixture.home_club_name}",
                font_size=dp(20), bold=True,
            ))
            match_info.add_widget(Label(
                text="vs",
                font_size=dp(14),
                color=(0.6, 0.6, 0.6, 1),
            ))
            match_info.add_widget(Label(
                text=f"{fixture.away_club_name}",
                font_size=dp(20), bold=True,
            ))
            layout.add_widget(match_info)

            if fixture.date and fixture.date > gs.current_date:
                # Match is in the future — advance days
                days_until = (fixture.date - gs.current_date).days
                layout.add_widget(Label(
                    text=f"Match in {days_until} day(s)",
                    font_size=dp(14), size_hint_y=None, height=dp(25),
                ))

                advance_btn = Button(
                    text=f"⏩ Advance to Match Day",
                    size_hint_y=None, height=dp(50),
                    font_size=dp(16),
                )
                advance_btn.bind(on_press=lambda inst: self._advance_to_match(conn, gs))
                layout.add_widget(advance_btn)
            else:
                # Match is today — simulate!
                sim_btn = Button(
                    text="▶ SIMULATE MATCH",
                    size_hint_y=None, height=dp(55),
                    font_size=dp(18),
                    background_color=(0.2, 0.7, 0.2, 1),
                )
                sim_btn.bind(on_press=lambda inst: self._simulate(conn, gs))
                layout.add_widget(sim_btn)
        else:
            # No fixture found — try advancing
            layout.add_widget(Label(
                text="No upcoming match found.",
                font_size=dp(16),
            ))
            advance_btn = Button(
                text="⏩ Advance Day",
                size_hint_y=None, height=dp(50),
            )
            advance_btn.bind(on_press=lambda inst: self._advance_one_day(conn, gs))
            layout.add_widget(advance_btn)

        # Navigation
        nav = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
        for target, text in [("squad", "📋 Squad"), ("table", "📊 Table"), ("inbox", "📧 Inbox")]:
            btn = Button(text=text, font_size=dp(13))
            btn.screen_target = target
            btn.bind(on_press=lambda inst: setattr(self.manager, 'current', inst.screen_target))
            nav.add_widget(btn)
        layout.add_widget(nav)

        self.add_widget(layout)

    def _simulate(self, conn, gs):
        """Simulate the user's match."""
        result = simulate_user_match(conn, gs)
        if result:
            self._show_result_popup(result)

        # Also advance the day
        advance_day(conn, gs)
        self.on_enter()

    def _advance_to_match(self, conn, gs):
        """Advance days until the user's next match."""
        messages = advance_to_next_match(conn, gs)
        self.on_enter()

    def _advance_one_day(self, conn, gs):
        """Advance a single day."""
        messages = advance_day(conn, gs)
        self.on_enter()

    def _show_result_popup(self, result):
        """Show match result in a popup."""
        content = BoxLayout(orientation="vertical", spacing=dp(5))

        # Score
        content.add_widget(Label(
            text=result.score_display,
            font_size=dp(22), bold=True,
            size_hint_y=None, height=dp(45),
        ))

        # Goals
        scroll = ScrollView(size_hint=(1, 1))
        events_layout = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(3),
        )
        events_layout.bind(minimum_height=events_layout.setter("height"))

        goals = [e for e in result.events if e.event_type == MatchEventType.GOAL]
        for g in goals:
            text = f"⚽ {g.minute}' {g.player_name}"
            if g.second_player_name:
                text += f" (assist: {g.second_player_name})"
            events_layout.add_widget(Label(
                text=text, font_size=dp(13),
                size_hint_y=None, height=dp(25),
            ))

        # Stats
        events_layout.add_widget(Label(text="", size_hint_y=None, height=dp(10)))
        stats_text = (
            f"Possession: {result.home_stats.possession:.0f}% - {result.away_stats.possession:.0f}%\n"
            f"Shots: {result.home_stats.shots} - {result.away_stats.shots}\n"
            f"On Target: {result.home_stats.shots_on_target} - {result.away_stats.shots_on_target}\n"
            f"Corners: {result.home_stats.corners} - {result.away_stats.corners}\n"
            f"Fouls: {result.home_stats.fouls} - {result.away_stats.fouls}"
        )
        events_layout.add_widget(Label(
            text=stats_text, font_size=dp(12),
            size_hint_y=None, height=dp(100),
        ))

        scroll.add_widget(events_layout)
        content.add_widget(scroll)

        close_btn = Button(text="OK", size_hint_y=None, height=dp(40))
        popup = Popup(
            title="Match Result",
            content=content,
            size_hint=(0.9, 0.7),
        )
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        popup.open()

