"""
Player card widget — reusable player info display.
"""
from __future__ import annotations
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from src.data.models import Player
from src.core.player import calculate_overall_rating


class PlayerCard(BoxLayout):
    """Compact player info card for use in lists and popups."""

    def __init__(self, player: Player, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(40)
        self.spacing = dp(5)

        ovr = calculate_overall_rating(player)

        self.add_widget(Label(text=player.name, font_size=dp(13),
            size_hint_x=0.35, halign="left", text_size=(dp(100), None)))
        self.add_widget(Label(text=player.position.value, font_size=dp(12),
            size_hint_x=0.1))
        self.add_widget(Label(text=str(player.age), font_size=dp(12),
            size_hint_x=0.1))
        self.add_widget(Label(text=str(ovr), font_size=dp(13), bold=True,
            size_hint_x=0.1,
            color=(0.3, 1, 0.3, 1) if ovr >= 70 else (1, 1, 1, 1)))
        self.add_widget(Label(text=f"{player.fitness}%", font_size=dp(12),
            size_hint_x=0.1,
            color=(0, 1, 0, 1) if player.fitness >= 80 else (1, 0, 0, 1)))
        self.add_widget(Label(text=f"{player.form:.1f}", font_size=dp(12),
            size_hint_x=0.1))

