"""
Stat bar widget — visual attribute/stat bar.
"""
from __future__ import annotations
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.metrics import dp


class StatBar(BoxLayout):
    """A labeled progress bar for displaying a stat value."""

    def __init__(self, label: str, value: int, max_value: int = 20, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(25)
        self.spacing = dp(5)

        self.add_widget(Label(
            text=label, font_size=dp(11),
            size_hint_x=0.4, halign="left",
            text_size=(dp(80), None),
        ))

        bar = ProgressBar(max=max_value, value=value, size_hint_x=0.45)
        self.add_widget(bar)

        self.add_widget(Label(
            text=str(value), font_size=dp(11), bold=True,
            size_hint_x=0.15,
            color=self._color_for_value(value, max_value),
        ))

    @staticmethod
    def _color_for_value(value: int, max_value: int) -> tuple:
        ratio = value / max_value
        if ratio >= 0.8:
            return (0.2, 1.0, 0.2, 1)
        elif ratio >= 0.6:
            return (0.8, 1.0, 0.2, 1)
        elif ratio >= 0.4:
            return (1.0, 1.0, 0.2, 1)
        elif ratio >= 0.2:
            return (1.0, 0.6, 0.2, 1)
        else:
            return (1.0, 0.2, 0.2, 1)

