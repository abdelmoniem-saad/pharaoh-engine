"""
Match result widget — compact result display.
"""
from __future__ import annotations
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from src.data.models import MatchResult


class MatchResultWidget(BoxLayout):
    """Compact match result display."""

    def __init__(self, result: MatchResult, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(35)

        self.add_widget(Label(
            text=result.home_club_name, font_size=dp(12),
            size_hint_x=0.35, halign="right", text_size=(dp(100), None),
        ))
        self.add_widget(Label(
            text=f"{result.home_goals} - {result.away_goals}",
            font_size=dp(14), bold=True, size_hint_x=0.15,
        ))
        self.add_widget(Label(
            text=result.away_club_name, font_size=dp(12),
            size_hint_x=0.35, halign="left", text_size=(dp(100), None),
        ))

