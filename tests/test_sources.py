from datetime import date
from bta.sources import espn
from bta.research.matchup import side_by_side,season_for


def test_scoreboard_normalizes_no_fake_events(monkeypatch):
    data={"events":[{"id":"4","date":"2026-11-08T18:00:00Z","status":{"type":{"state":"pre","shortDetail":"1:00 PM"}},"competitions":[{"competitors":[{"homeAway":"home","team":{"id":"2","displayName":"Home FC"}},{"homeAway":"away","team":{"id":"1","displayName":"Away FC"}}]}]}, {"id":"x","competitions":[]}]}
    monkeypatch.setattr(espn,"fetch",lambda *args,**kwargs:data)
    games,url=espn.scoreboard("NFL",date(2026,11,8))
    assert len(games)==1
    assert games[0].home=="Home FC" and games[0].source_status=="OBSERVED_THIRD_PARTY"
    assert "20261108" in url


def test_empty_scoreboard_does_not_invent(monkeypatch):
    monkeypatch.setattr(espn,"fetch",lambda *args,**kwargs:{"events":[]})
    games,_=espn.scoreboard("NBA")
    assert games==[]


def test_gamelog_cutoff_no_lookahead():
    data={"events":{"1":{"gameDate":"2026-11-01T00:00:00Z","opponent":{"abbreviation":"LAL"}},"2":{"gameDate":"2026-11-12T00:00:00Z","opponent":{"abbreviation":"BOS"}}},
        "seasonTypes":[{"categories":[{"labels":["MIN","PTS","REB","AST"],"events":[{"eventId":"1","stats":["30","22","4","5"]},{"eventId":"2","stats":["30","99","3","2"]}]}]}]}
    rows=espn.rows_from_gamelog(data,"points","2026-11-07T00:00:00Z")
    assert len(rows)==1 and rows[0]["value"]==22
    assert espn.rows_from_gamelog(data,"points_rebounds_assists","2026-11-07T00:00:00Z")[0]["value"]==31


def test_team_schedule_cutoff(monkeypatch):
    sample={"events":[{"id":"7","date":"2026-09-20T13:00:00Z","competitions":[{"status":{"type":{"state":"post"}},"competitors":[{"team":{"id":"10","displayName":"Team A"},"score":"35"},{"team":{"id":"11","displayName":"Team B"},"score":"17"}]}]}]}
    monkeypatch.setattr(espn,"fetch",lambda *a,**k:sample)
    rows,_=espn.team_schedule("CFB","10",2026)
    assert rows[0]["margin"]==18
    assert season_for("NFL","2027-01-10T00:00:00Z")==2026


def test_distinct_nfl_yards_categories_no_cross_contamination():
    data={"events":{"1":{"gameDate":"2026-10-01T00:00:00Z","opponent":{"abbreviation":"AAA"}}},
        "seasonTypes":[{"categories":[
            {"name":"passing","labels":["YDS","TD"],"events":[{"eventId":"1","stats":["320","2"]}]},
            {"name":"rushing","labels":["CAR","YDS"],"events":[{"eventId":"1","stats":["12","68"]}]},
            {"name":"receiving","labels":["REC","YDS"],"events":[{"eventId":"1","stats":["6","75"]}]}]}]}
    assert espn.rows_from_gamelog(data,"passing_yards")[0]["value"]==320
    assert espn.rows_from_gamelog(data,"rushing_yards")[0]["value"]==68
    assert espn.rows_from_gamelog(data,"receiving_yards")[0]["value"]==75
    assert espn.rows_from_gamelog(data,"receptions")[0]["value"]==6
