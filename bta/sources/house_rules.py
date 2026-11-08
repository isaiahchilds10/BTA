"""Small, explicit bookmaker terms registry, fail-closed on unsupported jurisdiction.

Only uses operator-hosted terms verified by a live TLS fetch. No claim of wagering
availability or jurisdictional applicability outside the user's chosen region.
"""
from __future__ import annotations
from functools import lru_cache
import requests
from bta.domain import Selection

FANDUEL_OH_2026='https://policies.fanduel.com/SB/OH/2026-07-22T12-49-10.html'
NBA_PLAYER_STATS={'points','rebounds','assists','three_pointers_made','steals','blocks',
                  'points_rebounds_assists','points_rebounds','points_assists',
                  'rebounds_assists','steals_blocks'}

@lru_cache(maxsize=8)
def _get_operator_terms(url:str)->str:
    if url!=FANDUEL_OH_2026:raise ValueError('Unsupported operator terms URL')
    r=requests.get(url,timeout=14,allow_redirects=False,headers={'Accept':'text/html','User-Agent':'BTA2.0/0.2'})
    r.raise_for_status()
    if len(r.content)>4_000_000:raise ValueError('Operator rules unexpectedly large')
    from html.parser import HTMLParser
    class Text(HTMLParser):
        def __init__(self):super().__init__();self.parts=[]
        def handle_data(self,data):self.parts.append(data)
    parser=Text();parser.feed(r.text)
    return ' '.join(' '.join(parser.parts).lower().split())


def validate_market_settlement(selection:Selection)->dict:
    """Recognize *only* standard OH FanDuel full-game NBA statistics for now."""
    base={'state':'NOT_VERIFIED','reason':'Official terms are missing, jurisdiction unknown or market unsupported','source_url':''}
    if (selection.platform!='FanDuel' or selection.jurisdiction!='OH' or selection.sport!='NBA'
            or selection.market not in NBA_PLAYER_STATS or selection.direction not in ('OVER','UNDER')
            or selection.inclusive or selection.threshold is None):return base
    try:rules=_get_operator_terms(FANDUEL_OH_2026)
    except (requests.RequestException,ValueError):return base
    required=('nba','player performance markets','overtime','official')
    if not all(term in rules for term in required):return base
    return {'state':'DOCUMENTED_FOR_REGION','reason':
            'Operator-hosted Ohio house rules retrieved for standard NBA full-game player-performance markets; '
            'special void/cancellation rules still apply and must be checked when triggered',
            'source_url':FANDUEL_OH_2026,'jurisdiction':'OH',
            'warning':'Only Ohio FanDuel rules; not confirmation of individual wager acceptance or current offered line'}
