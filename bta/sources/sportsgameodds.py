"""Optional free-tier odds snapshots from SportsGameOdds (v2).

Source: https://sportsgameodds.com/docs/endpoints/getEvents
This adapter only displays *observed quotes* with explicit bookmaker/upstream timestamps.
It makes no assertion of licensing permission, actual bet acceptance, or settlement parity.
The no-cost Amateur plan is very limited: calls/objects must be budgeted in real deployments.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
from functools import lru_cache
from typing import Any
import re,time,requests
from bta.domain import Game,utcnow

BASE='https://api.sportsgameodds.com/v2/events'
LEAGUES={'NBA':'NBA','NFL':'NFL','CFB':'NCAAF'}
BOOKS={'FanDuel':'fanduel','DraftKings':'draftkings'}
STAT_TO_MARKET={
    'points':'points','threePointersMade':'three_pointers_made',
    'rebounds':'rebounds','assists':'assists','steals':'steals','blocks':'blocks',
    'points+rebounds+assists':'points_rebounds_assists',
    'points+rebounds':'points_rebounds','points+assists':'points_assists',
    'rebounds+assists':'rebounds_assists','blocks+steals':'steals_blocks',
    'passing_yards':'passing_yards','passing_touchdowns':'passing_touchdowns',
    'passing_attempts':'passing_attempts','passing_completions':'completions',
    'receiving_yards':'receiving_yards','receiving_receptions':'receptions',
    'rushing_yards':'rushing_yards','rushing_attempts':'rushing_attempts',
    'rushing+receiving_yards':'rushing_receiving_yards',
}
class OddsSourceError(RuntimeError): pass


def norm(value: str)->str:
    return re.sub(r'[^a-z0-9]','',str(value or '').lower())


def _date(text:str)->datetime|None:
    try:
        dt=datetime.fromisoformat(str(text).replace('Z','+00:00'))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (ValueError,TypeError):return None


def _name(team:dict)->str:
    names=team.get('names') or {}
    return (names.get('long') or names.get('medium') or team.get('name') or team.get('displayName') or '')


def find_matching_event(game:Game,events:list[dict])->dict|None:
    """Both home/away and scheduled start must align. No fuzzy team aliases."""
    matches=[]
    gd=_date(game.start_time)
    if gd is None:return None
    for event in events:
        if not isinstance(event,dict) or event.get('leagueID') != LEAGUES[game.sport]:continue
        teams=event.get('teams') or {}
        if norm(_name(teams.get('home') or {}))!=norm(game.home):continue
        if norm(_name(teams.get('away') or {}))!=norm(game.away):continue
        ed=_date(event.get('startTime'))
        if ed is None or abs((ed-gd).total_seconds())>4*3600:continue
        matches.append(event)
    return matches[0] if len(matches)==1 else None


@lru_cache(maxsize=160)
def _cached_events(sport:str,start_iso:str,key:str,bucket:int)->list[dict]:
    del bucket
    dt=_date(start_iso)
    if sport not in LEAGUES or dt is None:raise OddsSourceError('Invalid event request')
    params={'leagueID':LEAGUES[sport],
            'startsAfter':(dt-timedelta(hours=8)).isoformat(),
            'startsBefore':(dt+timedelta(hours=8)).isoformat(),
            'bookmakerID':'fanduel,draftkings',
            'includeAltLines':'false',
            'limit':25}
    try:
        r=requests.get(BASE,params=params,headers={'x-api-key':key,'Accept':'application/json'},timeout=14,allow_redirects=False)
        if r.status_code == 429:raise OddsSourceError('Free quota exhausted; return later or use exact manual line')
        if r.status_code in (401,403):raise OddsSourceError('Odds service key invalid or plan cannot access this endpoint')
        r.raise_for_status()
        if len(r.content)>5_000_000:raise OddsSourceError('Odds payload exceeded safety size')
        data=r.json()
        if data.get('success') is not True or not isinstance(data.get('data'),list):
            raise OddsSourceError('Odds provider returned unsuccessful response')
        return data['data']
    except requests.RequestException as exc:
        raise OddsSourceError(f'Odds provider unreachable ({type(exc).__name__})') from exc
    except ValueError as exc:
        raise OddsSourceError('Odds provider returned invalid JSON') from exc


def observed_game_odds(game:Game,key:str)->dict|None:
    if not key:return None
    events=_cached_events(game.sport,game.start_time,key,int(time.time()//600))
    return find_matching_event(game,events)


def _book_price(book_value:dict)->tuple[int|None,float|None]:
    odds=str(book_value.get('odds') or '')
    if not re.fullmatch(r'[+-]\d{3,4}',odds):return None,None
    try:
        num=int(odds)
        if -100<num<100:return None,None
        return num,None
    except ValueError:return None,None


def extract_quotes(event:dict,sport:str,book_name:str,known_players:list[dict])->list[dict]:
    """Render only timestamped, explicitly available, full-game offers.

    A player quote joins a verified position-bearing ESPN roster by exact normalized
    name; one-to-many and ambiguous joins are intentionally omitted.
    """
    book=BOOKS.get(book_name)
    if not book:return []
    by_name={}
    for p in known_players:
        by_name.setdefault(norm(p.get('name')),[]).append(p)
    source_players=event.get('players') or {}
    quotes=[]
    for odd in (event.get('odds') or {}).values():
        if not isinstance(odd,dict) or odd.get('periodID')!='game':continue
        market='';subject='';athlete_id='';team_id='';team_role='';target=None;direction='';inclusive=False
        stat=odd.get('statID')
        typ=odd.get('betTypeID')
        side=str(odd.get('sideID') or '').lower()
        entity=str(odd.get('statEntityID') or '')
        observed=(odd.get('byBookmaker') or {}).get(book)
        if not isinstance(observed,dict) or observed.get('available') is not True:
            continue
        updated=_date(observed.get('lastUpdatedAt'))
        if not updated:continue
        if updated>datetime.now(timezone.utc)+timedelta(minutes=5):continue
        if (datetime.now(timezone.utc)-updated).total_seconds()>25*60:
            continue  # Too old to display as a presently available offer.
        price,_=_book_price(observed)
        if price is None:continue
        if stat=='points' and entity in ('home','away','all'):
            if typ=='ml' and side in ('home','away') and entity==side:
                market='moneyline';direction='YES';subject=_name((event.get('teams') or {}).get(side) or {})
            elif typ=='sp' and side in ('home','away') and entity==side:
                market='spread';direction='YES';subject=_name((event.get('teams') or {}).get(side) or {})
                try:target=float(observed['spread'])
                except (KeyError,TypeError,ValueError):continue
            elif typ=='ou' and side in ('over','under') and entity=='all':
                market='total';direction=side.upper();subject='Game total'
                try:target=float(observed['overUnder'])
                except (KeyError,TypeError,ValueError):continue
            else:continue
        elif entity not in ('home','away','all') and typ in ('ou','yn'):
            market=STAT_TO_MARKET.get(stat,'')
            if sport=='NBA' and market not in {'points','rebounds','assists','three_pointers_made','steals','blocks',
                                               'points_rebounds_assists','points_rebounds','points_assists',
                                               'rebounds_assists','steals_blocks'}:continue
            if sport in ('NFL','CFB') and market not in {'passing_yards','passing_touchdowns','passing_attempts',
                'completions','rushing_yards','rushing_attempts','receiving_yards','receptions','rushing_receiving_yards'}:continue
            direction={'over':'OVER','under':'UNDER','yes':'YES','no':'NO'}.get(side,'')
            if not market or not direction:continue
            upstream=source_players.get(entity) or source_players.get(odd.get('playerID')) or {}
            player_name=upstream.get('name') or ' '.join([upstream.get('firstName',''),upstream.get('lastName','')]).strip()
            matched=by_name.get(norm(player_name),[])
            if len(matched)!=1:continue
            player=matched[0]
            from bta.ui.market_catalog import player_eligible
            if not player_eligible(sport,market,player):continue
            subject=player['name'];athlete_id=player['id'];team_id=player.get('team_id','');team_role=player.get('position','')
            if typ=='ou':
                try:target=float(observed['overUnder'])
                except (KeyError,TypeError,ValueError):continue
            else:continue  # Other yes/no settlement conditions need dedicated terms.
        else:continue
        if not subject:continue
        quotes.append({'market':market,'subject':subject,'direction':direction,'threshold':target,
                        'inclusive':inclusive,'american_odds':price,'platform':book_name,'athlete_id':athlete_id,
                        'team_id':team_id,'team_role':team_role,'source_name':'SportsGameOdds v2',
                        'market_source_url':'https://sportsgameodds.com/docs/endpoints/getEvents',
                        'market_observed_at':updated.isoformat(),'provider_market_id':str(odd.get('oddID') or ''),
                        'quote_status':'OBSERVED_NOT_SETTLEMENT_CERTIFIED'})
    return quotes


def favorite_from_moneyline_quotes(quotes:list[dict],*,player_team:str,
                                   current_time:str)->dict:
    """Infer *current pregame* favorite only from both exact timestamped book quotes.

    Never use final score to infer favoritism. Vig is not removed here because
    only the ordering is used; no true win probability is inferred.
    """
    from bta.domain import implied_probability
    from bta.research.gates import timestamp
    as_of=timestamp(current_time)
    if not as_of:return {'state':'UNVERIFIED','reason':'Clock timestamp missing'}
    moneylines=[q for q in quotes if q.get('market')=='moneyline' and q.get('direction')=='YES'
                and isinstance(q.get('american_odds'),int)]
    uniq={q.get('subject','').casefold():q for q in moneylines if q.get('subject')}
    if len(moneylines)!=2 or len(uniq)!=2:
        return {'state':'UNVERIFIED','reason':'Both exact pregame moneylines at the same sportsbook are required'}
    times=[timestamp(q.get('market_observed_at','')) for q in moneylines]
    if not all(times) or any(not 0 <= (as_of-t).total_seconds() <= 900 for t in times):
        return {'state':'UNVERIFIED','reason':'At least one moneyline quote is stale or timestamped in the future'}
    if abs((times[0]-times[1]).total_seconds())>300:
        return {'state':'UNVERIFIED','reason':'Pregame team quotes were not updated within a comparable window'}
    probs=[implied_probability(q['american_odds']) for q in moneylines]
    if any(p is None for p in probs) or abs(probs[0]-probs[1])<0.01:
        return {'state':'UNVERIFIED','reason':'No distinct, measurable market favorite'}
    favored=moneylines[0 if probs[0]>probs[1] else 1]
    if norm(player_team) not in {norm(q['subject']) for q in moneylines}:
        return {'state':'UNVERIFIED','reason':'Player team not bound to either market side'}
    return {'state':'OBSERVED_MARKET_FAVORITE','player_team_is_favorite':norm(favored['subject'])==norm(player_team),
            'favorite_team':favored['subject'],'checked_at':current_time,
            'source_url':favored.get('market_source_url'),
            'reason':'Observed sportsbook favorite direction, not a calibrated independent win probability'}
