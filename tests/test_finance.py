"""
Tests for the financial module.
"""
from src.data.models import Club, ClubFinances
from src.core.finance import (
    calculate_monthly_income, calculate_monthly_expenses,
    monthly_cash_flow, can_afford_transfer, can_afford_wage,
)


def _make_club() -> Club:
    return Club(
        id=1, name="Test FC", short_name="TFC",
        city="Cairo", governorate="Cairo",
        reputation=150, facilities_level=7,
        finances=ClubFinances(
            balance=50000000,
            transfer_budget=20000000,
            wage_budget_weekly=2000000,
            wage_bill_weekly=1500000,
            matchday_income=800000,
            sponsorship_income_yearly=24000000,
            tv_revenue_yearly=12000000,
        ),
    )


class TestFinance:
    def test_monthly_income_positive(self):
        club = _make_club()
        income = calculate_monthly_income(club)
        assert income > 0

    def test_monthly_expenses_positive(self):
        club = _make_club()
        expenses = calculate_monthly_expenses(club)
        assert expenses > 0

    def test_cash_flow(self):
        club = _make_club()
        flow = monthly_cash_flow(club)
        assert isinstance(flow, int)

    def test_can_afford_transfer(self):
        club = _make_club()
        assert can_afford_transfer(club, 10000000)
        assert not can_afford_transfer(club, 100000000)

    def test_can_afford_wage(self):
        club = _make_club()
        assert can_afford_wage(club, 200000)
        assert not can_afford_wage(club, 1000000)

