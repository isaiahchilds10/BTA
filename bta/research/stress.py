"""Retrospective, source-linked stress evidence (NOT a synthetic simulation).

The five scripts are distinct for NBA/NFL/CFB. Historical score patterns are used
only when the athlete's numeric game log can be joined to the *same* finished game
by event ID. Scores never become claimed historic favorite odds. A scenario with
insufficient comparable games remains NOT_ASSESSED, rather than receiving a
fabricated BETTER/SAME/WORSE label.
"""
from __future__ import annotations
from statistics import median
from bta.domain import Selection, scripts_for, selection_hit

MIN_SCENARIO_GAMES = 3
MIN_TOTAL_GAMES = 8


def _not_assessed(name: str, reason: str, source: str = '') -> dict:
    return {'scenario': name, 'verdict': 'NOT_ASSESSED',
            'evidence_status': 'INSUFFICIENT', 'mechanism': reason,
            'sample': 0, 'hits': 0, 'source': source, 'examples': []}


def sourced_scripts(selection: Selection, history_rows: list[dict], team_games: list[dict],
                    team_source: str = '', *, player_team_is_favorite: bool|None = None,
                    favorite_source: str = '') -> list[dict]:
    """Use comparable finished games, never hypothetical win rates.

    NFL favorite/underdog labels cannot be derived from final score, so those
    scripts remain unverified pending contemporaneous historical closing lines.
    CFB moneyline needs the separate QB/turnover/trenches framework and is not
    replaced by a player-yardage script.
    """
    labels = scripts_for(selection)
    defaults = [_not_assessed(s, 'Insufficient verified scenario-specific performance data', team_source) for s in labels]
    if selection.sport == 'CFB' and selection.market == 'moneyline':
        for d in defaults:
            d['mechanism'] = 'Requires the CFB-specific opponent-adjusted QB, turnover, trenches and late-game adversity audit.'
        return defaults
    if selection.threshold is None or not history_rows or not team_games:
        return defaults
    by_event = {str(r['event_id']): r for r in team_games
                if r.get('event_id') and r.get('points_for') is not None
                and r.get('points_against') is not None and r.get('result') in ('W','L','T')}
    mapped = []
    for r in history_rows:
        g = by_event.get(str(r.get('event_id', '')))
        if not g or r.get('value') is None:
            continue
        outcome = selection_hit(float(r['value']),float(selection.threshold),
                                selection.direction,selection.inclusive)
        if outcome == 'PUSH':
            continue
        mapped.append({'event_id':str(r['event_id']), 'date':r.get('date', ''),
                       'value':float(r['value']), 'hit':outcome=='HIT',
                       'margin':float(g['margin']),
                       'points_for':float(g['points_for']),
                       'points_against':float(g['points_against']),
                       'total':float(g['points_for'])+float(g['points_against'])})
    if len(mapped) < MIN_TOTAL_GAMES:
        for d in defaults:
            d['mechanism'] = f'Only {len(mapped)} past game(s) linked by exact event ID; at least {MIN_TOTAL_GAMES} required.'
        return defaults
    total_med = median(g['total'] for g in mapped)
    baseline = sum(g['hit'] for g in mapped)/len(mapped)
    # For NBA, labels correspond to the player's team, not whichever team is favorite.
    if selection.sport == 'NBA':
        conditions = [
            lambda r:r['margin']>=15,
            lambda r:r['margin']<=-15,
            lambda r:abs(r['margin'])<=5,
            lambda r:r['total']<total_med,
            lambda r:r['total']>total_med,
        ]
    else:
        # The current *market-verified* favorite identifies which side of today's
        # matchup these analogous game environments represent. Historic games
        # are classified by actual player-team margin, not falsely labeled as
        # games in which that team was a pregame favorite.
        if isinstance(player_team_is_favorite,bool) and favorite_source.startswith('https://'):
            conditions=[(lambda r:r['margin']>=14) if player_team_is_favorite else (lambda r:r['margin']<=-14),
                        (lambda r:r['margin']<=-14) if player_team_is_favorite else (lambda r:r['margin']>=14),
                        lambda r:abs(r['margin'])<=7,
                        lambda r:r['total']<total_med,
                        lambda r:r['total']>total_med]
        else:
            conditions=[None,None,lambda r:abs(r['margin'])<=7,
                        lambda r:r['total']<total_med,lambda r:r['total']>total_med]
    result=[]
    for label,condition in zip(labels,conditions):
        if condition is None:
            result.append(_not_assessed(label,
                'Current favorite identity needs fresh same-game bookmaker quotes; historical final scores alone cannot establish a pregame favorite.',team_source))
            continue
        subset = [r for r in mapped if condition(r)]
        if len(subset) < MIN_SCENARIO_GAMES:
            row = _not_assessed(label,
                f'Only {len(subset)} comparable historical games under this condition (minimum {MIN_SCENARIO_GAMES}).',team_source)
            row['sample'] = len(subset)
            result.append(row)
            continue
        fraction = sum(r['hit'] for r in subset)/len(subset)
        diff = fraction-baseline
        # Classification describes observed historical robustness, not a scenario's future probability.
        if diff <= -0.25:
            label_verdict='WORSE'
        elif diff >= 0.20:
            label_verdict='BETTER'
        elif abs(diff) <= 0.10:
            label_verdict='SAME'
        else:
            label_verdict='MIXED'
        hits=sum(r['hit'] for r in subset)
        result.append({'scenario':label, 'verdict':label_verdict,
            'evidence_status':'VERIFIED' if team_source.startswith('https://') else 'SOURCE_MISSING',
            'mechanism':f'Observed {hits}/{len(subset)} exact-threshold hits in comparable finished games vs {sum(r["hit"] for r in mapped)}/{len(mapped)} overall; descriptive sensitivity, not a forecast. NFL blowout analogy uses current independently quoted favorite identity and historical actual game margins, not historical favorite claims.',
            'sample':len(subset),'hits':hits,'baseline_sample':len(mapped),
            'source':team_source, 'examples':[r['event_id'] for r in subset]})
    return result
