from bta.domain import Game
from bta.sources.sportsgameodds import find_matching_event,extract_quotes

G=Game(id='123',sport='NBA',start_time='2026-11-10T00:00:00Z',away='Houston Rockets',home='Phoenix Suns',state='pre')
E={'eventID':'x','leagueID':'NBA','startTime':'2026-11-10T00:00:00Z',
   'teams':{'home':{'names':{'long':'Phoenix Suns'}},'away':{'names':{'long':'Houston Rockets'}}},
   'players':{'JANE':'JANE'},
   'odds':{'points-all-game-ou-over':{'oddID':'points-all-game-ou-over','statID':'points','statEntityID':'all',
      'periodID':'game','betTypeID':'ou','sideID':'over','byBookmaker':{'fanduel':{'available':True,
        'odds':'-110','overUnder':'228.5','lastUpdatedAt':'2026-11-07T00:00:00Z'}}}}}

def test_exact_game_join():
    assert find_matching_event(G,[E])['eventID']=='x'
    swapped=dict(E, teams={'home':E['teams']['away'],'away':E['teams']['home']})
    assert find_matching_event(G,[swapped]) is None

def test_ambiguous_games_withheld():
    assert find_matching_event(G,[E,E]) is None

def test_absent_or_stale_quote_withheld():
    assert extract_quotes(E,'NBA','FanDuel',[])==[]

def test_unavailable_quote_withheld():
    import copy
    e=copy.deepcopy(E)
    e['odds']['points-all-game-ou-over']['byBookmaker']['fanduel']['available']=False
    assert extract_quotes(e,'NBA','FanDuel',[])==[]
