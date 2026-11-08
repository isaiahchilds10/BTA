"""Insecure single-user local DEMO storage; NEVER deploy publicly as private multiuser storage."""
from __future__ import annotations
import sqlite3, json
from uuid import uuid4
from bta.config import setting
from bta.domain import utcnow

class LocalStore:
    uid = "demo-owner"
    role = "owner"

    def __init__(self):
        self.path = setting("BTA_DB_PATH", "./bta_demo.db")
        with self.connect() as db:
            db.executescript("""
            create table if not exists tickets (id text primary key, name text, state text, legs text, version integer, updated_at text);
            create table if not exists versions (id text primary key, ticket_id text, version integer, snapshot text, created_at text);
            create table if not exists reports (id text primary key, ticket_id text, selection_id text, report text, created_at text);
            create table if not exists jobs (id text primary key, ticket_id text, selection_id text, state text, retries integer, updated_at text);
            """)

    def connect(self):
        return sqlite3.connect(self.path, timeout=15)

    def list_tickets(self) -> list[dict]:
        with self.connect() as db:
            r = db.execute("select id,name,state,legs,version,updated_at from tickets order by updated_at desc").fetchall()
        return [{"id": a, "name": b, "state": c, "legs": json.loads(d), "version": e, "updated_at": f} for a,b,c,d,e,f in r]

    def create_ticket(self, name: str) -> dict:
        ticket = {"id": str(uuid4()), "name": name[:100], "state": "DRAFT", "legs": [], "version": 1, "updated_at": utcnow()}
        with self.connect() as db:
            db.execute("insert into tickets values (?,?,?,?,?,?)", (ticket["id"],ticket["name"],ticket["state"],"[]",1,ticket["updated_at"]))
            db.execute("insert into versions values (?,?,?,?,?)", (str(uuid4()),ticket["id"],1,json.dumps(ticket),utcnow()))
        return ticket

    def save_ticket(self, ticket: dict) -> dict:
        if len(ticket["legs"]) > 30:
            raise ValueError("Maximum 30 legs per slip")
        with self.connect() as db:
            current = db.execute("select version from tickets where id=?", (ticket["id"],)).fetchone()
            if not current or current[0] != ticket["version"]:
                raise ValueError("Ticket has changed. Reload to avoid overwriting someone else's edits.")
            new = dict(ticket, version=ticket["version"]+1, updated_at=utcnow())
            db.execute("update tickets set name=?, state=?, legs=?, version=?, updated_at=? where id=?", (new["name"],new["state"],json.dumps(new["legs"]),new["version"],new["updated_at"],new["id"]))
            db.execute("insert into versions values (?,?,?,?,?)", (str(uuid4()),new["id"],new["version"],json.dumps(new),utcnow()))
        return new

    def list_versions(self, ticket_id: str) -> list[dict]:
        with self.connect() as db:
            rows = db.execute("select version,snapshot,created_at from versions where ticket_id=? order by version desc",(ticket_id,)).fetchall()
        return [{"version": a, "snapshot": json.loads(b), "created_at": c} for a,b,c in rows]

    def add_report(self, ticket_id: str, selection_id: str, report: dict) -> None:
        with self.connect() as db:
            db.execute("insert into reports values (?,?,?,?,?)", (str(uuid4()),ticket_id,selection_id,json.dumps(report),utcnow()))

    def list_reports(self, ticket_id: str) -> dict[str, dict]:
        with self.connect() as db:
            rows = db.execute("select selection_id,report from reports where ticket_id=? order by created_at,id", (ticket_id,)).fetchall()
        return {a: json.loads(b) for a,b in rows}

    def add_job(self, ticket_id: str, selection_id: str) -> None:
        with self.connect() as db:
            db.execute("insert into jobs values (?,?,?,?,?,?)", (str(uuid4()), ticket_id, selection_id, "queued", 0, utcnow()))

    def list_jobs(self, ticket_id: str | None = None) -> list[dict]:
        query = "select id,ticket_id,selection_id,state,retries,updated_at from jobs"
        with self.connect() as db:
            if ticket_id:
                rows = db.execute(query + " where ticket_id=? order by updated_at desc",(ticket_id,)).fetchall()
            else:
                rows = db.execute(query + " order by updated_at desc").fetchall()
        return [dict(zip(("id","ticket_id","selection_id","state","retries","updated_at"), r)) for r in rows]

    def update_job(self, job_id: str, state: str) -> None:
        with self.connect() as db:
            db.execute("update jobs set state=?,updated_at=? where id=?",(state,utcnow(),job_id))
