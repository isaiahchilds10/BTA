"""Free-plan odds adapters with conservative exact identity and timestamp checks.

Supported sources: PropLine (nested bookmakers/markets/outcomes), ParlayAPI
(nested game lines, flat player props). A quote is a provider observation,
NOT proof that a bookmaker will accept a wager or honor particular rules.

No client-supplied verified flag can enter this module. Missing/ambiguous fixture,
unknown periods, incomplete boards and stale observations fail closed.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import re
import requests
from bta.config import setting
from bta.domain import Game, utcnow
from bta.research.gates import timestamp

SPORT_KEYS = {
    'PropLine': {'NBA':'basketball_nba','NFL':'football_nfl','CFB':'americanfootball_ncaaf'},
    'ParlayAPI': {'NBA':'basketball_nba','NFL':'americanfootball_nfl','CFB':'americanfootball_ncaaf'},
}
# Only exactly recognized FULL-GAME markets. Unknown outcomes are not guessed.
MARKETS = {
    'h2h':'moneyline','spreads':'spread','totals':'total',
    'player_points':'points','player_rebounds':'rebounds','player_assists':'assists',
    'player_threes':'three_pointers_made','player_threes_made':'three_pointers_made',
    'player_3pt_made':'three_pointers_made','player_steals':'steals','player_blocks':'blocks',
    'player_points_rebounds_assists':'points_rebounds_assists',
    'player_points_rebounds':'points_rebounds','player_points_assists':'points_assists',
    'player_rebounds_assists':'rebounds_assists','player_steals_blocks':'steals_blocks',
    'player_pass_yds':'passing_yards','player_pass_tds':'passing_touchdowns',
    'player_pass_attempts':'passing_attempts','player_pass_completions':'completions',
    'player_rush_yds':'rushing_yards','player_rush_attempts':'rushing_attempts',
    'player_reception_yds':'receiving_yards','player_receptions':'receptions',
    'player_rush_reception_yds':'rushing_receiving_yards',
}
PROVIDER_HOSTS=('api.prop-line.com','parlay-api.com','api.parlay-api.com')
class FreeOddsUnavailable(RuntimeError):pass


def normalized(name: str) -> str:
    return re.sub(r'[^a-z0-9]','',str(name).lower())


def fixture_matches(event:dict,game:Game) -> bool:
    """Exact home/away and kickoff; no reverse fixture or fuzzy game identity."""
    if normalized(event.get('home_team','')) != normalized(game.home):return False
    if normalized(event.get('away_team','')) != normalized(game.away):return False
    kickoff=timestamp(event.get('commence_time'))
    own=timestamp(game.start_time)
    return bool(kickoff and own and abs((kickoff-own).total_seconds())<=1800)


def _get(url:str, key:str, params:dict, *, timeout=13):
    if not url.startswith(('https://api.prop-line.com/v1/','https://parlay-api.com/v1/')):
        raise FreeOddsUnavailable('Unexpected odds host')
    try:
        r=requests.get(url,headers={'X-API-Key':key,'Accept':'application/json'},params=params,timeout=timeout)
        if r.status_code in (401,403,429):
            raise FreeOddsUnavailable(f'Odds feed unavailable ({r.status_code}); quota, access or plan limit')
        r.raise_for_status()
        if len(r.content)>8_000_000:raise FreeOddsUnavailable('Oversized odds response')
        return r.json(),r.headers
    except (requests.RequestException, ValueError,TypeError) as exc:
        raise FreeOddsUnavailable('Odds request failed; source may be down or unavailable') from exc


def _price(value):
    try:
        if isinstance(value,bool) or value is None:return None
        n=int(value)
        return n if abs(n)>=100 and abs(n)<=100000 else None
    except (ValueError,TypeError):return None


def _num(value):
    try:
        if isinstance(value,bool) or value is None:return None
        v=float(value)
        return v if abs(v)<=100000 and __import__('math').isfinite(v) else None
    except (ValueError,TypeError):return None


def _athlete(name:str,players:list[dict]) -> dict | None:
    exact=[p for p in players if normalized(p.get('name',''))==normalized(name)]
    return exact[0] if len(exact)==1 else None


def _quote(*,provider:str, event:dict,game:Game, book:str,market_key:str,
           outcome_name:str, description:str,point,price,observed_at:str,
           players:list[dict], url:str, period:str='FULL', row_id:str='') -> dict | None:
    if period not in ('FULL','',None):return None
    m=MARKETS.get(market_key)
    if not m or m not in __import__('bta.domain',fromlist=['SPORT_MARKETS']).SPORT_MARKETS[game.sport]:return None
    if not fixture_matches(event,game):return None
    t=timestamp(observed_at)
    now=datetime.now(timezone.utc)
    if not t or t > now+timedelta(minutes=2) or now-t>timedelta(minutes=15):return None
    book=book.lower()
    if book not in ('fanduel','draftkings'):return None
    american=_price(price)
    if american is None:return None
    point=_num(point)
    name=str(outcome_name or '').strip()
    player=None; athlete_id=''; team_id='';team_role=''
    if m=='moneyline':
        if normalized(name) not in (normalized(game.home),normalized(game.away)):return None
        subject=game.home if normalized(name)==normalized(game.home) else game.away
        direction='YES'; point=None
    elif m=='spread':
        if point is None or normalized(name) not in (normalized(game.home),normalized(game.away)):return None
        subject=game.home if normalized(name)==normalized(game.home) else game.away
        direction='YES'
    elif m=='total':
        if name.lower() not in ('over','under') or point is None:return None
        subject=f'{game.away} @ {game.home}';direction=name.upper()
    else:
        if name.lower() not in ('over','under') or point is None:return None
        player=_athlete(description,players)
        if player is None:return None
        subject=player['name'];athlete_id=str(player['id']);team_id=str(player.get('team_id',''));team_role=str(player.get('position',''))
        direction=name.upper()
    # Outcome identity is a deterministic fingerprint of the *observed row*, not
    # a fabricated native bookmaker id. An explicit provider ID is preferred.
    ident=str(row_id or f"{event.get('id') or event.get('event_id')}:{book}:{market_key}:{normalized(subject)}:{direction}:{point}")
    return {'provider':provider,'source_name':provider,'platform':book.title().replace('Fanduel','FanDuel').replace('Draftkings','DraftKings'),
            'sport':game.sport,'subject':subject,'market':m,'direction':direction,
            'threshold':point,'inclusive':False,'american_odds':american,
            'athlete_id':athlete_id,'team_id':team_id,'team_role':team_role,
            'market_source_url':url,'market_observed_at':t.isoformat(),
            'provider_market_id':ident,'fixture_id':str(event.get('id') or event.get('event_id') or ''),
            'provider_market_key':market_key,'bookmaker':book,'period':'FULL'}


def parse_nested(event:dict,game:Game,players:list[dict],provider:str,url:str)->list[dict]:
    """PropLine and Parlay game-line responses are compatible nested structures."""
    if not fixture_matches(event,game):return []
    result=[]
    for book in event.get('bookmakers') or []:
        book_key=str(book.get('key','')).lower()
        for market in book.get('markets') or []:
            if market.get('suspended_at'):continue
            market_key=str(market.get('key',''))
            period=market.get('period','FULL')
            asof=market.get('last_update') or book.get('last_update')
            for outcome in market.get('outcomes') or []:
                q=_quote(provider=provider,event=event,game=game,book=book_key,market_key=market_key,
                    outcome_name=outcome.get('name'),description=outcome.get('description',''),
                    point=outcome.get('point'),price=outcome.get('price'),observed_at=asof,
                    players=players,url=url,period=period,
                    row_id=outcome.get('outcome_id') or outcome.get('book_outcome_id') or '')
                if q:result.append(q)
    return result


def parse_flat_props(rows:list[dict],game:Game,players:list[dict],url:str,
                    *,truncated:bool=False)->list[dict]:
    if truncated:return []  # Incomplete board cannot establish absence or full coverage.
    out=[]
    for row in rows:
        if not fixture_matches(row,game):continue
        if row.get('period')!='FULL':continue
        if row.get('is_dfs_flat_payout'):continue
        for side in ('over','under'):
            q=_quote(provider='ParlayAPI',event=row,game=game,book=row.get('bookmaker',''),
                market_key=row.get('market_key',''),outcome_name=side,
                description=row.get('player',''),point=row.get('line'),
                price=row.get(side+'_price'),observed_at=row.get('last_update'),players=players,url=url,
                row_id=f"{row.get('canonical_event_id') or row.get('event_id')}:{row.get('market_key')}:{row.get('player')}:{side}:{row.get('line')}")
            if q:out.append(q)
    return out


def configured()->tuple[str,...]:
    return tuple(name for name,key in (('PropLine','PROPLINE_API_KEY'),('ParlayAPI','PARLAY_API_KEY')) if setting(key))


def fetch_quotes(game:Game,players:list[dict],market:str|None=None)->dict:
    """Provider failover. No retries that multiply free API charges; explicit status.

    PropLine is fetched in one sport-wide bulk call, then matched by BOTH teams
    and start time. ParlayAPI game odds + flat props are different schemas.
    """
    attempts=[]
    for provider in configured():
        sport=SPORT_KEYS[provider].get(game.sport)
        if not sport:continue
        key=setting('PROPLINE_API_KEY') if provider=='PropLine' else setting('PARLAY_API_KEY')
        try:
            if provider=='PropLine':
                url=f'https://api.prop-line.com/v1/sports/{sport}/odds'
                requested=sorted(k for k,v in MARKETS.items() if v==market) if market else list(MARKETS)
                # Limit quota/bandwidth by requesting only the selected market.
                params={'markets':','.join(requested),'bookmakers':'fanduel,draftkings','max_age':900,
                        'includeBookIds':'true'}
                payload,_=_get(url,key,params)
                events=payload if isinstance(payload,list) else (payload.get('events') or payload.get('data') or [])
                matches=[e for e in events if isinstance(e,dict) and fixture_matches(e,game)]
                if len(matches)!=1:raise FreeOddsUnavailable('No unique exact game returned')
                quotes=parse_nested(matches[0],game,players,provider,url)
            else:
                quotes=[]
                if market in (None,'moneyline','spread','total'):
                    url=f'https://parlay-api.com/v1/sports/{sport}/odds'
                    payload,_=_get(url,key,{'markets':'h2h,spreads,totals','regions':'us','bookmakers':'fanduel,draftkings'})
                    events=payload if isinstance(payload,list) else []
                    matches=[e for e in events if fixture_matches(e,game)]
                    if len(matches)==1:
                        quotes=parse_nested(matches[0],game,players,provider,url)
                if market not in ('moneyline','spread','total'):
                    props_url=f'https://parlay-api.com/v1/sports/{sport}/props'
                    mk=sorted(k for k,v in MARKETS.items() if v==market) if market else []
                    params={'bookmakers':'fanduel,draftkings','limit':5000}
                    if mk:params['markets']=','.join(mk)
                    rows,headers=_get(props_url,key,params)
                    if isinstance(rows,list):quotes+=parse_flat_props(rows,game,players,props_url,
                        truncated=str(headers.get('x-result-truncated','false')).lower()=='true')
            if market:quotes=[q for q in quotes if q['market']==market]
            if quotes:return {'state':'OBSERVED','provider':provider,'quotes':quotes,'checked_at':utcnow(),'attempts':attempts}
            attempts.append(f'{provider}: no fresh exact offers for requested market')
        except (FreeOddsUnavailable,TypeError,KeyError,ValueError) as e:
            attempts.append(f'{provider}: {type(e).__name__}')
    return {'state':'UNAVAILABLE','quotes':[],'attempts':attempts,'checked_at':utcnow(),
            'message':'No exact fresh permitted offer found; use a manually entered research threshold'}
