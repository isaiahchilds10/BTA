"""Source-authority and chronology aware participation reconciliation.

A source being official does NOT imply the player will play or play full minutes.
This module refuses to infer active status from absent injury records, missing
reports, older designations or AI prose. It is usable by all three sports.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from bta.research.gates import timestamp

AUTHORITY = {'OFFICIAL_GAME_DAY': 5, 'OFFICIAL_LEAGUE': 4,
             'OFFICIAL_CONFERENCE': 4, 'OFFICIAL_TEAM': 3,
             'CREDIBLE_REPORTING': 2, 'SECONDARY_TRANSCRIPTION': 1}
CLEAR = {'AVAILABLE', 'ACTIVE'}
RESTRICTED = {'QUESTIONABLE', 'DOUBTFUL', 'GAME TIME DECISION', 'GTD', 'PROBABLE', 'LIMITED'}
OUT = {'OUT', 'INACTIVE', 'RULED OUT'}
PUBLISHERS = {
  'OFFICIAL_GAME_DAY': {'nfl.com','www.nfl.com','nba.com','www.nba.com',
                        'bigten.org','www.bigten.org','secsports.com','www.secsports.com',
                        'theacc.com','www.theacc.com','admin.theacc.com'},
  'OFFICIAL_LEAGUE': {'nfl.com','www.nfl.com','nba.com','www.nba.com',
                      'official.nba.com','ncaa.com','www.ncaa.com'},
  'OFFICIAL_CONFERENCE': {'bigten.org','www.bigten.org','secsports.com',
                           'www.secsports.com','theacc.com','www.theacc.com',
                           'admin.theacc.com'},
}



def reconcile_participation(observations: list[dict], *, game_start: str,
                            checked_at: str | None = None,
                            freshness_hours: float = 36,
                            known_official_team_hosts: set[str] | None = None) -> dict:
    """Return source-linked, chronology-safe status, never a role/workload guarantee.

    Only server-owned observation adapters may invoke this for production use;
    caller data is considered descriptive until independently retrieved.
    """
    cutoff = timestamp(game_start)
    checked = timestamp(checked_at) if checked_at else datetime.now(timezone.utc)
    if not cutoff or not checked:
        return {'state':'UNVERIFIED','eligible':False,'reason':'Unknown game clock or check time','sources':[]}
    asof = min(cutoff,checked)
    valid=[]; ignored=[]
    for raw in observations:
        authority = raw.get('source_class')
        issued = timestamp(raw.get('published_at') or raw.get('updated_at') or '')
        status = str(raw.get('status') or '').strip().upper().replace('_',' ')
        source_url = raw.get('source_url') or ''
        same_game = raw.get('game_id_verified') is True
        parts=urlparse(source_url)
        # Operator-supplied credentials/hostnames and model text are not proof.
        host_ok=(parts.scheme=='https' and parts.username is None and parts.password is None and
                 bool(parts.hostname) and (parts.hostname in PUBLISHERS.get(authority,set()) or
                 (authority=='OFFICIAL_TEAM' and parts.hostname in (known_official_team_hosts or set())) or
                 authority in ('CREDIBLE_REPORTING','SECONDARY_TRANSCRIPTION')))
        if (authority not in AUTHORITY or not issued or not host_ok
            or not same_game or issued>asof or issued<asof-timedelta(hours=freshness_hours)):
            ignored.append({'source_url':source_url,'reason':'Unverified identity, publication time, source, or age'})
            continue
        if status not in CLEAR | RESTRICTED | OUT:
            ignored.append({'source_url':source_url,'reason':'Unrecognized status; do not infer active'})
            continue
        valid.append({'status':status,'source_class':authority,'source_url':source_url,
                      'published_at':issued.isoformat(),'strength':AUTHORITY[authority]})
    if not valid:
        return {'state':'UNVERIFIED','eligible':False,'reason':'No current, game-matched dated participation finding',
                'sources':[],'ignored':ignored}
    top=max(x['strength'] for x in valid)
    relevant=[x for x in valid if x['strength']==top]
    newest=max(timestamp(x['published_at']) for x in relevant)
    current=[x for x in relevant if timestamp(x['published_at'])==newest]
    statuses={x['status'] for x in current}
    if len(statuses)>1:
        return {'state':'CONFLICTING','eligible':False,'reason':'Equal-authority, same-timestamp statuses conflict',
                'sources':current,'ignored':ignored}
    winner=next(iter(statuses))
    # A published designation is not the same as the official inactive list.
    verified = top>=3
    state=('OFFICIALLY_OUT' if winner in OUT and verified else
           'OFFICIALLY_AVAILABLE' if winner in CLEAR and verified else
           'OFFICIALLY_UNCERTAIN' if winner in RESTRICTED and verified else
           'REPORTED_ONLY')
    return {'state':state,'status':winner,'eligible':state=='OFFICIALLY_AVAILABLE',
            'workload_confirmed':False,'source_class':current[0]['source_class'],
            'reason':('A participation designation is not proof of unrestricted usage' if verified
                      else 'Secondary reporting does not establish official availability'),
            'sources':current,'ignored':ignored}
