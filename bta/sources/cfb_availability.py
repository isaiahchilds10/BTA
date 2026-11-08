"""Official FBS availability *policy* registry and conservative report extraction.

SEC/ACC/Big Ten reports cover applicable conference contests, not every FBS
fixture. Many current reports are dynamic/PDF; unavailable extraction stays
unverified, not a fictional athlete clearance. A source link alone cannot
satisfy official-participation certification.
"""
from __future__ import annotations
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from bta.research.gates import timestamp
from bta.domain import utcnow

CONFERENCES={
  'SEC':{'hub':'https://www.secsports.com/fbreports','hours_before_kickoff':1.5,
         'policy':'https://www.secsports.com/reports'},
  'ACC':{'hub':'https://admin.theacc.com/sports/2025/8/28/availability-reporting.aspx',
         'hours_before_kickoff':2.0,'policy':'https://admin.theacc.com/sports/2025/8/28/availability-reporting.aspx'},
  'BIG TEN':{'hub':'https://bigten.org/news/2026/8/28/big-ten-announces-changes-to-football-availability-reporting-process.aspx',
         'hours_before_kickoff':2.0,'policy':'https://bigten.org/news/2026/8/28/big-ten-announces-changes-to-football-availability-reporting-process.aspx'},
}
HOSTS={'SEC':{'www.secsports.com','secsports.com'},
       'ACC':{'admin.theacc.com','theacc.com','www.theacc.com'},
       'BIG TEN':{'bigten.org','www.bigten.org'}}
STATUSES={'AVAILABLE','PROBABLE','QUESTIONABLE','DOUBTFUL','OUT',
          'GAME TIME DECISION','OUT (1ST HALF)'}


def availability_source_plan(conference: str | None, *, is_conference_game: bool) -> dict:
    conf=(conference or '').upper().replace('B1G','BIG TEN').strip()
    entry=CONFERENCES.get(conf)
    if not entry or not is_conference_game:
        return {'state':'NO_CONFERENCE_REPORT_ASSUMED','source_url':'',
                'reason':'Conference reports are not universal; seek official school/team updates and independent credible reporting'}
    return {'state':'OFFICIAL_HUB_IDENTIFIED','source_url':entry['hub'],
            'policy_url':entry['policy'],'game_day_report_expected_hours_before':entry['hours_before_kickoff'],
            'reason':'Hub/policy is verified, but this does not establish a published report or any individual status'}


def extract_conference_report(html: str, *, conference: str, fixture_label: str,
                              player_name: str, game_date: str,
                              report_published_at: str, source_url: str) -> dict:
    """Parse a *specific* dated, conference-hosted HTML report with exact fixture heading.

    Intentionally refuses to treat ambiguous report hubs, missing dates, PDFs,
    and player absence as official health clearance.
    """
    base={'state':'UNVERIFIED','status':None,'game_id_verified':False,'source_class':'OFFICIAL_CONFERENCE',
          'source_url':source_url,'published_at':report_published_at,
          'reason':'Individual official conference report not unambiguously parsed'}
    conf=(conference or '').upper().strip()
    if conf not in HOSTS or urlparse(source_url).hostname not in HOSTS[conf]:return base
    when=timestamp(report_published_at)
    expected=timestamp(game_date)
    if not html or len(html)>3_000_000 or not when or not expected or when>expected:
        return base
    soup=BeautifulSoup(html,'html.parser')
    norm=lambda t:' '.join(str(t or '').casefold().replace('’',"'").split())
    wanted=norm(player_name)
    fixture=norm(fixture_label)
    # Require fixture and start date near the relevant source content, not merely
    # an arbitrary multi-game hub mentioning both names somewhere.
    hits=[]
    for table in soup.select('table'):
        context=[]
        heading=table.find_previous(['h1','h2','h3','h4'])
        if heading:context.append(heading.get_text(' ',strip=True))
        caption=table.find('caption')
        if caption:context.append(caption.get_text(' ',strip=True))
        if table.get('aria-label'):context.append(table.get('aria-label'))
        # Fixture could be represented as 'X vs Y' or 'X @ Y' — no substring
        # guess from one school name permitted here.
        context_text=norm(' '.join(context))
        if fixture not in context_text:continue
        # Same teams can rematch; a generic fixture header is not proof of
        # which game this report describes. Require the dated header itself.
        formats=(expected.strftime('%Y-%m-%d'),expected.strftime('%m/%d/%Y'),
                 expected.strftime('%B %d, %Y').casefold())
        if not any(date.casefold() in context_text for date in formats):continue
        headings=[]
        for row in table.find_all('tr'):
            fields=[c.get_text(' ',strip=True) for c in row.find_all(['th','td'])]
            if not fields:continue
            if not headings:
                headings=[norm(v) for v in fields]
                if not any('status' in x for x in headings) or not any('player' in x or 'student-athlete' in x for x in headings):
                    headings=[]
                continue
            ip=next((i for i,h in enumerate(headings) if 'player' in h or 'student-athlete' in h),None)
            ist=next((i for i,h in enumerate(headings) if 'status' in h),None)
            if ip is None or ist is None or max(ip,ist)>=len(fields):continue
            if norm(fields[ip]) != wanted:continue
            status=fields[ist].strip().upper()
            if status in STATUSES:hits.append(status)
    if len(hits)!=1:return {**base,'reason':'No unique player status in fixture-specific conference report table'}
    return {**base,'state':'OFFICIAL_DESIGNATION','status':hits[0],
            'game_id_verified':True,'reason':'Matched player and fixture-specific dated conference HTML table; report time supplied by upstream metadata and must be verified by fetch adapter'}


def verify_official_report_url(url: str, conference: str) -> bool:
    p=urlparse(url)
    return p.scheme=='https' and p.username is None and p.password is None and p.hostname in HOSTS.get(conference.upper(),set())
