"""Official NBA public injury PDF reader; fail closed on ambiguous tables.

Sources: official.nba.com season injury report index; NBA-controlled ak-static.cms.nba.com
PDF. The league's designation is a reporting status, never proof of future
minutes, active-list inclusion or that a player missing from a report is healthy.
"""
from __future__ import annotations
from datetime import datetime,timezone,timedelta
from io import BytesIO
from urllib.parse import urljoin,urlsplit
from zoneinfo import ZoneInfo
import re
import requests

INDEX='https://official.nba.com/nba-injury-report-2026-27-season/'
PDF_HOST='ak-static.cms.nba.com'
ALLOWED={'Available','Probable','Questionable','Doubtful','Out'}


class InjurySourceError(RuntimeError):pass


def player_key(name:str)->str:
    name=' '.join(str(name or '').strip().split())
    if ',' in name:
        surname,first=name.split(',',1)
        name=f'{first.strip()} {surname.strip()}'
    return re.sub(r'[^a-z0-9]','',name.lower())


def pdf_row_status(rows:list[list[str]],*,matchup:str,game_date:str,player:str)->dict:
    """Require exact matchup/date/player on one unambiguous official PDF row."""
    target=player_key(player); current_game=''; current_date=''; seen=[]; team_submitted=True; found_game=False
    for raw in rows:
        cells=[re.sub(r'\s+',' ',str(x or '')).strip() for x in raw]
        if len(cells)<7:continue
        date,time,game,team,name,status,*rest=cells[:7]
        if date and re.search(r'\d{2}/\d{2}/\d{4}',date):
            current_date=re.search(r'\d{2}/\d{2}/\d{4}',date).group(0)
        if game and re.search(r'\b[A-Z]{2,3}@[A-Z]{2,3}\b',game):
            current_game=re.search(r'\b[A-Z]{2,3}@[A-Z]{2,3}\b',game).group(0)
        if current_game!=matchup or current_date!=game_date:continue
        found_game=True
        if 'NOT YET SUBMITTED' in ' '.join(cells).upper(): team_submitted=False
        if player_key(name)!=target:continue
        normalized=status.title().strip()
        if normalized not in ALLOWED:continue
        seen.append({'status':normalized,'team':team,'reason':' '.join(rest).strip()})
    if not found_game:return {'state':'MATCHUP_NOT_FOUND','reason':'Exact game/date not found in the official PDF'}
    if not team_submitted:return {'state':'REPORT_INCOMPLETE','reason':'Team has not submitted a required report'}
    if len(seen)>1 and len(set(x['status'] for x in seen))!=1:
        return {'state':'CONFLICTING','reason':'Conflicting player statuses in official report'}
    if seen:
        return {'state':'OFFICIALLY_REPORTED','status':seen[0]['status'],'team':seen[0]['team'],
                'reason':seen[0]['reason']}
    return {'state':'NOT_LISTED','game_verified':True,'team_submitted':True,
            'reason':"Both teams' game is present on the submitted report; the player has no named reported limitation. This is NOT official confirmation of full minutes or that the player will start."}


def _latest_link(html:str)->tuple[str,str]:
    # Do not follow arbitrary links or URLs returned by upstream page content.
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.urls=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a':
                href=dict(attrs).get('href','')
                if href:self.urls.append(href)
    parser=Links();parser.feed(html)
    files=[]
    for href in parser.urls:
        url=urljoin(INDEX,href)
        parts=urlsplit(url)
        if parts.scheme!='https' or parts.hostname!=PDF_HOST or parts.username or parts.password:continue
        match=re.search(r'/Injury-Report_(\d{4}-\d\d-\d\d)_(\d\d)_(\d\d)(AM|PM)\.pdf$',parts.path,re.I)
        if not match:continue
        day,hh,mm,am_pm=match.groups()
        try:
            local=datetime.strptime(f'{day} {hh}:{mm}{am_pm}', '%Y-%m-%d %I:%M%p').replace(tzinfo=ZoneInfo('America/New_York'))
        except ValueError:continue
        files.append((local,url))
    if not files:raise InjurySourceError('Official NBA report index has no allowed PDF links')
    latest,url=max(files,key=lambda p:p[0]);return url,latest.astimezone(timezone.utc).isoformat()


def _positioned_rows(page) -> list[list[str]]:
    """Fallback when the NBA PDF has horizontal separators but no vertical table grid."""
    words=page.extract_words(x_tolerance=2,y_tolerance=3)
    grouped=[]
    for word in sorted(words,key=lambda w:(round(w['top']/3)*3,w['x0'])):
        if not grouped or abs(grouped[-1][0]['top']-word['top'])>3:
            grouped.append([word])
        else:
            grouped[-1].append(word)
    rows=[]
    edges=(0,.14,.22,.31,.49,.67,.79,1.01)
    for words_at_line in grouped:
        cells=['']*7
        for word in sorted(words_at_line,key=lambda w:w['x0']):
            frac=word['x0']/page.width
            for i in range(7):
                if edges[i]<=frac<edges[i+1]:
                    cells[i]+= (' ' if cells[i] else '')+word['text']
                    break
        rows.append(cells)
    return rows


def current_player_status(player:str,matchup:str,game_start:str,*,now:datetime|None=None)->dict:
    """Server-only retrieval; never use a document published after a prediction cutoff."""
    now=now or datetime.now(timezone.utc)
    start=datetime.fromisoformat(game_start.replace('Z','+00:00'))
    if start.tzinfo is None:start=start.replace(tzinfo=timezone.utc)
    if now>=start:return {'state':'NOT_APPLICABLE','reason':'Do not use post-tipoff reports to rewrite pregame research'}
    try:
        resp=requests.get(INDEX,headers={'User-Agent':'BTA2.0-research/0.2'},timeout=12,allow_redirects=False)
        resp.raise_for_status()
        if len(resp.content)>2_500_000:raise InjurySourceError('Oversized NBA report index')
        url,stamp=_latest_link(resp.text)
        report_time=datetime.fromisoformat(stamp)
        # Require a reasonably current report and a game inside the report's temporal neighborhood.
        if not timedelta(0)<=now-report_time<=timedelta(hours=28):
            return {'state':'OUTDATED','reason':'Most recent official PDF is stale or future-dated','source_url':url,'published_at':stamp}
        doc=requests.get(url,headers={'User-Agent':'BTA2.0-research/0.2'},timeout=16,allow_redirects=False)
        doc.raise_for_status()
        if not doc.content.startswith(b'%PDF') or len(doc.content)>6_000_000:
            raise InjurySourceError('Unrecognized PDF data')
        import pdfplumber
        rows=[]
        with pdfplumber.open(BytesIO(doc.content)) as pdf:
            if len(pdf.pages)>30:raise InjurySourceError('Implausible official report length')
            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    for row in table:
                        if row:rows.append(row)
                rows.extend(_positioned_rows(page))
        game_date=start.astimezone(ZoneInfo('America/New_York')).strftime('%m/%d/%Y')
        found=pdf_row_status(rows,matchup=matchup,game_date=game_date,player=player)
        return {**found,'source_url':url,'published_at':stamp,'checked_at':now.isoformat(),
                'provider':'NBA official injury report','source_type':'OFFICIAL'}
    except Exception as exc:
        # In particular, table extractor may fail after a legitimate NBA PDF layout change.
        return {'state':'UNAVAILABLE','reason':f'Official report could not be verified ({type(exc).__name__})'}
