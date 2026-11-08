from bta.research.engine import compute_history, wilson_interval, script_audit, admissible_grade, analyze, assess_ticket
from bta.domain import Selection


def test_history_not_forecast(player):
    rows=[{"date":f"2026-10-{i:02d}T00:00:00Z","event_id":str(i),"opponent":"X","value":v} for i,v in enumerate([45,35,29,0,37,49,20,38,43,40],1)]
    hist=compute_history(player,rows)
    assert hist["hits"]==9
    assert hist["three_for_three"]==3
    assert hist["median"]==37.5
    assert hist["not_probability"] is True
    assert hist["sample"]==10
    assert len(hist["rows"])==10
    assert wilson_interval(10,10)[0]<1


def test_missing_evidence_never_promoted(player):
    report=analyze(player,rows_override=[{"date":"2026-10-01T00:00:00Z","event_id":"1","opponent":"A","value":100}])
    assert report["grade"]=="PENDING VERIFICATION"
    assert report["model_true_probability"] is None
    assert report["worse_count"] is None
    assert len(report["scripts"])==5
    assert all(v["verdict"]=="NOT_ASSESSED" for v in report["scripts"])


def test_two_worse_strict_cut():
    scripts=[{"verdict":v,"evidence_status":"VERIFIED"} for v in ["WORSE","WORSE","BETTER","SAME","MIXED"]]
    grade,why=admissible_grade({},scripts,{})
    assert grade=="CUT" and "Two" in why


def test_historical_perfect_not_certified_without_verification():
    hist={"available":True,"hits":10,"sample":10,"median_clearance":80}
    scripts=[{"verdict":"BETTER","evidence_status":"VERIFIED"}]*5
    assert admissible_grade(hist,scripts,{},True)[0]=="PENDING VERIFICATION"


def test_full_explicit_gate_conditional_vs_certification():
    gates={key:True for key in ("participation","market","settlement","opponent","script_evidence","role","provenance")}
    hist={"available":True,"hits":9,"sample":10,"median_clearance":5}
    scripts=[{"verdict":"BETTER","evidence_status":"VERIFIED"}]*5
    assert admissible_grade(hist,scripts,gates,True)[0]=="BTA+"
    assert admissible_grade(hist,scripts,gates,False)[0]=="BTA"
    gates["participation"]=False
    assert admissible_grade(hist,scripts,gates,True)[0]=="PENDING VERIFICATION"


def test_ticket_review_preserves_original(player):
    b=Selection.new(**{k:v for k,v in player.asdict().items() if k not in {"id","created_at"}})
    b.threshold=30
    before=(player.threshold,b.threshold)
    audit=assess_ticket([player,b],{})
    assert audit["total"]==2
    assert audit["qualified"]==0
    assert audit["incomplete"]==2
    assert audit["overlaps"]
    assert (player.threshold,b.threshold)==before


def test_client_cannot_self_certify_market_by_boolean(player):
    player.market_verified=True
    player.settlement_verified=True
    r=analyze(player,rows_override=[])
    assert r["market_status"]=="USER ENTERED — OFFER NOT VERIFIED"
    assert r["settlement_status"]=="TERMS NOT VERIFIED"
    assert r["grade"]=="PENDING VERIFICATION"
