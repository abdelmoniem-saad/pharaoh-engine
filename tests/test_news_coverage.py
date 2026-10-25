"""Exercise every authored random event and press branch, not one lucky sample."""
import re
from string import Formatter
import pytest
from src.core.media import HEADLINES, RANDOM_EVENTS
from src.core.events import _get_event_pool
from src.data.models import GameState
from src.ui.screens.post_match import _PRESS_QUESTIONS
from src.utils.inbox_localization import translate_text, CATALOG


def assert_ar(text):
    translated, missing = translate_text(text, {'Club': 'النادي', 'Player': 'اللاعب', 'Opponent': 'المنافس'})
    assert not missing, (text, translated)
    assert not re.search('[A-Za-z]{2,}', translated), (text, translated)
    return translated


@pytest.mark.parametrize('template', [t for group in HEADLINES.values() for t in group])
def test_all_headlines(template):
    assert_ar(template.format(club='Club', opponent='Opponent'))


@pytest.mark.parametrize('event', RANDOM_EVENTS)
def test_all_random_news(event):
    assert_ar(event['subject'])
    assert_ar(event['body'].format(club='Club', player='Player'))


@pytest.mark.parametrize('event', _get_event_pool(GameState(user_club_name='Club'), None))
def test_all_interactive_event_outcomes(event):
    assert_ar(event.title)
    assert_ar(event.body)
    for choice in event.choices:
        assert_ar(choice.text)
        assert_ar(choice.response)
        assert_ar(event.body + '\n\n📌 Your decision: ' + choice.text + '\n\n' + choice.response)


@pytest.mark.parametrize('question,answers', [q for group in _PRESS_QUESTIONS.values() for q in group])
def test_every_press_answer(question, answers):
    assert_ar(question)
    for text, tone, _, _ in answers:
        assert_ar(text)
        assert_ar(tone)
        assert_ar('Q: ' + question + '\nManager\'s response: "' + text + '"')


def test_all_catalog_templates_keep_their_parameters():
    for english, arabic in CATALOG.items():
        fields = {f for _,f,_,_ in Formatter().parse(english) if f}
        target_fields = {f for _,f,_,_ in Formatter().parse(arabic) if f}
        assert fields == target_fields, english
        sample = english.format(**{f: str(170+i) for i,f in enumerate(sorted(fields))})
        rendered = assert_ar(sample)
        for i,f in enumerate(sorted(fields)):
            assert str(170+i) in rendered, (english, rendered)


def test_season_transition_messages_use_arabic_prose():
    from src.data import database, queries
    from src.data.seed import seed_database
    from src.core.season import start_new_season
    from src.utils.inbox_localization import localize_message
    conn=database.connect('news-season')
    gs=seed_database(conn)
    gs.user_club_id=1
    gs.manager_name='Manager'
    start_new_season(conn,gs)
    for msg in queries.get_inbox(conn,1000):
        shown=localize_message(msg,conn,language='ar')
        assert not shown.has_original_text, (msg.subject,shown.body)


def test_board_status_and_development_terms():
    from src.core.development import PLANS
    from src.utils.config import BoardConfidence, INJURY_TYPES, SEASON_EXPECTATIONS
    for value in [*INJURY_TYPES, *(c.value for c in BoardConfidence),
                  *(v[0] for v in SEASON_EXPECTATIONS.values()), *(p['label'] for p in PLANS.values())]:
        assert_ar(value)
    assert_ar('Fee phase, response expected tomorrow, 2 fee attempt(s) remaining')
    assert_ar('Personal Terms phase, response expected in 3 days, 1 fee attempt(s) remaining')
