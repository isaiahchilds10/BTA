import pytest
from bta.domain import Selection

@pytest.fixture
def player():
    return Selection.new(sport="NFL",game_id="4012",game_label="A @ B",game_start="2026-11-08T18:00:00Z",
        subject="Test Player",market="receiving_yards",direction="YES",threshold=20,inclusive=True,
        athlete_id="12345",team_role="away")
