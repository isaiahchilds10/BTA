import os
import pytest
from bta.storage.local import LocalStore


def test_demo_persists_and_preserves_versions(tmp_path,monkeypatch):
    monkeypatch.setenv("BTA_DB_PATH", str(tmp_path/"bta.db"))
    s=LocalStore()
    t=s.create_ticket("Research")
    assert len(s.list_tickets())==1
    t["name"]="Edited"
    updated=s.save_ticket(t)
    assert updated["version"]==2
    assert len(s.list_versions(t["id"]))==2
    assert s.list_versions(t["id"])[1]["snapshot"]["name"]=="Research"
    with pytest.raises(ValueError): s.save_ticket(t)
    assert len(LocalStore().list_tickets())==1


def test_30_leg_limit(tmp_path,monkeypatch):
    monkeypatch.setenv("BTA_DB_PATH",str(tmp_path/"limit.db"))
    s=LocalStore()
    t=s.create_ticket("Max")
    t["legs"]=[{"id":str(i)} for i in range(31)]
    with pytest.raises(ValueError): s.save_ticket(t)
