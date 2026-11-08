"""Encrypted export + integrity inspection (not a complete Supabase auth/database restore).
Use ONLY for trusted owner-side staging. Do not upload unencrypted data or keys into source control.
"""
from __future__ import annotations
import os, json, hashlib, argparse
from datetime import datetime, timezone
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken
from bta.storage.cloud import make_client

TABLES = ("members", "tickets", "ticket_versions", "reports", "jobs", "shares", "audit_events")


def seal_snapshot(snapshot: dict, key: bytes) -> bytes:
    body = json.dumps(snapshot,sort_keys=True,ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")
    manifest = {"sha256": hashlib.sha256(body).hexdigest(), "body": body.decode("utf-8"), "format": "BTA-SNAPSHOT-v1"}
    return Fernet(key).encrypt(json.dumps(manifest).encode("utf-8"))


def inspect_snapshot(encrypted: bytes, key: bytes) -> dict:
    manifest = json.loads(Fernet(key).decrypt(encrypted))
    if manifest.get("format") != "BTA-SNAPSHOT-v1":
        raise ValueError("Unknown snapshot format")
    raw = manifest["body"].encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != manifest["sha256"]:
        raise ValueError("Snapshot integrity validation failed")
    return json.loads(raw)


def export_snapshot() -> dict:
    from bta.config import mode
    if mode() != "private":
        raise RuntimeError("Only private authenticated owner infrastructure supports database export")
    c = make_client(service=True)
    data = {"format":"BTA-export-v1","created_at":datetime.now(timezone.utc).isoformat(),"tables":{}}
    for table in TABLES:
        all_rows=[]
        page=0
        while True:
            chunk = c.table(table).select("*").range(page*400,(page+1)*400-1).execute().data or []
            all_rows += chunk
            if len(chunk)<400: break
            page+=1
        data["tables"][table]=all_rows
    # auth.users are NOT exported; this is not an end-to-end restorable database.
    data["known_limitations"] = "auth.users not included; migration/restore not implemented; mandatory full restore drill still blocked"
    return data


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",help="Destination for encrypted archive")
    parser.add_argument("--inspect",help="Validate encrypted archive checksum without printing member contents")
    args=parser.parse_args()
    raw_key=os.environ.get("BTA_BACKUP_FERNET_KEY", "")
    if not raw_key:
        raise SystemExit("BTA_BACKUP_FERNET_KEY required (do not write key to repository)")
    key=raw_key.encode("ascii")
    if args.output:
        result=seal_snapshot(export_snapshot(),key)
        path=Path(args.output)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(result)
        path.chmod(0o600)
        print("Encrypted snapshot written (NOT a tested database restore):",path)
    elif args.inspect:
        data=inspect_snapshot(Path(args.inspect).read_bytes(),key)
        print("Integrity OK. Encrypted member table counts:",{k:len(v) for k,v in data.get("tables",{}).items()})
    else:
        parser.error("Choose --output or --inspect")

if __name__ == "__main__":
    main()
