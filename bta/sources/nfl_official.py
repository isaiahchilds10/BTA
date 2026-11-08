"""Conservative official NFL injury-page reader.

NOTE: An HTML parser is an OPTIONAL observation layer, not a guaranteed
stable/authorized NFL API. If markup, team association, publication time, or
week identity is ambiguous, it fails closed instead of claiming official
confirmation. Website access and redistribution rules require hosted review.
"""
from __future__ import annotations
import re
from functools import lru_cache
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from bta.domain import utcnow
from bta.sources.nfl_injuries import normalized

URL='https://www.nfl.com/injuries/league/{season}/REG{week}'
ALLOWED={'www.nfl.com','nfl.com'}


def parse_official_nfl_html(html:str,*,player:str,team_name:str,season:int,week:int)->dict:
    base={'state':'UNVERIFIED','status':None,'source_class':'LEAGUE_PUBLISHED_PAGE',
          'official_verification':False,'reason':'NFL web report markup not safely identified'}
    if not html or len(html)>5_000_000 or not team_name or not player:return base
    soup=BeautifulSoup(html,'html.parser')
    # Avoid trusting an outdated cached page for the selected week.
    text=soup.get_text(' ',strip=True)
    match=re.search(r'\bInjuries\s*[-–:]?\s*WEEK\s+(\d+)\b',text,re.I)
    if not match or int(match.group(1))!=week:
        return {**base,'reason':'NFL page week not independently matched'}
    aliases={normalized(team_name)}
    # Official NFL team headings often use the nickname (e.g. 'Bears')
    # even though fixture identification uses the full name ('Chicago Bears').
    # Exact final-token matching is safe only because NFL nickname labels are
    # unique; never match substring labels such as 'New York'.
    parts=normalized(team_name).split()
    if len(parts)>=2: aliases.add(parts[-1])
    if len(parts)>=2 and parts[-2]=='49ers': aliases.add('49ers')
    found=[]
    for table in soup.select('table'):
        rows=table.find_all('tr')
        if not rows:continue
        header=[normalized(cell.get_text(' ',strip=True)) for cell in rows[0].find_all(['th','td'])]
        columns={'player':None,'game status':None}
        for key in columns:
            columns[key]=next((i for i,value in enumerate(header) if value==key),None)
        if any(v is None for v in columns.values()):continue
        # A table without an unambiguous team label is not certifying evidence.
        label=[]
        if table.get('aria-label'):label.append(table['aria-label'])
        caption=table.find('caption')
        if caption:label.append(caption.get_text(' ',strip=True))
        heading=table.find_previous(['h2','h3','h4','h5'])
        if heading:label.append(heading.get_text(' ',strip=True))
        if not any(normalized(v) in aliases for v in label):continue
        for row in rows[1:]:
            cells=[c.get_text(' ',strip=True) for c in row.find_all(['td','th'])]
            if len(cells)<=max(columns.values()):continue
            if normalized(cells[columns['player']])!=normalized(player):continue
            found.append(cells[columns['game status']].strip())
    if len(found)!=1:
        return {**base,'reason':'No single player row joined to exact team and week on league page'}
    status=found[0].upper().strip()
    allowed={'OUT','DOUBTFUL','QUESTIONABLE'}
    if status not in allowed:
        # A blank status doesn't mean active and a FULL practice is not a game designation.
        return {**base,'state':'OFFICIALLY_LISTED','reason':'Exact player row seen but no definitive game status; do not infer availability'}
    return {**base,'state':'OFFICIALLY_DESIGNATED','status':status,
            'official_verification':True,'reason':'League page lists a game designation; not active/inactive confirmation'}


@lru_cache(maxsize=16)
def _request_nfl_page(season:int,week:int,minute_bucket:int)->str:
    del minute_bucket
    if not (2020<=season<=2100 and 1<=week<=23):raise ValueError('Invalid league page season/week')
    url=URL.format(season=season,week=week)
    response=requests.get(url,timeout=12,headers={'Accept':'text/html',
                          'User-Agent':'BTA sports research/2.0'},allow_redirects=False)
    response.raise_for_status()
    if urlparse(response.url).hostname not in ALLOWED or len(response.content)>5_000_000:
        raise ValueError('Unapproved or oversized league page')
    return response.text


def official_nfl_observation(player:str,team_name:str,season:int,week:int|None)->dict:
    base={'state':'UNAVAILABLE','official_verification':False,
          'source_url':'','checked_at':utcnow(),
          'reason':'Verified current NFL league injury page unavailable'}
    if not isinstance(week,int) or isinstance(week,bool) or not 1<=week<=23:return base
    from time import time
    url=URL.format(season=season,week=week)
    try:
        html=_request_nfl_page(season,week,int(time()//900))
        return {**base,**parse_official_nfl_html(html,player=player,team_name=team_name,
                              season=season,week=week),'source_url':url,'checked_at':utcnow(),
                'publication_time':'UNKNOWN'}
    except (requests.RequestException,ValueError) as exc:
        return {**base,'source_url':url,'reason':f'Official NFL page retrieval unusable ({type(exc).__name__})'}
