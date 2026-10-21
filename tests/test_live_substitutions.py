"""Regression tests for live commands, scoring, fatigue and appearance accounting."""
from datetime import date

import pytest

from src.core import match_engine as engine
from src.data.models import MatchEvent, MatchResult, TeamTactics
from src.utils import rng
from src.utils.config import MatchEventType as E
from tests.test_match_engine import _make_club, _make_squad
from src.core.tactics import auto_select_xi


def fixture(seed=42):
    rng.seed(seed)
    squads = [_make_squad(1), _make_squad(100)]
    tactics = []
    for squad in squads:
        xi, bench = auto_select_xi(squad, "4-4-2")
        tactics.append(TeamTactics(formation="4-4-2", starting_xi=xi, bench=bench))
    result = engine.simulate_match(_make_club(1, "Home"), _make_club(2, "Away"),
                                  *squads, *tactics, match_date=date(2026, 8, 1),
                                  controlled_club_id=1)
    return result, tactics


@pytest.mark.parametrize("seed", range(20))
def test_substitution_keeps_past_and_score_matches_events(seed):
    result, tactics = fixture(seed)
    xi = engine.lineup_at(result, 1, tactics[0].starting_xi, 60)
    before = [e.model_dump() for e in result.events if e.minute <= 60]
    world_state = rng.get_rng().getstate()
    updated = engine.substitute(result, 60, 1, xi[-1], tactics[0].bench[0])
    assert rng.get_rng().getstate() == world_state
    assert [e.model_dump() for e in updated.events if e.minute <= 60][:-1] == before
    assert result.events != updated.events  # original is not mutated
    for club_id, goals, stats in [(1, updated.home_goals, updated.home_stats),
                                   (2, updated.away_goals, updated.away_stats)]:
        assert goals == sum(e.club_id == club_id and e.event_type in (E.GOAL, E.PENALTY)
                            for e in updated.events)
        assert stats.shots >= stats.shots_on_target >= goals
    assert updated.events[-1].event_type == E.FULL_TIME
    assert updated.events[-1].minute == max(e.minute for e in updated.events)
    assert tactics[0].bench[0] in updated.player_ratings


def test_repeat_substitution_preserves_prior_commands_and_rejects_reentry():
    result, tactics = fixture()
    xi, bench = tactics[0].starting_xi, tactics[0].bench
    first = engine.substitute(result, 60, 1, xi[-1], bench[0])
    second = engine.substitute(first, 70, 1, bench[0], bench[1])
    assert sum(e.event_type == E.SUBSTITUTION and e.club_id == 1 for e in second.events) == 2
    minutes = engine.minutes_played(second, 1, xi)
    assert minutes[xi[-1]] == 60
    assert minutes[bench[0]] == 10
    assert minutes[bench[1]] == 20
    with pytest.raises(ValueError):
        engine.substitute(second, 75, 1, bench[1], xi[-1])
    with pytest.raises(ValueError):
        engine.substitute(second, 50, 1, xi[1], bench[2])


def test_only_submitted_bench_and_three_changes_allowed():
    result, tactics = fixture()
    xi, bench = tactics[0].starting_xi, tactics[0].bench
    with pytest.raises(ValueError):
        engine.substitute(result, 60, 1, xi[-1], 9999)
    with pytest.raises(ValueError):
        engine.substitute(result, 60, 2, tactics[1].starting_xi[-1], tactics[1].bench[0])
    for i in range(3):
        result = engine.substitute(result, 60+i, 1, xi[-1-i], bench[i])
    with pytest.raises(ValueError):
        engine.substitute(result, 75, 1, xi[-4], bench[3])


def test_dismissed_player_cannot_be_replaced_and_minutes_are_capped():
    result = MatchResult(home_club_id=1, away_club_id=2, events=[
        MatchEvent(minute=35, club_id=1, event_type=E.RED_CARD, player_id=2),
        MatchEvent(minute=65, club_id=1, event_type=E.SUBSTITUTION, player_id=3, second_player_id=12),
    ])
    assert engine.lineup_at(result, 1, [1, 2, 3], 70) == [1, 12]
    assert engine.minutes_played(result, 1, [1, 2, 3]) == {1: 90, 2: 35, 3: 65, 12: 25}


def test_persisted_penalty_and_substitute_statistics(monkeypatch):
    from src.core.calendar import _update_player_stats_after_match
    home, away = _make_squad(1), _make_squad(100)
    result = MatchResult(home_club_id=1, away_club_id=2, home_goals=1, events=[
        MatchEvent(minute=60, club_id=1, event_type=E.SUBSTITUTION,
                   player_id=home[0].id, second_player_id=home[11].id),
        MatchEvent(minute=70, club_id=1, event_type=E.PENALTY, player_id=home[11].id),
    ])
    monkeypatch.setattr('src.data.queries.update_player_stats', lambda *_: None)
    _update_player_stats_after_match(None, result, home, away,
        TeamTactics(starting_xi=[p.id for p in home[:11]]),
        TeamTactics(starting_xi=[p.id for p in away[:11]]))
    assert home[0].season_stats.minutes_played == 60
    assert home[11].season_stats.minutes_played == 30
    assert home[11].season_stats.appearances == 1
    assert home[11].season_stats.goals == 1
