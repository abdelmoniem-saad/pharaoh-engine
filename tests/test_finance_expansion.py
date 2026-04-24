import pytest
from src.data.models import Club, ClubFinances
from src.core.finance import (
    calculate_matchday_attendance, 
    calculate_matchday_income,
    update_budgets,
    calculate_monthly_income,
    calculate_monthly_expenses
)

@pytest.fixture
def mock_club():
    finances = ClubFinances(
        balance=1_000_000,
        ticket_price=100,
        sponsorship_income_yearly=1_200_000,
        tv_revenue_yearly=2_400_000,
        wage_bill_weekly=10_000
    )
    return Club(
        id=1,
        name="Test Club",
        short_name="TC",
        city="Cairo",
        governorate="Cairo",
        reputation=100,
        stadium_capacity=20_000,
        fan_happiness=50,
        finances=finances,
        facilities_level=5
    )

def test_calculate_matchday_attendance(mock_club):
    # reputation 100/200 = 0.5, happiness 50 = +0 modifier. 50% of 20,000 = 10,000
    attendance = calculate_matchday_attendance(mock_club)
    assert attendance == 10_000

def test_attendance_with_happiness(mock_club):
    mock_club.fan_happiness = 100  # +10% modifier
    attendance = calculate_matchday_attendance(mock_club)
    assert attendance == 12_000  # 60% of 20,000

def test_calculate_matchday_income(mock_club):
    # 10,000 attendance * 100 ticket price = 1,000,000
    income = calculate_matchday_income(mock_club)
    assert income == 1_000_000

def test_update_budgets(mock_club):
    update_budgets(mock_club)
    # 1,000,000 matchday * 17 = 17,000,000
    # + 1,200,000 sponsorship + 2,400,000 TV = 20,600,000 total projected
    # Wage budget: 65% of 20.6M = 13,390,000 yearly
    # Weekly: 13,390,000 / 52 = 257,500
    assert mock_club.finances.wage_budget_weekly == 257_500
    # Transfer budget: 30% of 1,000,000 balance = 300,000
    assert mock_club.finances.transfer_budget == 300_000

def test_monthly_finances_calculation(mock_club):
    # Matchday monthly: 1M * 2 = 2M
    # Sponsorship: 1.2M / 12 = 100K
    # TV: 2.4M / 12 = 200K
    # Total monthly income: 2.3M
    income = calculate_monthly_income(mock_club)
    assert income == 2_300_000

    # Wages monthly: 10K * 4 = 40K
    # Stadium maintenance: 20K capacity * 5 = 100K
    # Facilities: 5 level * 25K = 125K
    # Total monthly expenses: 265K
    expenses = calculate_monthly_expenses(mock_club)
    assert expenses == 265_000
