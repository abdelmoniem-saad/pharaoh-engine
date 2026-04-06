"""
Financial modeling — budgets, income, expenses, and cash flow.

Phase 2 module — stub implementation for MVP.
"""

from __future__ import annotations

from src.data.models import Club


def calculate_matchday_attendance(club: Club) -> int:
    """Calculate attendance based on capacity, reputation, and fan happiness."""
    # Base attendance percentage: reputation (1-200) / 2 = 50% average
    base_percent = club.reputation / 200.0

    # Happiness impact (-10% to +10%)
    happiness_modifier = (club.fan_happiness - 50) / 500.0

    attendance_percent = max(0.1, min(1.0, base_percent + happiness_modifier))
    return int(club.stadium_capacity * attendance_percent)


def calculate_matchday_income(club: Club) -> int:
    """Revenue from a single home match."""
    attendance = calculate_matchday_attendance(club)
    return attendance * club.finances.ticket_price


def update_budgets(club: Club):
    """
    Board-set budget caps based on balance and projected income.
    """
    # 17 home games in a 18-team league
    projected_yearly_income = (
        (calculate_matchday_income(club) * 17)
        + club.finances.sponsorship_income_yearly
        + club.finances.tv_revenue_yearly
    )

    # Wage Cap: Board limits wages to 65% of projected revenue
    wage_limit_weekly = int((projected_yearly_income * 0.65) // 52)
    club.finances.wage_budget_weekly = max(
        wage_limit_weekly, club.finances.wage_bill_weekly
    )

    # Transfer Budget: 30% of current positive balance
    if club.finances.balance > 0:
        club.finances.transfer_budget = int(club.finances.balance * 0.3)
    else:
        club.finances.transfer_budget = 0


def calculate_monthly_income(club: Club) -> int:
    """Calculate total monthly income for a club."""
    f = club.finances
    # Use the calculated matchday income instead of the static field
    matchday_rev = calculate_matchday_income(club)
    matchday_monthly = matchday_rev * 2  # ~2 home games per month
    sponsorship_monthly = f.sponsorship_income_yearly // 12
    tv_monthly = f.tv_revenue_yearly // 12
    return matchday_monthly + sponsorship_monthly + tv_monthly


def calculate_monthly_expenses(club: Club) -> int:
    """Calculate total monthly expenses."""
    wage_monthly = club.finances.wage_bill_weekly * 4
    # Stadium maintenance scales with capacity
    stadium_maintenance = club.stadium_capacity * 5
    facilities_cost = club.facilities_level * 25000
    return wage_monthly + facilities_cost + stadium_maintenance


def monthly_cash_flow(club: Club) -> int:
    """Net monthly cash flow."""
    return calculate_monthly_income(club) - calculate_monthly_expenses(club)


def process_monthly_finances(club: Club) -> str:
    """Process end-of-month finances. Returns a summary message."""
    income = calculate_monthly_income(club)
    expenses = calculate_monthly_expenses(club)
    net = income - expenses

    club.finances.balance += net
    update_budgets(club)

    if net >= 0:
        return f"Monthly finances: +{net:,} EGP (Income: {income:,}, Expenses: {expenses:,})"
    else:
        return f"Monthly finances: {net:,} EGP (Income: {income:,}, Expenses: {expenses:,}) ⚠️"


def can_afford_transfer(club: Club, fee: int) -> bool:
    """Check if a club can afford a transfer fee."""
    return club.finances.transfer_budget >= fee


def can_afford_wage(club: Club, weekly_wage: int) -> bool:
    """Check if adding a wage would stay within budget."""
    return (
        club.finances.wage_bill_weekly + weekly_wage
    ) <= club.finances.wage_budget_weekly
