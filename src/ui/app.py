"""
Main Kivy application — screen manager and app lifecycle.
"""
from __future__ import annotations

import os
import sys

# Ensure src is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.core.window import Window

from src.ui.screens.main_menu import MainMenuScreen
from src.ui.screens.squad import SquadScreen
from src.ui.screens.tactics import TacticsScreen
from src.ui.screens.match_day import MatchDayScreen
from src.ui.screens.table import TableScreen
from src.ui.screens.inbox import InboxScreen

# Set mobile-friendly window size for desktop testing
Window.size = (400, 700)


class PharaohScreenManager(ScreenManager):
    """Manages all game screens."""
    pass


class PharaohEngineApp(App):
    """Main application class."""

    title = "Pharaoh Engine"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_conn = None
        self.game_state = None

    def build(self):
        self.sm = PharaohScreenManager(transition=SlideTransition())

        # Add all screens
        self.sm.add_widget(MainMenuScreen(name="main_menu"))
        self.sm.add_widget(SquadScreen(name="squad"))
        self.sm.add_widget(TacticsScreen(name="tactics"))
        self.sm.add_widget(MatchDayScreen(name="match_day"))
        self.sm.add_widget(TableScreen(name="table"))
        self.sm.add_widget(InboxScreen(name="inbox"))

        return self.sm

    def on_stop(self):
        """Clean up on app exit."""
        if self.db_conn:
            from src.data.database import close
            close()

    def switch_screen(self, screen_name: str, direction: str = "left"):
        """Navigate to a different screen."""
        self.sm.transition.direction = direction
        self.sm.current = screen_name


def run_app():
    """Entry point to launch the application."""
    PharaohEngineApp().run()

