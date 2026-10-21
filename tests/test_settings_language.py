"""Exercise language callbacks under the legacy Windows console encoding."""
import io
import sys
from dataclasses import fields
from types import SimpleNamespace

import flet as ft
import pytest

from src.ui import app
from src.ui.screens.settings import build_settings_screen
from src.utils import prefs
from src.utils.localization import get_language, set_language, t
from src.data import database


def walk(control):
    yield control
    for field in fields(control):
        value = getattr(control, field.name)
        if isinstance(value, ft.Control):
            yield from walk(value)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, ft.Control):
                    yield from walk(child)


@pytest.mark.parametrize('career', [False, True])
def test_language_toggle_and_reload_on_windows(monkeypatch, career):
    state = app.AppState()
    if career:
        state.db_conn = database.connect('language-test')
    monkeypatch.setattr(app, 'app_state', state)
    page = SimpleNamespace(navigation_bar=None, rtl=False)
    screens = []
    monkeypatch.setattr(app, 'navigate', lambda p, route: screens.append(build_settings_screen(p)))
    # The original Unicode debug print raises here, exactly as on Windows.
    console = io.TextIOWrapper(io.BytesIO(), encoding='cp1252', errors='strict')
    monkeypatch.setattr(sys, 'stdout', console)
    set_language('en')
    try:
        screen = build_settings_screen(page)
        for language, label in [('ar', 'سرعة المباراة'), ('en', 'Match Speed')]:
            radio = next(c for c in walk(screen) if isinstance(c, ft.RadioGroup)
                         and c.value in ('en', 'ar'))
            radio.value = language
            radio.on_change(SimpleNamespace(control=radio))
            assert get_language() == language
            assert page.rtl == (language == 'ar')
            screen = screens[-1]
            assert any(isinstance(c, ft.Dropdown) and c.label == label for c in walk(screen))
            assert any(isinstance(c, ft.RadioGroup) and c.value == language for c in walk(screen))
            if career:
                assert state.db_conn.execute('SELECT language FROM game_settings WHERE id=1').fetchone()[0] == language
            # Simulate cold preference loading, as main() does on refresh.
            prefs._cache = None
            set_language('en' if language == 'ar' else 'ar')
            set_language(prefs.get_pref('language', 'en'))
            page.rtl = get_language() == 'ar'
            screen = build_settings_screen(page)
            assert get_language() == language
            assert any(isinstance(c, ft.Dropdown) and c.label == label for c in walk(screen))
            assert t('language_help') != '[language_help]'
    finally:
        set_language('en')
