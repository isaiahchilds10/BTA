from bta.ui.market_catalog import eligible_players, player_eligible,market_entries

PLAYERS=[{'id':'1','name':'Quarterback','position':'QB'},
         {'id':'2','name':'Receiver','position':'WR'},
         {'id':'3','name':'Tight end','position':'TE'},
         {'id':'4','name':'Back','position':'RB'},
         {'id':'5','name':'Unknown','position':''},
         {'id':'6','name':'Linebacker','position':'LB'}]

def test_passers_only_qb():
    assert [p['id'] for p in eligible_players('NFL','passing_yards',PLAYERS)]==['1']

def test_receiving_excludes_qb():
    assert {p['id'] for p in eligible_players('NFL','receiving_yards',PLAYERS)}=={'2','3','4'}

def test_rushing_excludes_wr_te():
    assert {p['id'] for p in eligible_players('NFL','rushing_yards',PLAYERS)}=={'1','4'}

def test_unknown_role_not_assumed_eligible():
    assert not player_eligible('NFL','anytime_td',PLAYERS[4])

def test_nba_catalog_contains_requested_groups():
    from bta.ui.market_catalog import market_groups
    assert set(('Points','Threes','Rebounds','Assists','Combos','Defense','Game Lines')) <= set(market_groups('NBA'))
    assert len(market_entries('NBA','Combos')) >= 3
