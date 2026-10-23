"""Construct real Flet controls against a disposable seeded career."""
from importlib import import_module
from types import SimpleNamespace

import pytest

from src.data import database, queries
from src.data.seed import seed_database
from src.ui import app, theme
from src.utils.localization import set_language


class Page:
    width = 390
    height = 844
    navigation_bar = None
    def __init__(self):
        self.controls = []
        self.overlay = []
        self.dialog = None
    def update(self):
        pass
    def show_dialog(self, dialog):
        self.dialog = dialog
    def pop_dialog(self):
        self.dialog = None
    def run_task(self, task, *args):
        pass


@pytest.mark.parametrize('palette', ['classic', 'supporter'])
@pytest.mark.parametrize('language', ['en', 'ar'])
def test_career_screens_build(palette, language, monkeypatch):
    conn = database.connect('screen-test')
    gs = seed_database(conn)
    club = queries.get_all_clubs(conn)[0]
    gs.user_club_id, gs.user_club_name = club.id, club.name
    queries.save_game_state(conn, gs)
    from src.core.league import create_league_season
    create_league_season(conn, queries.get_all_clubs(conn), gs.season_year)
    state = app.AppState()
    state.db_conn, state.game_state = conn, gs
    monkeypatch.setattr(app, 'app_state', state)
    theme.configure(palette)
    set_language(language)
    page = Page()
    try:
        for screen, builder in [
            ('squad','build_squad_screen'), ('tactics','build_tactics_screen'),
            ('match_day','build_match_day_screen'), ('table','build_table_screen'),
            ('inbox','build_inbox_screen'), ('club_overview','build_club_overview_screen'),
            ('fixtures','build_fixtures_screen'), ('transfers','build_transfers_screen'),
            ('pre_match','build_pre_match_screen'), ('settings','build_settings_screen'),
            ('history','build_history_screen'), ('main_menu','build_main_menu'),
        ]:
            module = import_module('src.ui.screens.' + screen)
            assert getattr(module, builder)(page) is not None, screen
        # Sorting used to evaluate a nonexistent fallback key even for valid choices.
        from dataclasses import fields
        import flet as ft
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
        from src.ui.screens.squad import build_squad_screen
        squad = build_squad_screen(page)
        dropdown = next(c for c in walk(squad) if isinstance(c, ft.Dropdown))
        for option in dropdown.options:
            dropdown.value = option.key
            dropdown.on_select(SimpleNamespace(control=dropdown))
        # Tactical adjustment commits once on release, without a rebuild per drag tick.
        monkeypatch.setattr(app, 'navigate', lambda *args: None)
        from src.ui.screens.tactics import build_tactics_screen
        tactics = build_tactics_screen(page)
        slider = next(c for c in walk(tactics) if isinstance(c, ft.Slider))
        assert slider.on_change is None
        slider.value = 7
        slider.on_change_end(SimpleNamespace(control=slider))
        assert queries.get_club(conn, club.id).pressing_intensity == 7
        from src.ui.screens.squad import _show_player_detail
        from src.core.player import calculate_overall_rating
        from src.utils.localization import t
        players = queries.get_players_by_club(conn, club.id)
        _show_player_detail(page, players[0], calculate_overall_rating(players[0]))
        assert page.dialog is not None
        for label in (t("attributes"), t("development"), t("overview_tab")):
            button = next(c for c in walk(page.dialog) if isinstance(c, ft.TextButton)
                          and c.content == label)
            button.on_click(SimpleNamespace(control=button))
        from src.data.models import MatchResult, MatchdayOutcome, MatchEvent
        from src.utils.config import MatchEventType
        state._last_outcome = MatchdayOutcome(matchday=1, user_result=MatchResult(
            home_club_id=club.id, away_club_id=999, home_club_name=club.name,
            away_club_name="Opposition", home_goals=1,
            events=[MatchEvent(minute=20, event_type=MatchEventType.PENALTY,
                              club_id=club.id, player_id=players[0].id,
                              player_name="Penalty scorer")]))
        from src.ui.screens.post_match import build_post_match_screen
        report = build_post_match_screen(page)
        assert any(isinstance(c, ft.Text) and c.value == "Penalty scorer" for c in walk(report))
        app.show_tutorial_overlay(page)
        assert page.overlay
        from src.ui.screens.main_menu import _show_load_game_dialog
        _show_load_game_dialog(page)
        assert page.dialog is not None
    finally:
        theme.configure('classic')
        set_language('en')


def test_settings_without_career_does_not_create_save(monkeypatch):
    monkeypatch.setattr(app, 'app_state', app.AppState())
    from src.ui.screens.settings import build_settings_screen
    build_settings_screen(Page())
    assert not list(database._DEFAULT_DB_DIR.glob('*.db'))
