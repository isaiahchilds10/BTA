import pytest
from bta.ui.quickadd import parse_one,parse_bulk


def test_plus_exact_semantics():
    d=parse_one("Test Player 20+ receiving yards","NFL")
    assert (d["direction"],d["inclusive"],d["threshold"])==("YES",True,20)


def test_polymarket_no_exactly():
    d=parse_one("NO Test Player 100+ rushing yards","NFL")
    assert d["direction"]=="NO" and d["inclusive"] is True


def test_standard_over():
    d=parse_one("Test Player over 20.5 points","NBA")
    assert d["market"]=="points" and not d["inclusive"]


def test_ambiguous_doesnt_guess():
    with pytest.raises(ValueError): parse_one("Test Player is a lock","NFL")
    parsed,errors=parse_bulk("Test Player 20+ receiving yards\nSomeone 4.5 tds","NFL")
    assert len(parsed)==1 and len(errors)==1
