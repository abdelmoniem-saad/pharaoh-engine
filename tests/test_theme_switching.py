"""Switch already-imported components both ways without stale cached tokens."""
import flet as ft
from src.ui import theme
from src.ui.widgets.cards import section_card
from src.ui.widgets.nav_bar import build_nav_bar
from src.utils.localization import set_language


def test_theme_switch_updates_existing_component_modules():
    try:
        theme.configure('classic')
        original = section_card('Club', [ft.Text('Test')])
        theme.configure('supporter')
        supporter = section_card('Club', [ft.Text('Test')])
        assert supporter.bgcolor == theme.CARD_GLASS_STRONG != original.bgcolor
        assert supporter.content.controls[0].controls[0].color == theme.ACCENT
        theme.configure('classic')
        restored = section_card('Club', [ft.Text('Test')])
        assert restored.bgcolor == original.bgcolor
        assert restored.border_radius == original.border_radius
        theme.configure('unknown-preference')
        assert theme.current_theme() == 'classic'
    finally:
        theme.configure('classic')


def test_empty_inbox_label_is_translated():
    try:
        set_language('ar')
        nav = build_nav_bar(None)
        assert nav.destinations[-1].label != 'Inbox'
    finally:
        set_language('en')
