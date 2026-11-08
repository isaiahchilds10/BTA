import pytest
from bta.domain import Selection, scripts_for, implied_probability, selection_hit, overlaps


def test_american_odds():
    assert implied_probability(-110) == pytest.approx(110/210)
    assert implied_probability(150) == pytest.approx(100/250)
    assert implied_probability(None) is None
    with pytest.raises(ValueError): implied_probability(-90)


def test_market_semantics_exact_and_no():
    assert selection_hit(100,100,"YES",True)=="HIT"
    assert selection_hit(100,100,"NO",True)=="MISS"
    assert selection_hit(99,100,"NO",True)=="HIT"
    assert selection_hit(100,100,"NO",False)=="HIT"
    assert selection_hit(100,100,"OVER",False)=="PUSH"
    assert selection_hit(100,100,"UNDER",False)=="PUSH"
    assert selection_hit(100,100,"UNDER",True)=="HIT"


def test_distinct_five_scripts(player):
    assert len(scripts_for(player))==5
    moneyline=Selection.new(sport="CFB",game_id="1",game_label="A @ B",game_start="2026-11-08T20:00:00Z",
        subject="Favorite",market="moneyline",direction="YES",threshold=None)
    assert "turnover" in " ".join(scripts_for(moneyline)).lower()
    assert "turnover" not in " ".join(scripts_for(player)).lower()
    assert len(scripts_for(Selection.new(sport="NBA",game_id="2",game_label="A @ B",game_start="",subject="B",market="points",direction="OVER",threshold=20.5)))==5


def test_correlated_nested(player):
    a=player
    b=Selection.new(**{k:v for k,v in player.asdict().items() if k not in {"id","created_at"}})
    b.threshold=30
    joined=" ".join(overlaps(a,b))
    assert "Nested" in joined and "Same game" in joined


def test_bogus_selection_rejected():
    with pytest.raises(ValueError):
        Selection.new(sport="NBA",game_id="",game_label="",game_start="",subject="X",market="receptions",direction="OVER",threshold=2).validate()
