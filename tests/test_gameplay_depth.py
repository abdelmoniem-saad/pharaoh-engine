from datetime import date

from src.core.board import evaluate_objective_progress
from src.core.media import create_weekly_board_brief_message
from src.core.transfers import Negotiation, negotiation_pacing_hint, negotiation_response_eta_days
from src.data.models import BoardObjective, Club


def _make_club(expectation: str = "top_4") -> Club:
    return Club(
        name="Test FC",
        short_name="TFC",
        city="Cairo",
        governorate="Cairo",
        season_expectation=expectation,
        board_objectives=[
            BoardObjective(description="Top 4 Finish", target="top_4", priority="high"),
            BoardObjective(description="Score 50+ league goals", target="score_50_goals", priority="medium"),
        ],
    )


def test_objective_progress_flags_on_track_and_at_risk_states() -> None:
    club = _make_club()

    progress = evaluate_objective_progress(
        club,
        position=6,
        total_teams=18,
        goals_for=20,
        goal_difference=5,
        season_progress=0.20,
    )

    assert progress[0].status == "at_risk"
    assert "top 4" in progress[0].detail.lower()
    assert progress[1].status == "on_track"


def test_objective_progress_flags_off_track_late_season() -> None:
    club = _make_club()

    progress = evaluate_objective_progress(
        club,
        position=10,
        total_teams=18,
        goals_for=18,
        goal_difference=-6,
        season_progress=0.85,
    )

    assert progress[0].status == "off_track"
    assert progress[1].status == "off_track"


def test_weekly_board_brief_includes_counts_and_confidence() -> None:
    club = _make_club("top_4")
    progress = evaluate_objective_progress(
        club,
        position=3,
        total_teams=18,
        goals_for=26,
        goal_difference=9,
        season_progress=0.45,
    )

    msg = create_weekly_board_brief_message(
        club_name=club.name,
        board_confidence=68,
        confidence_level="Stable",
        season_expectation=club.season_expectation,
        position=3,
        total_teams=18,
        progress=progress,
        current_date=date(2026, 10, 1),
    )

    assert msg.subject == "🏛️ Weekly Board Brief"
    assert "Confidence: 68/100 (Stable)" in msg.body
    assert "Expectation: Top 4 Finish" in msg.body
    assert "Board Summary:" in msg.body


def test_negotiation_pacing_hint_uses_eta_and_attempts() -> None:
    neg = Negotiation(
        id=1,
        player_id=10,
        player_name="Player A",
        from_club_id=2,
        from_club_name="Other FC",
        to_club_id=1,
        to_club_name="Test FC",
        phase="fee",
        status="pending",
        current_offer=1_000_000,
        asking_price=1_400_000,
        counter_price=0,
        wage_offer=0,
        current_wage=50_000,
        attempt=2,
        max_attempts=3,
        submitted_date="2026-08-10",
        respond_date="2026-08-12",
        direction="user_buying",
    )

    now = date(2026, 8, 11)
    assert negotiation_response_eta_days(neg, now) == 1
    hint = negotiation_pacing_hint(neg, now)
    assert "response expected tomorrow" in hint
    assert "1 fee attempt(s) remaining" in hint

