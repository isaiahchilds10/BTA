"""nflverse historical/current NFL injury-report *transcription*.

nflverse publishes data derived from NFL weekly reports, but this is a third-party
copy. An entry is corroborating context only: it cannot certify current NFL
active status, unrestricted snaps, or an official source timestamp. The absence
of a name is not evidence that the player is healthy or active.
"""
from __future__ import annotations

from csv import DictReader
from datetime import datetime, timezone, timedelta
from functools import lru_cache
from io import StringIO
from urllib.parse import urlparse
import requests

from bta.research.gates import timestamp
from bta.domain import utcnow

URL_TEMPLATE = 'https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv'
HOSTS = {'github.com', 'objects.githubusercontent.com', 'release-assets.githubusercontent.com'}
MAX_BYTES = 20_000_000

class NFLInjuryError(RuntimeError):
    pass


def normalized(value: object) -> str:
    return ' '.join(str(value or '').casefold().replace('’', "'").replace('.', '').split())


def nfl_team_code(value: str) -> str:
    code=str(value or '').upper().strip()
    return {'JAX':'JAC','WSH':'WAS','LA':'LA','LAR':'LA','LV':'LV'}.get(code,code)


@lru_cache(maxsize=8)
def _load_csv(season: int, hour_bucket: int) -> tuple[list[dict], str]:
    del hour_bucket
    if not 2009 <= season <= 2100:raise NFLInjuryError('Invalid season')
    url=URL_TEMPLATE.format(season=season)
    try:
        response=requests.get(url,timeout=15,headers={'Accept':'text/csv','User-Agent':'BTA/2.0-source-reader'},
                              stream=True,allow_redirects=True)
        response.raise_for_status()
        if urlparse(response.url).scheme!='https' or urlparse(response.url).hostname not in HOSTS:
            raise NFLInjuryError('NFL injury download redirected to an unapproved host')
        content=bytearray()
        for chunk in response.iter_content(chunk_size=65_536):
            content.extend(chunk)
            if len(content)>MAX_BYTES:raise NFLInjuryError('Injury file exceeds size limit')
        raw=content.decode('utf-8-sig')
        rows=list(DictReader(StringIO(raw)))
        required={'season','week','team','full_name','report_status','date_modified'}
        if not rows or not required.issubset(rows[0]):
            raise NFLInjuryError('Injury feed schema is missing required columns')
        return rows,url
    except (requests.RequestException,UnicodeDecodeError) as exc:
        raise NFLInjuryError(f'Injury feed unavailable ({type(exc).__name__})') from exc


def nfl_injury_observation(player_name: str, team_abbr: str, season: int,
                           week: int|None, *, as_of: str|None = None,
                           snapshot_rows: list[dict]|None = None) -> dict:
    """Return dated, non-authoritative NFL injury context; no health inference.

    The optional snapshot_rows argument is for deterministic testing/offline
    replay. Production never treats caller-supplied rows as official evidence.
    """
    observed_at=utcnow()
    base={'state':'UNKNOWN','status':None,'source_class':'SECONDARY_TRANSCRIPTION',
          'official_verification':False,'observed_at':observed_at,'source_url':'',
          'reason':'Authoritative, current NFL participation not established'}
    if not isinstance(week,int) or isinstance(week,bool) or not 1<=week<=23 or not team_abbr:
        return {**base,'reason':'Verified season/week/team identity is required for injury lookup'}
    if snapshot_rows is None:
        try:
            rows,url=_load_csv(season,int(datetime.now(timezone.utc).timestamp()//3600))
        except NFLInjuryError as exc:
            return {**base,'reason':str(exc)}
    else:
        rows,url=snapshot_rows,URL_TEMPLATE.format(season=season)
    cutoff=timestamp(as_of) if as_of else datetime.now(timezone.utc)
    if cutoff is None:return {**base,'reason':'Unparseable as-of time; refuse injury chronology'}
    matches=[]
    for row in rows:
        try:
            if int(row.get('season') or -1)!=season or int(row.get('week') or -1)!=week:continue
        except (ValueError,TypeError):continue
        if nfl_team_code(row.get('team',''))!=nfl_team_code(team_abbr):continue
        if normalized(row.get('full_name'))!=normalized(player_name):continue
        changed=timestamp(row.get('date_modified',''))
        # Entries without a verifiable source update time are not eligible.
        if changed is None or changed>cutoff:continue
        matches.append((changed,row))
    if not matches:
        return {**base,'source_url':url,'state':'NOT_LISTED',
                'reason':'No matching dated injury row; this does NOT establish healthy or active'}
    newest=max(x[0] for x in matches)
    rows_latest=[x[1] for x in matches if x[0]==newest]
    statuses={normalized(r.get('report_status')).upper() for r in rows_latest if r.get('report_status')}
    if len(statuses)>1:
        return {**base,'state':'CONFLICTING','source_url':url,'updated_at':newest.isoformat(),
                'reason':'Same-timestamp rows disagree about game status'}
    status=next(iter(statuses),None)
    age=cutoff-newest
    if age>timedelta(days=4):
        state='OUTDATED'
    elif status:
        state='REPORTED_SECONDARY'
    else:
        state='PRACTICE_ONLY'
    return {**base,'state':state,'status':status,'source_url':url,
            'updated_at':newest.isoformat(),'hours_old':round(age.total_seconds()/3600,1),
            'primary_injury':rows_latest[0].get('report_primary_injury') or '',
            'practice_status':rows_latest[0].get('practice_status') or '',
            'reason':'nflverse republishes injury-report information; the current official game status, active/inactive list and workload require separate confirmation'}
