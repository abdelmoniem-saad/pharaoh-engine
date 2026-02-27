"""
Financial modeling — budgets, income, expenses, and cash flow.

Phase 2 module — stub implementation for MVP.
"""
from __future__ import annotations

from src.data.models import Club, ClubFinances


def calculate_monthly_income(club: Club) -> int:
    """Calculate total monthly income for a club."""
    f = club.finances
    matchday_monthly = f.matchday_income * 2  # ~2 home games per month
    sponsorship_monthly = f.sponsorship_income_yearly // 12
    tv_monthly = f.tv_revenue_yearly // 12
    return matchday_monthly + sponsorship_monthly + tv_monthly


def calculate_monthly_expenses(club: Club) -> int:
    """Calculate total monthly expenses."""
    wage_monthly = club.finances.wage_bill_weekly * 4
    facilities_cost = club.facilities_level * 50000  # Rough maintenance
    return wage_monthly + facilities_cost


def monthly_cash_flow(club: Club) -> int:
    """Net monthly cash flow."""
    return calculate_monthly_income(club) - calculate_monthly_expenses(club)


def process_monthly_finances(club: Club) -> str:
    """Process end-of-month finances. Returns a summary message."""
    income = calculate_monthly_income(club)
    expenses = calculate_monthly_expenses(club)
    net = income - expenses

    club.finances.balance += net

    if net >= 0:
        return f"Monthly finances: +{net:,} EGP (Income: {income:,}, Expenses: {expenses:,})"
    else:
        return f"Monthly finances: {net:,} EGP (Income: {income:,}, Expenses: {expenses:,}) ⚠️"


def can_afford_transfer(club: Club, fee: int) -> bool:
    """Check if a club can afford a transfer fee."""
    return club.finances.transfer_budget >= fee


def can_afford_wage(club: Club, weekly_wage: int) -> bool:
    """Check if adding a wage would stay within budget."""
    return (club.finances.wage_bill_weekly + weekly_wage) <= club.finances.wage_budget_weekly

