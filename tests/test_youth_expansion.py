import pytest
from src.data.models import Club, ClubFinances, Player, PlayerAttributes
from src.core.youth import (
    get_academy_description,
    generate_scouting_report,
    generate_youth_player
)

@pytest.fixture
def mock_club():
    return Club(
        id=1,
        name="Al Ahly",
        short_name="AHL",
        city="Cairo",
        governorate="Cairo",
        reputation=180,
        stadium_capacity=75_000,
        academy_tier=1,
        finances=ClubFinances()
    )

def test_get_academy_description():
    assert get_academy_description(1) == "Elite Academy (World Class)"
    assert get_academy_description(4) == "Minimal Facilities (Local)"

def test_generate_scouting_report():
    player = Player(
        name="Ahmed Youth",
        age=17,
        position="ST",
        potential_ability=170,
        attributes=PlayerAttributes(pace=15, finishing=14)
    )
    report = generate_scouting_report(player)
    assert "⭐⭐⭐⭐⭐" in report
    assert "Pace" in report or "Finishing" in report

def test_generate_youth_player(mock_club):
    player = generate_youth_player(mock_club)
    assert player.age in [16, 17, 18]
    assert player.club_id == mock_club.id
    # Tier 1 should result in high PA
    assert player.potential_ability >= 145 # 100 + (4-1)*15
