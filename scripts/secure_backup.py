"""Encrypted backup plus isolated data-level restore drill.

Runs only in PRIVATE GitHub repositories. This is not a PostgreSQL disaster-recovery
restore: the owner must separately test restoring into another Supabase project.
"""
from __future__ import annotations
import base64,hashlib,json,os,sqlite3,tempfile
from datetime import datetime,timezone
from pathlib import Path
from cryptography.fernet import Fernet

TABLES=('members','tickets','ticket_versions','reports','jobs','shares','audit_events')

def snapshot(admin) ->dict:
    items={}
    for table in TABLES:
        rows=[];start=0
        while True:
            chunk=admin.table(table).select('*').range(start,start+499).execute().data or []
            rows.extend(chunk)
            if len(chunk)<500:break
            start+=500
        items[table]=rows
    return {'created_at':datetime.now(timezone.utc).isoformat(), 'schema':'bta-2.0-initial-v1','tables':items}

def encode_payload(data:dict,fernet_key:str)->bytes:
    serialized=json.dumps(data,sort_keys=True,ensure_ascii=False,default=str,separators=(',',':')).encode()
    digest=hashlib.sha256(serialized).hexdigest()
    package={'sha256':digest,'payload':base64.b64encode(serialized).decode()}
    return Fernet(fernet_key.encode()).encrypt(json.dumps(package).encode())

def decode_payload(blob:bytes,fernet_key:str)->dict:
    package=json.loads(Fernet(fernet_key.encode()).decrypt(blob))
    content=base64.b64decode(package['payload'])
    if hashlib.sha256(content).hexdigest()!=package['sha256']:
        raise ValueError('Snapshot checksum mismatch')
    return json.loads(content)

def isolated_integrity_test(data:dict)->dict:
    """Import encrypted snapshot into a detached temporary SQLite database for row reconciliation.
    Distinct from a real Postgres/RLS restore exercise; do not misrepresent this as one.
    """
    with tempfile.TemporaryDirectory() as directory:
        con=sqlite3.connect(str(Path(directory)/'restore-drill.sqlite'))
        try:
            for table,rows in data['tables'].items():
                if table not in TABLES:raise ValueError('Unexpected table')
                con.execute('create table "'+table+'" (record text not null)')
                for row in rows:
                    con.execute('insert into "'+table+'" values (?)',(json.dumps(row,sort_keys=True),))
            con.commit()
            counts={table:con.execute('select count(*) from "'+table+'"').fetchone()[0] for table in data['tables']}
            expected={table:len(rows) for table,rows in data['tables'].items()}
            if counts!=expected: raise ValueError('Isolated replay mismatch')
        finally:con.close()
    return counts

def main():
    if os.getenv('GITHUB_REPOSITORY_VISIBILITY','').lower()!='private':
        raise SystemExit('Refusing to export private member data to a public-repository artifact.')
    key=os.getenv('BTA_BACKUP_KEY','')
    if not key: raise SystemExit('BTA_BACKUP_KEY secret required')
    from bta.storage.cloud import make_client
    data=snapshot(make_client(service=True))
    output=Path(os.getenv('BTA_BACKUP_OUTPUT','/tmp/bta-backup.enc'))
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(encode_payload(data,key))
    restored=decode_payload(output.read_bytes(),key)
    counts=isolated_integrity_test(restored)
    # Never log email/row details, keys or full SQL content.
    print('Encrypted backup and isolated row-integrity replay:',counts)

if __name__=='__main__':main()
