"""NFL-published weekly injury roundup as a fallback reporting observation.

League editorial coverage has stronger provenance than social rumors but is
not a final official inactive list. Publication time and exact week/team/player
are required before the report can be treated as current context.
"""
from __future__ import annotations
import re
from functools import lru_cache
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from bta.domain import utcnow
from bta.research.gates import timestamp
from bta.sources.nfl_injuries import normalized

URL='https://www.nfl.com/news/nfl-week-{week}-injury-report-{season}-season'


def parse_nfl_editorial(html:str,*,team_nickname:str,player:str,week:int,season:int)->dict:
    base={'state':'UNVERIFIED','status':None,'source_class':'CREDIBLE_REPORTING',
          'reason':'League editorial report did not establish this exact team/player/status',
          'published_at':None,'game_id_verified':False}
    if not html or len(html)>4_000_000 or not team_nickname or not player:return base
    soup=BeautifulSoup(html,'html.parser')
    header_text=' '.join(h.get_text(' ',strip=True) for h in soup.select('h1,h2'))
    if not re.search(rf'\bweek\s+{week}\b',header_text,re.I) or str(season) not in header_text:
        return base
    meta=soup.select_one('meta[property="article:published_time"],meta[name="datePublished"],meta[itemprop="datePublished"]')
    published=(meta.get('content') if meta else '')
    if not timestamp(published):return {**base,'reason':'League article has no verifiable publication time'}
    team=normalized(team_nickname)
    hits=[]
    for heading in soup.find_all(['h2','h3','h4']):
        if normalized(heading.get_text(' ',strip=True)) not in (team,team.upper().casefold()):continue
        text=[]
        for following in heading.next_elements:
            if following is heading:continue
            if getattr(following,'name',None) in ('h2','h3','h4'):break
            if getattr(following,'name',None) in ('p','li'):
                text.append(following.get_text(' ',strip=True))
        for block in text:
            m=re.match(r'^\s*(OUT|DOUBTFUL|QUESTIONABLE)\s*:\s*(.+)',block,re.I)
            if not m:continue
            segment=normalized(m.group(2))
            name=normalized(player)
            # Name must be a whole phrase, not a substring of another surname.
            if re.search(r'(?<![a-z0-9])'+re.escape(name)+r'(?![a-z0-9])',segment):
                hits.append(m.group(1).upper())
    if len(hits)!=1:return {**base,'reason':'No unique status in dated weekly NFL editorial section'}
    return {**base,'state':'LEAGUE_EDITORIAL_STATUS','status':hits[0],
            'published_at':timestamp(published).isoformat(),
            'game_id_verified':False,
            'reason':'NFL-published editorial injury summary; not league game-day active/inactive verification'}


@lru_cache(maxsize=32)
def _fetch(week:int,season:int,bucket:int)->str:
    del bucket
    if not 1<=week<=23 or not 2020<=season<=2100:raise ValueError('Invalid NFL week/season')
    url=URL.format(week=week,season=season)
    resp=requests.get(url,timeout=11,allow_redirects=False,
                      headers={'User-Agent':'BTA research/2','Accept':'text/html'})
    resp.raise_for_status()
    if len(resp.content)>4_000_000 or urlparse(resp.url).hostname not in {'www.nfl.com','nfl.com'}:
        raise ValueError('Invalid NFL editorial response')
    return resp.text


def nfl_editorial_observation(*,player:str,team_nickname:str,week:int|None,season:int)->dict:
    from time import time
    if week is None:return {'state':'UNAVAILABLE','reason':'NFL week is not verified'}
    url=URL.format(week=week,season=season)
    try:
        raw=_fetch(week,season,int(time()//1800))
        return {**parse_nfl_editorial(raw,team_nickname=team_nickname,
             player=player,week=week,season=season),'source_url':url,'checked_at':utcnow()}
    except (ValueError,requests.RequestException) as exc:
        return {'state':'UNAVAILABLE','source_url':url,'checked_at':utcnow(),
                'reason':f'NFL editorial fallback unavailable ({type(exc).__name__})'}
