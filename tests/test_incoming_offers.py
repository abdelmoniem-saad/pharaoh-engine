from datetime import date, timedelta
import pytest
from src.data import database, queries
from src.data.models import InboxMessage
from src.core.incoming_offers import get_offer, refresh_offers, decide_offer

TODAY = date(2025, 8, 15)

@pytest.fixture
def career():
    conn = database.connect('offers')
    conn.executemany("INSERT INTO clubs(id,name,short_name,balance,transfer_budget,wage_bill_weekly) VALUES(?,?,?,?,?,?)", [(1,'Seller','SEL',10000,10000,100),(2,'Buyer','BUY',10000,10000,0),(3,'Other','OTH',10000,10000,0)])
    conn.execute("""INSERT INTO players(id,name,age,nationality,governorate,position,preferred_foot,current_ability,potential_ability,club_id,wage_weekly)
        VALUES(1,'Player',25,'Egyptian','Cairo','ST','Right',100,150,1,100)""")
    conn.commit()
    mid = queries.insert_message(conn, InboxMessage(date=TODAY,subject='Offer',body='TRANSFER_OFFER|1|1|2|1000|200',category='transfer'))
    return conn, mid


def financials(conn):
    return [tuple(r) for r in conn.execute('SELECT balance,transfer_budget,wage_bill_weekly FROM clubs ORDER BY id')]


def test_accept_is_persisted_and_cannot_repeat(career):
    conn, mid = career
    assert decide_offer(conn,mid,'accepted',TODAY,1) == 'accepted'
    assert conn.execute('SELECT club_id FROM players').fetchone()[0] == 2
    assert financials(conn)[:2] == [(11000,11000,0),(9000,9000,200)]
    database.close()
    conn = database.connect('offers')
    refresh_offers(conn,TODAY)
    assert decide_offer(conn,mid,'accepted',TODAY,1) == 'accepted'
    assert decide_offer(conn,mid,'declined',TODAY,1) == 'accepted'
    assert financials(conn)[:2] == [(11000,11000,0),(9000,9000,200)]


def test_reading_is_not_deciding_and_decline_is_final(career):
    conn, mid = career
    queries.mark_message_read(conn,mid)
    refresh_offers(conn,TODAY)
    assert get_offer(conn,mid)['status'] == 'pending'
    before = financials(conn)
    assert decide_offer(conn,mid,'declined',TODAY,1) == 'declined'
    assert decide_offer(conn,mid,'accepted',TODAY,1) == 'declined'
    assert financials(conn) == before


@pytest.mark.parametrize('cause',['date','owner','funds','budget'])
def test_stale_offer_expires_without_moving_money(career,cause):
    conn,mid=career
    today=TODAY
    if cause=='date':today += timedelta(days=7)
    if cause=='owner':conn.execute('UPDATE players SET club_id=3')
    if cause=='funds':conn.execute('UPDATE clubs SET balance=10 WHERE id=2')
    if cause=='budget':conn.execute('UPDATE clubs SET transfer_budget=10 WHERE id=2')
    conn.commit()
    before=financials(conn)
    assert decide_offer(conn,mid,'accepted',today,1)=='expired'
    assert financials(conn)==before


def test_accept_rolls_back_everything_on_write_failure(career):
    conn,mid=career
    conn.execute("CREATE TRIGGER fail_payment BEFORE UPDATE ON clubs BEGIN SELECT RAISE(ABORT, 'disk failure'); END")
    before=financials(conn)
    with pytest.raises(Exception,match='disk failure'):
        decide_offer(conn,mid,'accepted',TODAY,1)
    assert get_offer(conn,mid)['status']=='pending'
    assert conn.execute('SELECT club_id FROM players').fetchone()[0]==1
    assert financials(conn)==before


def test_legacy_letters_import_once_and_expire(career):
    conn,mid=career
    conn.execute('DELETE FROM incoming_offers')
    conn.commit()
    refresh_offers(conn,TODAY+timedelta(days=7))
    refresh_offers(conn,TODAY+timedelta(days=8))
    assert get_offer(conn,mid)['status']=='expired'
    assert conn.execute('SELECT COUNT(*) FROM incoming_offers').fetchone()[0]==1


def test_other_club_cannot_decide(career):
    conn,mid=career
    assert decide_offer(conn,mid,'accepted',TODAY,3)=='unavailable'
    assert get_offer(conn,mid)['status']=='pending'


def test_competing_bids_expire_when_one_is_accepted(career):
    conn, mid=career
    other=queries.insert_message(conn,InboxMessage(date=TODAY,subject='Second',body='TRANSFER_OFFER|1|1|3|1100|200',category='transfer'))
    decide_offer(conn,mid,'accepted',TODAY,1)
    assert get_offer(conn,other)['status']=='expired'


def test_offer_expires_at_window_close(career):
    conn,_=career
    mid=queries.insert_message(conn,InboxMessage(date=date(2025,8,30),subject='Late',body='TRANSFER_OFFER|1|1|2|1000|200',category='transfer'))
    assert get_offer(conn,mid)['expires_on']=='2025-09-01'
    refresh_offers(conn,date(2025,9,1))
    assert get_offer(conn,mid)['status']=='expired'


def test_free_agent_can_still_sign(career):
    conn,_=career
    conn.execute('UPDATE players SET club_id=NULL')
    conn.commit()
    queries.transfer_player(conn,1,0,2,0,200,current_date=TODAY)
    assert conn.execute('SELECT club_id FROM players').fetchone()[0]==2


@pytest.mark.parametrize('status',['accepted','declined','expired'])
@pytest.mark.parametrize('language',['en','ar'])
def test_resolved_letters_only_show_close(career,monkeypatch,status,language):
    from types import SimpleNamespace
    from src.ui import app
    from src.ui.screens.inbox import _show_message_detail
    from src.utils.localization import set_language,t
    from src.data.models import GameState
    conn,mid=career
    today=TODAY
    if status=='expired':
        today+=timedelta(days=7)
        refresh_offers(conn,today)
    else:decide_offer(conn,mid,status,today,1)
    monkeypatch.setattr(app,'app_state',SimpleNamespace(game_state=GameState(user_club_id=1,current_date=today)))
    dialogs=[]
    page=SimpleNamespace(width=390,height=844,show_dialog=dialogs.append)
    set_language(language)
    try:
        _show_message_detail(page,conn,queries.get_inbox(conn,1)[0])
        assert len(dialogs[0].actions)==1
        assert dialogs[0].actions[0].content==t('close_btn')
    finally:set_language('en')


def test_simultaneous_accept_callbacks_pay_once(career):
    from concurrent.futures import ThreadPoolExecutor
    conn,mid=career
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _: decide_offer(conn,mid,'accepted',TODAY,1),range(2)))
    assert results==['accepted','accepted']
    assert financials(conn)[:2]==[(11000,11000,0),(9000,9000,200)]
