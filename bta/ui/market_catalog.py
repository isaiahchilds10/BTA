"""Sportsbook-style browsing taxonomy, not a claim that a bookmaker offers any quote.

The browser never invents betting lines or prices: it requests a user-entered exact
threshold when a compliant currently offered market is not independently available.
Position filters are conservative: unknown roles are excluded rather than guessed.
"""
from __future__ import annotations
from typing import Mapping

MARKET_GROUPS: dict[str, dict[str, tuple[tuple[str,str],...]]] = {
    'NBA': {
        'Points': (('Player points','points'),),
        'Threes': (('Three-pointers made','three_pointers_made'),),
        'Rebounds': (('Player rebounds','rebounds'),),
        'Assists': (('Player assists','assists'),),
        'Combos': (('Points + rebounds + assists','points_rebounds_assists'),
                   ('Points + rebounds','points_rebounds'),('Points + assists','points_assists'),
                   ('Rebounds + assists','rebounds_assists')),
        'Defense': (('Steals','steals'),('Blocks','blocks'),('Steals + blocks','steals_blocks')),
        'Game Lines': (('Moneyline','moneyline'),('Spread','spread'),('Total points','total')),
    },
    'NFL': {
        'Passing': (('Passing yards','passing_yards'),('Passing touchdowns','passing_touchdowns'),
                    ('Pass completions','completions'),('Passing attempts','passing_attempts')),
        'Receiving': (('Receiving yards','receiving_yards'),('Receptions','receptions')),
        'Rushing': (('Rushing yards','rushing_yards'),('Rushing attempts','rushing_attempts'),
                    ('Rushing + receiving yards','rushing_receiving_yards')),
        'Touchdowns': (('Anytime rushing/receiving touchdown','anytime_td'),),
        'Game Lines': (('Moneyline','moneyline'),('Spread','spread'),('Total points','total')),
    },
    'CFB': {
        'Game Lines': (('Moneyline','moneyline'),('Spread','spread'),('Total points','total')),
        'Passing': (('Passing yards','passing_yards'),),
        'Rushing': (('Rushing yards','rushing_yards'),),
        'Receiving': (('Receiving yards','receiving_yards'),),
    },
}
ROLE_ELIGIBILITY: dict[str, frozenset[str]] = {
    'passing_yards':frozenset({'QB'}), 'passing_touchdowns':frozenset({'QB'}),
    'passing_attempts':frozenset({'QB'}), 'completions':frozenset({'QB'}),
    'receiving_yards':frozenset({'WR','TE','RB','FB'}),
    'receptions':frozenset({'WR','TE','RB','FB'}),
    'rushing_yards':frozenset({'RB','FB','QB'}),
    'rushing_attempts':frozenset({'RB','FB','QB'}),
    'rushing_receiving_yards':frozenset({'RB','FB','QB'}),
    'anytime_td':frozenset({'QB','RB','FB','WR','TE'}),
}
GAME_LINES=frozenset({'moneyline','spread','total'})


def normalize_position(value: object) -> str:
    """Never infer position from a person's name or team; use explicit roster values."""
    if isinstance(value, Mapping):
        value = value.get('abbreviation') or value.get('shortName') or value.get('name') or ''
    key = str(value or '').upper().strip().replace('-', ' ')
    aliases = {'QUARTERBACK':'QB','RUNNING BACK':'RB','FULLBACK':'FB',
               'WIDE RECEIVER':'WR','TIGHT END':'TE', 'POINT GUARD':'PG',
               'SHOOTING GUARD':'SG','SMALL FORWARD':'SF','POWER FORWARD':'PF','CENTER':'C',
               'HALFBACK':'RB','H B':'RB','T B':'RB','HB':'RB','TB':'RB'}
    return aliases.get(key,key)


def player_eligible(sport: str, market: str, player: Mapping) -> bool:
    if market in GAME_LINES:
        return False
    if not player.get('id') or not player.get('name'):
        return False
    position=normalize_position(player.get('position'))
    if sport=='NBA':
        return position in {'PG','SG','SF','PF','C','G','F','G-F','F-G','F-C','C-F'}
    return position in ROLE_ELIGIBILITY.get(market, frozenset())


def eligible_players(sport: str, market: str, players: list[dict]) -> list[dict]:
    found={}
    for player in players:
        if player_eligible(sport,market,player):
            found[str(player['id'])]=player
    return sorted(found.values(), key=lambda p:(str(p.get('team','')),str(p.get('name',''))))


def market_groups(sport: str) -> list[str]:
    return list(MARKET_GROUPS[sport])


def market_entries(sport: str, group: str) -> tuple[tuple[str,str],...]:
    return MARKET_GROUPS[sport][group]
