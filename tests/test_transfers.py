import pytest
from datetime import date, timedelta
from src.core.transfers import (
    is_transfer_window_open, estimate_player_value, negotiate_fee,
    negotiation_response_eta_days, Negotiation
)
from src.data.models import Player, PlayerAttributes, PlayerContract
from src.utils.config import Position

def _make_player(ca=100, age=25, contract_expiry=None):
    if contract_expiry is None:
        contract_expiry = date(2026, 6, 30)
    return Player(
        id=1, name="Test Player", age=age,
        position=Position.CM,
        attributes=PlayerAttributes(),
        current_ability=ca, potential_ability=ca+20,
        contract=PlayerContract(wage_weekly=10000, contract_expiry=contract_expiry),
        fitness=100, morale=70, form=7.0
    )

def test_is_transfer_window_open():
    # Summer window: June 1 to Aug 31
    assert is_transfer_window_open(date(2025, 6, 1)) is True
    assert is_transfer_window_open(date(2025, 7, 1)) is True
    assert is_transfer_window_open(date(2025, 8, 15)) is True
    assert is_transfer_window_open(date(2025, 8, 31)) is True
    # Winter window: Jan 1 to Jan 31
    assert is_transfer_window_open(date(2026, 1, 1)) is True
    assert is_transfer_window_open(date(2026, 1, 31)) is True
    # Closed
    assert is_transfer_window_open(date(2025, 5, 31)) is False
    assert is_transfer_window_open(date(2025, 9, 1)) is False
    assert is_transfer_window_open(date(2025, 12, 31)) is False
    assert is_transfer_window_open(date(2026, 2, 1)) is False

def test_estimate_player_value_scales_with_ca():
    p_low = _make_player(ca=80)
    p_high = _make_player(ca=150)
    assert estimate_player_value(p_high) > estimate_player_value(p_low)

def test_estimate_player_value_scales_with_age():
    p_young = _make_player(ca=120, age=20)
    p_old = _make_player(ca=120, age=33)
    assert estimate_player_value(p_young) > estimate_player_value(p_old)

def test_estimate_player_value_scales_with_contract():
    base_date = date(2025, 1, 1)
    p_long = _make_player(ca=120, contract_expiry=date(2027, 6, 30))
    p_short = _make_player(ca=120, contract_expiry=date(2025, 3, 1)) # < 6 months
    assert estimate_player_value(p_long, base_date) > estimate_player_value(p_short, base_date)

def test_negotiate_fee_logic():
    asking = 1000000
    
    # 90%+ accepted
    accepted, counter = negotiate_fee(asking, 950000)
    assert accepted is True
    assert counter == 950000
    
    # <50% rejected flat
    accepted, counter = negotiate_fee(asking, 400000)
    assert accepted is False
    assert counter == asking
    
    # Counter offer sequence
    _, counter1 = negotiate_fee(asking, 700000, attempt=1)
    _, counter2 = negotiate_fee(asking, 700000, attempt=2)
    _, counter3 = negotiate_fee(asking, 700000, attempt=3)
    
    assert counter1 > counter2 > counter3
    assert counter3 >= 700000

def test_negotiation_response_eta():
    current = date(2025, 7, 1)
    neg = Negotiation(
        id=1, player_id=1, player_name="Test", 
        from_club_id=2, from_club_name="S", 
        to_club_id=3, to_club_name="B",
        phase="fee", status="pending",
        current_offer=100, asking_price=200, counter_price=200,
        wage_offer=0, current_wage=0,
        attempt=1, max_attempts=3,
        submitted_date="2025-07-01", respond_date="2025-07-03",
        direction="user_buying"
    )
    eta = negotiation_response_eta_days(neg, current)
    assert eta == 2
    
    # If past respond_date
    eta_past = negotiation_response_eta_days(neg, date(2025, 7, 5))
    assert eta_past == 0
