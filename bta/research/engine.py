"""Deterministic, evidence-gated BTA engine. AI cannot award certification."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from math import sqrt
from typing import Any
from bta.domain import Selection, scripts_for, selection_hit, implied_probability, overlaps, utcnow
from bta.sources.espn import gamelog, rows_from_gamelog, SourceError, summary, roster
from bta.research.matchup import side_by_side, season_for
from bta.research.stress import sourced_scripts
from bta.research.gates import role_observation, quote_observation, independent_second_pass, candidate_screen, GATE_KEYS
from bta.sources.espn import team_schedule
from bta.config import setting
from bta.research.opponent import audit_nba_defense
from bta.sources.house_rules import validate_market_settlement

REQUIRED_FOR_CERTIFICATION = (
    "Authoritative current participation/injury and expected workload",
    "Verified exact market offer and applicable settlement rules",
    "Comparable current-season samples and role stability",
    "Opponent-adjusted matchup and scheme assessment",
    "Evidence-supported five-script verdicts and reverse critique",
    "Independent second-pass audit and validated source provenance",
)


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Descriptive 95% interval for observed hit fraction, NOT a forecast probability."""
    if n <= 0 or not 0 <= successes <= n:
        return None
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2*n)) / denom
    half = z / denom * sqrt(p*(1-p)/n + z*z/(4*n*n))
    return round(max(0, center-half), 4), round(min(1, center+half), 4)


def compute_history(selection: Selection, rows: list[dict]) -> dict:
    if selection.threshold is None or selection.market in {"moneyline", "spread", "total", "quarter_rushing_yards"}:
        return {"available": False, "reason": "This market requires a verified dedicated settlement/game model", "rows": []}
    # Exact threshold only; do not turn absent or malformed observations into zero.
    recent = rows[:10]
    if not recent:
        return {"available": False, "reason": "No comparable numeric game-log rows available", "rows": []}
    values = [float(r["value"]) for r in recent]
    outcomes = [selection_hit(v, float(selection.threshold), selection.direction, selection.inclusive) for v in values]
    hits = sum(x == "HIT" for x in outcomes)
    pushes = sum(x == "PUSH" for x in outcomes)
    n = len(values)
    margin = [v - float(selection.threshold) if selection.direction in {"OVER", "YES"} else float(selection.threshold)-v for v in values]
    games = [{**dict(recent[i]), "result": outcomes[i], "clearance_margin": round(margin[i], 2)} for i in range(n)]
    return {
        "available": True, "rows": games, "sample": n, "hits": hits, "pushes": pushes,
        "median": median(values), "min": min(values), "max": max(values),
        "median_clearance": round(median(margin), 2), "three_for_three": sum(x == "HIT" for x in outcomes[:3]) if n >= 3 else None,
        "wilson_descriptive": wilson_interval(hits, n),
        "not_probability": True,
    }


def script_audit(selection: Selection, _history: dict) -> list[dict]:
    """Do not invent script outcomes from aggregate logs; mark missing inputs clearly."""
    scripts = scripts_for(selection)
    return [{
        "scenario": s, "verdict": "NOT_ASSESSED",
        "mechanism": (
            "Needs quarterback/trenches/turnover-adjusted comparative evidence to evaluate outright win resilience."
            if selection.sport == "CFB" and selection.market == "moneyline" else
            "Needs team favorite status, actual role/usage and verified game-flow comparison to determine effect on exact threshold."
        ),
        "evidence_status": "MISSING", "source": "",
    } for s in scripts]


def admissible_grade(history: dict, scripts: list[dict], gates: dict, second_pass: bool = False) -> tuple[str, str]:
    """Pure qualification gate. Caller must provide internally established, independently checked gate states.
    No UI checkbox or LLM response is allowed to mark any gate true.
    """
    worse = sum(v.get("verdict") == "WORSE" for v in scripts)
    if worse >= 2 and all(v.get("verdict") in {"BETTER", "SAME", "MIXED", "WORSE"} and v.get("evidence_status")=="VERIFIED" for v in scripts):
        return "CUT", "Two or more evidence-backed WORSE script results"
    if not all(gates.get(k, False) for k in ("participation", "market", "settlement", "opponent", "script_evidence", "role", "provenance")):
        return "PENDING VERIFICATION", "Material verification gates are unresolved"
    if len(scripts) != 5 or any(s.get("verdict") == "NOT_ASSESSED" or s.get("evidence_status") != "VERIFIED" for s in scripts):
        return "PENDING VERIFICATION", "Not all game scripts have verified evidence"
    if gates.get('matchup_favorable') is False:
        return "CONDITIONAL", "Source-backed opponent matchup is materially adverse"
    if not history.get("available") or history.get("sample", 0) < 8:
        return "CONDITIONAL", "Insufficient comparable numerical performance sample"
    hits = history["hits"]
    n = history["sample"]
    margin = history["median_clearance"]
    if worse == 0 and hits == n and margin > 0 and second_pass and n >= 10 and gates.get("exceptional", False):
        return "TAIG", "Exceptional full-sample consistency and independently verified robustness"
    if worse <= 1 and hits >= n-1 and margin > 0 and second_pass:
        return "BTA+", "Strong comparable results and verified second-pass script resilience"
    if worse <= 1 and hits >= n-2 and margin > 0:
        return "BTA", "Qualifying supported record with limited verified scenario risk"
    return "CONDITIONAL", "Historical cushion or script evidence does not support strict approval"


def discover_market_context(selection: Selection) -> dict:
    """Best-effort, real third-party context. Never upgrades official injury/line gates.
    Game date, participating teams, ESPN roster IDs are used only when unambiguous.
    """
    context={"checked_at":utcnow(),"status":"UNAVAILABLE","sources":[],"athlete_id":"", 
             "athlete_team_id":"", "fixture_verified":False, "matchup_code":"",
             "team_comparison":None,"opponent_status":"NOT_VERIFIED","warnings":[],
             "team_abbreviations":{},"team_locations":{},"week":None}
    if not selection.game_id or not selection.game_id.isdigit():
        context['warnings'].append('Game identifier absent; select a displayed fixture for fuller automatic context')
        return context
    try:
        raw,url=summary(selection.sport,selection.game_id)
        context['sources'].append({"url":url,"provider":"ESPN public web summary","retrieved_at":utcnow(),"trust":"THIRD_PARTY"})
        competition=(((raw.get('header') or {}).get('competitions') or [{}])[0])
        teams=competition.get('competitors') or []
        week_obj=(raw.get('header') or {}).get('week') or competition.get('week') or {}
        if isinstance(week_obj,dict):
            week_value=week_obj.get('number') or week_obj.get('week')
        else:week_value=week_obj
        try:
            if isinstance(week_value,bool):raise ValueError()
            n=int(week_value)
            context['week']=n if 1<=n<=23 else None
        except (TypeError,ValueError):pass
        team_ids=[]
        team_names={}
        found=[]
        for team in teams:
            t=team.get('team') or {}
            ident=str(t.get('id') or '')
            side=team.get('homeAway','')
            if ident.isdigit() and side in ('away','home'):
                team_ids.append((side,ident))
                team_names[side]={'name':t.get('displayName') or t.get('name') or '',
                                  'abbreviation':t.get('abbreviation') or ''}
        if team_names.get('away') and team_names.get('home'):
            expected=f"{team_names['away']['name']} @ {team_names['home']['name']}"
            context['fixture_verified']=(expected.casefold().strip()==selection.game_label.casefold().strip())
            if not context['fixture_verified']:
                context['warnings'].append('Exact selected fixture label does not match the server-fetched event; certification blocked')
            a,h=team_names['away']['abbreviation'],team_names['home']['abbreviation']
            if a and h:context['matchup_code']=f'{a}@{h}'
            context['team_ids']=dict(team_ids)
            context['team_names']={side:data['name'] for side,data in team_names.items()}
            context['team_abbreviations']={side:data['abbreviation'] for side,data in team_names.items()}
            context['team_locations']={
                side:str(next((c.get('team') or {}).get('location') or (c.get('team') or {}).get('displayName') or ''
                         for c in teams if c.get('homeAway')==side))
                for side in ('away','home')}

        # Always bind athlete ID to the unique official fixture roster identity.
        # A user-entered numeric athlete_id alone must NEVER be accepted as proof.
        if selection.market not in ('moneyline','spread','total'):
            for _,ident in team_ids:
                try:
                    players,roster_url=roster(selection.sport,ident)
                    context['sources'].append({'url':roster_url,'provider':'ESPN public web roster',
                         'retrieved_at':utcnow(),'trust':'THIRD_PARTY'})
                    found.extend({**p,'team_id':ident} for p in players
                                 if p.get('name','').strip().casefold()==selection.subject.strip().casefold())
                except SourceError:continue
            if len(found)==1 and (not selection.athlete_id or selection.athlete_id==found[0]['id']):
                context['athlete_id']=found[0]['id']
                context['athlete_team_id']=found[0]['team_id']
            elif len(found)>1:
                context['warnings'].append('Ambiguous exact name across fixture rosters')
            else:
                context['warnings'].append('The player ID/name is not verified against a fixture roster')
        by_side=dict(team_ids)
        if by_side.get('away') and by_side.get('home'):
            comparison=side_by_side(selection.sport,by_side['away'],by_side['home'],selection.game_start)
            context['team_comparison']=comparison
            for t in comparison.get('teams',[]):
                if t.get('source_url'):
                    context['sources'].append({"url":t['source_url'],"provider":"ESPN team schedule","retrieved_at":utcnow(),"trust":"THIRD_PARTY"})
        context['status']='THIRD_PARTY_CONTEXT_AVAILABLE'
    except (SourceError,ValueError,KeyError,IndexError,TypeError) as exc:
        context['warnings'].append(f'Current matchup context unavailable ({type(exc).__name__})')
    return context


def analyze(selection: Selection, *, rows_override: list[dict] | None = None, source_override: str = "") -> dict:
    selection.validate()
    checked = utcnow()
    context=discover_market_context(selection) if rows_override is None else {"status":"EXTERNAL_SAMPLE","warnings":["Fixture context not verified"]}
    # All evidence is gathered server-side. Client toggles, reported athlete IDs,
    # and LLM narratives are never sources of certification.
    issue = ''
    source_url = source_override
    rows: list[dict] = []
    verified_player = bool(context.get('fixture_verified') and context.get('athlete_id'))
    if rows_override is not None:
        rows=rows_override
        issue='Externally supplied research sample is not a verified source'
    elif verified_player and selection.market not in {'moneyline','spread','total'}:
        try:
            season=season_for(selection.sport,selection.game_start)
            payload,source_url=gamelog(selection.sport,context['athlete_id'],season=season)
            rows=rows_from_gamelog(payload,selection.market,cutoff=selection.game_start)
            if not rows:issue='No unambiguous comparable upstream game-log values for this market'
        except (SourceError,ValueError,TypeError,KeyError) as exc:
            issue=f'Game-log retrieval not usable ({type(exc).__name__})'
    else:
        issue='Game/player identity and exact market-specific game logs not fully confirmed'

    history=compute_history(selection,rows)
    role=role_observation(selection,rows)
    team_games=[]; team_games_url=''
    if rows_override is None and verified_player and context.get('athlete_team_id'):
        try:
            team_games,team_games_url=team_schedule(selection.sport,context['athlete_team_id'],
                                                    season_for(selection.sport,selection.game_start))
            team_games=[r for r in team_games if not selection.game_start or r['date']<selection.game_start]
        except (SourceError,ValueError,TypeError,KeyError):
            pass
    nfl_weekly={}
    if (rows_override is None and selection.sport=='NFL' and verified_player and
        context.get('week') and context.get('athlete_team_id') and
        (not history.get('available') or history.get('sample',0)<8)):
        try:
            from bta.sources.nfl_weekly import nfl_weekly_observations
            from bta.research.football import join_nfl_weekly_events
            team_abbr=next((context.get('team_abbreviations',{}).get(side,'')
                for side,tid in (context.get('team_ids') or {}).items()
                if tid==context.get('athlete_team_id')),'')
            nfl_weekly=nfl_weekly_observations(selection.subject,team_abbr,selection.market,
                season_for('NFL',selection.game_start),context['week'])
            if nfl_weekly.get('state')=='HISTORICAL_WEEKLY_RESEARCH' and nfl_weekly.get('sample',0)>len(rows):
                rows=join_nfl_weekly_events(nfl_weekly['rows'],team_games)
                source_url=nfl_weekly['source_url']
                history=compute_history(selection,rows)
                role=role_observation(selection,rows)
                issue='nflverse weekly historical source, verified by exact roster/team name, not pregame frozen and not official availability'
        except Exception as exc:
            nfl_weekly={'state':'UNAVAILABLE','reason':f'Weekly data source exception ({type(exc).__name__})'}
    scripts=(sourced_scripts(selection,rows,team_games,team_games_url) if team_games
             else script_audit(selection,history))

    # The football evidence lane does not substitute for official participation,
    # market rules, or a verified primary-source quarterback report.
    football_evidence={}
    if rows_override is None and selection.sport in ('NFL','CFB') and context.get('fixture_verified'):
        from bta.research.football import football_market_evidence
        try:
            football_evidence=football_market_evidence(selection,context,cfbd_key=setting('CFBD_API_KEY'))
        except Exception as exc:
            football_evidence={'sport':selection.sport,'state':'UNAVAILABLE',
                               'reason':f'Football source unavailable ({type(exc).__name__})'}
        if selection.sport=='CFB' and selection.market=='moneyline' and football_evidence.get('scripts'):
            scripts=football_evidence['scripts']
    # NBA: check the exact named player against a league-published, timestamped
    # injury report. Missing from the report is NOT the same as confirmed active.
    availability={'state':'UNKNOWN','reason':'No official current participation report verified'}
    if (rows_override is None and selection.sport=='NBA' and verified_player
        and context.get('matchup_code') and selection.game_start):
        from bta.sources.nba_official import current_player_status
        availability=current_player_status(selection.subject,context['matchup_code'],selection.game_start)

    checked=utcnow()
    favorite_evidence={}
    quote_info={'state':'UNAVAILABLE','reason':'No verified current offered line','checked_at':checked}
    if (rows_override is None and context.get('fixture_verified') and selection.platform in ('FanDuel','DraftKings')
        and setting('SPORTSGAMEODDS_API_KEY')):
        try:
            from bta.sources.sportsgameodds import observed_game_odds,extract_quotes
            from bta.domain import Game
            names=dict((t.get('homeAway'),t.get('team') or {}) for t in
                       (((summary(selection.sport,selection.game_id)[0].get('header') or {})
                         .get('competitions') or [{}])[0].get('competitors') or []))
            game=Game(selection.game_id,selection.sport,selection.game_start,
                      names.get('away',{}).get('displayName',''),names.get('home',{}).get('displayName',''),
                      'pre')
            provider_event=observed_game_odds(game,setting('SPORTSGAMEODDS_API_KEY'))
            if provider_event:
                players=[]
                for side,tid in (context.get('team_ids') or {}).items():
                    raw_players,_=roster(selection.sport,tid)
                    players.extend({**p,'team_id':tid,'team':game.away if side=='away' else game.home}
                                   for p in raw_players)
                quote_candidates=extract_quotes(provider_event,selection.sport,selection.platform,players)
                if selection.sport=='NFL' and verified_player:
                    from bta.sources.sportsgameodds import favorite_from_moneyline_quotes
                    player_team=next((g.away if side=='away' else g.home
                          for side,tid in (context.get('team_ids') or {}).items()
                          if tid==context.get('athlete_team_id')), '')
                    favorite_evidence=favorite_from_moneyline_quotes(quote_candidates,
                          player_team=player_team,current_time=checked)
                    if favorite_evidence.get('state')=='OBSERVED_MARKET_FAVORITE' and team_games:
                        scripts=sourced_scripts(selection,rows,team_games,team_games_url,
                            player_team_is_favorite=favorite_evidence['player_team_is_favorite'],
                            favorite_source=favorite_evidence.get('source_url') or '')
                for quote in quote_candidates:
                    checked_quote=quote_observation(selection,quote,checked_at=checked)
                    if checked_quote['state']=='OBSERVED':
                        quote_info=checked_quote
                        break
        except Exception:
            # Odds service outage cannot be converted into a positive market gate.
            pass

    # A second, no-card bookmaker feed path: PropLine primary, ParlayAPI fallback.
    # Server fetch is mandatory: NEVER promote the selection's stored quote flags.
    if (rows_override is None and context.get('fixture_verified') and
        selection.platform in ('FanDuel','DraftKings') and
        (setting('PROPLINE_API_KEY') or setting('PARLAY_API_KEY')) and
        quote_info.get('state')!='OBSERVED'):
        try:
            from bta.sources.free_odds import fetch_quotes
            from bta.domain import Game
            teams=context.get('team_names') or {}
            g=Game(selection.game_id,selection.sport,selection.game_start,
                   teams.get('away',''),teams.get('home',''),'pre')
            known=[]
            if selection.market not in ('moneyline','spread','total'):
                for side,tid in (context.get('team_ids') or {}).items():
                    roster_rows,_=roster(selection.sport,tid)
                    known += [{**p,'team_id':tid} for p in roster_rows]
            fetched=fetch_quotes(g,known,selection.market)
            for quote in fetched['quotes']:
                observed=quote_observation(selection,quote,checked_at=utcnow())
                if observed['state']=='OBSERVED':
                    quote_info=observed
                    break
        except (ValueError,TypeError,KeyError,SourceError):
            # Failure must not enable the market/settlement gates.
            pass

    opponent={'state':'NOT_ASSESSED','reason':'Position-specific opponent information missing'}
    if (rows_override is None and verified_player and selection.sport=='NBA' and selection.team_role):
        own=context.get('athlete_team_id')
        other_ids=[tid for tid in (context.get('team_ids') or {}).values() if tid!=own]
        if len(other_ids)==1:
            opponent=audit_nba_defense(selection,other_ids[0],rows)
    terms=validate_market_settlement(selection) if quote_info.get('state')=='OBSERVED' else {
        'state':'NOT_VERIFIED','reason':'No jurisdiction-specific official bookmaker rules verified'}

    # Explicit, named gates, computed from server-fetched data; never client booleans.
    gates={
        'participation':(availability.get('state')=='OFFICIALLY_REPORTED' and availability.get('status')=='Available')
                         or (availability.get('state')=='NOT_LISTED' and availability.get('game_verified') is True
                         and availability.get('team_submitted') is True and role.get('state')=='SUPPORTED'),
        'market':quote_info.get('state')=='OBSERVED',
        'settlement':terms.get('state')=='DOCUMENTED_FOR_REGION',
        'opponent':opponent.get('state')=='ASSESSED',
        'matchup_favorable':opponent.get('matchup_label')!='ADVERSE' if opponent.get('state')=='ASSESSED' else None,
        'script_evidence':len(scripts)==5 and all(s.get('evidence_status')=='VERIFIED' for s in scripts),
        'role':role.get('state')=='SUPPORTED' and verified_player,
        'provenance':bool(rows_override is None and verified_player and source_url.startswith('https://')),
    }
    # Exceptional TAIG must be explicitly established, not inferred from 10/10
    # alone. This heuristic is a grading safeguard, NOT a calibrated probability.
    enough=bool(history.get('available') and history.get('sample',0)>=10 and
        history.get('hits')==history.get('sample') and history.get('pushes')==0)
    if enough and selection.threshold and selection.threshold>0:
        observed=[float(r['value']) for r in rows[:10]]
        safety=(min(observed)-selection.threshold if selection.direction in ('OVER','YES')
                else selection.threshold-max(observed))
        cushion_ratio=safety/selection.threshold
        gates['exceptional']=(cushion_ratio>=0.30 and role.get('sample',0)>=10
            and role.get('games_at_65pct_median',0)>=10
            and opponent.get('matchup_label')=='FAVORABLE'
            and (opponent.get('comparison_ratio') or 0)>=1.10
            and all(sc.get('verdict')!='WORSE' for sc in scripts))
    else:gates['exceptional']=False
    # A retrospective analysis performed after actual tipoff must not borrow
    # newly available reports or corrected final data to certify a pregame pick.
    try:
        tip=datetime.fromisoformat(selection.game_start.replace('Z','+00:00'))
        if tip.tzinfo is None:tip=tip.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc)>=tip:
            gates['provenance']=False
            gates['participation']=False
            gates['market']=False
    except (ValueError,TypeError,AttributeError):
        gates['provenance']=False
    audit=independent_second_pass(selection,history,scripts,gates,rows)
    grade,grade_reason=admissible_grade(history,scripts,gates,second_pass=(audit['status']=='PASS'))
    preliminary=candidate_screen(history,role,scripts)
    blockers=[f"{key.replace('_',' ').title()}: not independently verified" for key in GATE_KEYS if not gates[key]]
    if not history.get('available'):
        blockers.append('Exact-threshold comparable current-season player history unavailable')
    if availability.get('state') in ('OFFICIALLY_REPORTED', 'REPORT_INCOMPLETE', 'CONFLICTING'):
        if availability.get('status') not in (None,'Available'):
            blockers.append(f"NBA official report lists {availability.get('status')}; participation/workload uncertain")
    if rows_override is not None:
        blockers.append('External test rows are never certifying evidence')
    if selection.sport=='CFB' and selection.market=='moneyline':
        blockers.append('CFB QB, trenches, competition-adjusted edges and five distinct upset scripts not fully sourced')
    if selection.sport=='NFL':
        injury=(football_evidence.get('injury') or {})
        if injury.get('state') in ('REPORTED_SECONDARY','PRACTICE_ONLY','OUTDATED','CONFLICTING'):
            blockers.append('NFL league-authoritative active/inactive confirmation and expected workload still needed')

    status='PENDING EVIDENCE'
    if selection.game_status=='post':
        status='HISTORICAL / NOT ACTIONABLE'
    elif selection.game_status=='in':
        status='IN PLAY / PREGAME RESEARCH INCOMPLETE'
    elif grade in ('TAIG','BTA+','BTA'):
        status='SOURCE-GATED RESEARCH CERTIFIED'
    elif grade=='CUT':
        status='EVIDENCE-SUPPORTED CUT'
    elif grade=='CONDITIONAL':
        status='CONDITIONAL / NOT CERTIFIED'
    price=implied_probability(selection.american_odds)
    overview=('Real game-log and contextual sources have been checked, with evidence-specific gates shown below.'
             if history.get('available') else 'No defensible full-sample result; see the specific failed evidence checks.')
    if selection.market in {'anytime_td','quarter_rushing_yards'}:
        overview='Touchdown/quarter markets require dedicated red-zone or quarter-level evidence, not just whole-game totals.'
    if selection.market=='moneyline':
        overview='Outright-win research requires distinct QB, trenches, strength-of-schedule and adversity evidence.'
    return {
        'selection_id':selection.id,'checked_at':checked,'grade':grade,'status':status,
        'recommendation': 'CUT' if grade=='CUT' else 'PENDING' if grade=='PENDING VERIFICATION' else 'KEEP' if grade in ('BTA','BTA+','TAIG') else 'REVIEW',
        'summary':overview,'grade_reason':grade_reason,'source_context':context,
        'evidence_quality':'MODERATE' if history.get('available') and verified_player else 'LIMITED' if history.get('available') else 'INCOMPLETE',
        'history':history,'scripts':scripts,'worse_count':sum(s.get('verdict')=='WORSE' for s in scripts)
             if all(s.get('evidence_status')=='VERIFIED' for s in scripts) else None,
        'role_evidence':role,'official_availability':availability,'market_verification':quote_info,
        'opponent_evidence':opponent,'settlement_evidence':terms,
        'football_evidence':football_evidence, 'favorite_evidence':favorite_evidence,
        'nfl_weekly_evidence':{'state':nfl_weekly.get('state','UNAVAILABLE'),
            'source_url':nfl_weekly.get('source_url',''),'reason':nfl_weekly.get('reason','')},
        'verification_gates':{key:{'passed':bool(gates[key]),'reason':next((b for b in blockers if b.lower().startswith(key.replace('_',' ').lower())),'' )} for key in GATE_KEYS},
        'preliminary_screen':preliminary, 'blockers':blockers,'data_issue':issue,'source_url':source_url,
        'source_type':('nflverse weekly game stats (third-party, updated after game)' if nfl_weekly.get('state')=='HISTORICAL_WEEKLY_RESEARCH' and nfl_weekly.get('source_url')==source_url else 'ESPN public game log / third-party (not official injury evidence)') if source_url else 'NONE',
        'market_status':('EXACT QUOTE SERVER-REVERIFIED' if gates['market'] else 'USER ENTERED — OFFER NOT VERIFIED'),
        'market_observation':quote_info,
        'settlement_status':'OH FANDUEL STANDARD NBA RULES OBSERVED' if gates['settlement'] else 'TERMS NOT VERIFIED',
        'price_break_even':price,'model_true_probability':None,'positive_ev':None,
        'probability_validation':{'state':'NOT_SUPPORTED','reason':'No approved out-of-time calibrated market-specific pregame/live forecasting model'},
        'independent_audit':audit,'cutoff':selection.game_start,
        'failure_paths':['Normal lower playing time/volume or efficiency can defeat the exact threshold',
            'Material availability, role or matchup uncertainties remain until independently sourced',
            'An observed quote does not establish applicability of all settlement and void terms'],
        'base_case':f"Historical {history.get('hits','?')}/{history.get('sample','?')} exact-threshold hits; not a projected success probability",
        'adverse_case':'Review sourced scenario hit frequencies and explicit unresolved stress conditions',
        'reverse_case':'Reconstruct ordinary misses from full logs; absent scenario evidence is not proof of robustness',
    }


def assess_ticket(selections: list[Selection], reports: dict[str, dict]) -> dict:
    overlaps_out = []
    for i, first in enumerate(selections):
        for second in selections[i+1:]:
            reasons = overlaps(first, second)
            if reasons:
                overlaps_out.append({"a": first.id, "b": second.id, "a_name": first.subject, "b_name": second.subject, "reasons": reasons})
    qualified = [s for s in selections if reports.get(s.id, {}).get("grade") in ("TAIG", "BTA+", "BTA")]
    pending = [s for s in selections if reports.get(s.id, {}).get("grade") not in ("TAIG", "BTA+", "BTA", "CUT")]
    return {
        "total": len(selections), "qualified": len(qualified), "incomplete": len(pending),
        "cut": len(selections) - len(qualified) - len(pending),
        "overlaps": overlaps_out,
        "risk_summary": "Combined win probability unavailable: market-specific dependency-aware joint model has not passed out-of-time validation.",
        "what_if_remove_incomplete": {
            "original_legs": len(selections), "illustrative_remaining": len(selections)-len(pending),
            "note": "Illustration only; original ticket is unchanged.",
        },
    }
