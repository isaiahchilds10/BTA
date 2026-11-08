"""Simple in-game market browser: game -> market family -> role-qualified player -> slip.

This is a *research selection browser*, not a licensed sportsbook market feed.
Never display guessed odds, limits, eligibility or an offer as verified.
"""
from __future__ import annotations
from datetime import datetime,timezone
from typing import Callable
from html import escape
from bta.config import setting
from bta.domain import Game, Selection, utcnow
from bta.sources.espn import roster, SourceError
from bta.ui.market_catalog import MARKET_GROUPS, GAME_LINES, eligible_players
import streamlit as st
from bta.sources.free_odds import configured as odds_configured, fetch_quotes


def _load_rosters(game:Game)->tuple[list[dict],list[str]]:
    """Best effort explicit positions; returns no fake active/inactive assumptions."""
    players=[]
    warnings=[]
    for side,tid,name in (('away',game.away_id,game.away),('home',game.home_id,game.home)):
        if not tid:
            warnings.append(f'{name}: team ID unavailable')
            continue
        try:
            list_players,url=roster(game.sport,str(tid))
            players += [dict(p,team=name,team_id=tid,side=side,roster_url=url) for p in list_players]
            if not list_players:
                warnings.append(f'{name}: no roster returned')
        except (SourceError,ValueError) as e:
            warnings.append(f'{name}: roster unavailable ({type(e).__name__})')
    return players,warnings


def render_market_browser(game:Game, *, store, add_leg:Callable[[dict,Selection],dict],fmt_time:Callable[[str],str])->None:
    st.markdown(f'<div class="bta-eyebrow">MATCHUP / MARKET BROWSER</div>',unsafe_allow_html=True)
    st.markdown(f'## {escape(game.away)}  <span style="color:#8f98ab">at</span>  {escape(game.home)}',unsafe_allow_html=True)
    a,b,c=st.columns([1,1,1])
    a.caption(f'{"LIVE" if game.state=="in" else "FINAL" if game.state=="post" else "SCHEDULED"} · {game.detail}')
    b.caption(f'Game: {fmt_time(game.start_time)}')
    c.caption(f'Score: {game.score or "not yet available"}')
    st.caption(f'Observed schedule/score: ESPN public web feed · checked {fmt_time(game.checked_at)} · player roster ≠ confirmed active lineup')
    if game.state!='pre':
        st.info('This game is already in progress or complete. New selections may not be actionable. Live observations do not overwrite prior pregame research.')
    group_names=list(MARKET_GROUPS[game.sport])
    group=st.segmented_control('Market category',group_names,default=group_names[0],key=f'category_{game.sport}_{game.id}',label_visibility='collapsed') or group_names[0]
    entries=list(MARKET_GROUPS[game.sport][group])
    labels=[label for label,_ in entries]
    market_label=st.selectbox('Market',labels,key=f'market_label_{game.sport}_{game.id}_{group}')
    market=dict(entries)[market_label]
    is_game=market in GAME_LINES
    subject=''
    athlete_id=''
    team_id=''
    team_role=''
    players=[]
    if not is_game:
        with st.spinner('Retrieving available team rosters'):
            players,warnings=_load_rosters(game)
        teams=st.segmented_control('Team',["Both teams",game.away,game.home],default='Both teams',key=f'team_{game.sport}_{game.id}_{group}',label_visibility='visible')
        choices=eligible_players(game.sport,market,players)
        if teams!='Both teams':
            choices=[p for p in choices if p.get('team')==teams]
        for warning in warnings:
            st.caption(warning)
        if not choices:
            st.warning('No players with an explicitly verified position were returned for this market. BTA will not guess who plays which role. You can still use Quick Add on My Slip with an exact player name.')
            return
        chosen_id=st.selectbox('Player', [p['id'] for p in choices],format_func=lambda k:next(f"{p['name']} · {p['position']} · {p['team']}" for p in choices if p['id']==k),key=f'player_{game.id}_{group}_{market}')
        chosen=next(p for p in choices if p['id']==chosen_id)
        subject=chosen['name'];athlete_id=chosen['id'];team_id=chosen['team_id'];team_role=chosen['position']
        st.caption('Roster identity and position observed from a third-party feed. Availability, expected minutes/snaps, betting terms and live offers still require separate verification.')
    elif market == 'total':
        subject=f'{game.away} @ {game.home}'
    else:
        team=st.selectbox('Select team',[game.away,game.home],key=f'side_{game.id}_{market}')
        subject=team
        team_id=game.away_id if team==game.away else game.home_id
    # Region determines which operator rules are applicable. Unknown never certifies terms.
    region=st.selectbox('Bookmaker rules region (optional)',('Unknown','OH'),
             key=f'book_region_{game.id}',help='Select only the state whose operator house rules actually apply. This does not place a wager.')
    jurisdiction='' if region=='Unknown' else region
    tickets=store.list_tickets()
    target_id=None
    if tickets:
        ids=[t['id'] for t in tickets]
        target_id=st.selectbox('Add to slip',ids,format_func=lambda i:next(f"{t['name']} · {len(t['legs'])}/30 legs" for t in tickets if t['id']==i),key=f'browser_slip_{game.id}')
    else:
        st.caption('Your first selection will create a new private slip automatically.')
    # Exactly observed offers, requested by user to respect no-card free quotas.
    if odds_configured():
        with st.expander('Live published markets · FanDuel / DraftKings',expanded=False):
            st.caption('Published third-party observations only. Not a guarantee that the book will accept a wager. Each quote is rechecked by the server before BTA certification.')
            cache_key=f'bta_free_quotes_{game.sport}_{game.id}_{market}'
            if st.button('Fetch real available lines',key=f'get_free_quotes_{game.id}_{market}'):
                with st.spinner('Checking free odds providers'):
                    st.session_state[cache_key]=fetch_quotes(game,players,market)
            observed=st.session_state.get(cache_key)
            if observed:
                if observed['state']!='OBSERVED':
                    st.info('No verified fresh quote. Manual threshold analysis remains available.')
                    with st.expander('Provider details'):
                        for reason in observed.get('attempts',[]):st.caption(reason)
                else:
                    st.caption(f"From {observed['provider']} · fetched {fmt_time(observed['checked_at'])}")
                    quotes=[q for q in observed['quotes'] if q['market']==market and
                            (is_game or q['subject'].casefold()==subject.casefold())]
                    if not quotes:st.info('No currently observed offer for this selection.')
                    else:
                        display=quotes[:80]
                        pick=st.selectbox('Offered selections',range(len(display)),
                            format_func=lambda j:(f"{display[j]['platform']} · {display[j]['subject']} · "
                                f"{display[j]['direction']} {display[j]['threshold'] if display[j]['threshold'] is not None else ''} "
                                f"· {display[j]['american_odds']:+d} · {fmt_time(display[j]['market_observed_at'])}"),
                            key=f'free_quote_{game.id}_{market}')
                        if st.button('＋ Add observed line',type='primary',key=f'free_add_{game.id}_{market}'):
                            q=display[pick]
                            try:
                                leg=Selection.new(sport=game.sport,game_id=game.id,game_label=f'{game.away} @ {game.home}',
                                    game_start=game.start_time,game_status=game.state,subject=q['subject'],
                                    market=q['market'],direction=q['direction'],threshold=q['threshold'],
                                    inclusive=q['inclusive'],platform=q['platform'],american_odds=q['american_odds'],
                                    athlete_id=q['athlete_id'],team_id=q['team_id'],team_role=q['team_role'],
                                    market_verified=False,settlement_verified=False,
                                    market_source_url=q['market_source_url'],market_observed_at=q['market_observed_at'],
                                    quote_source_name=q['source_name'],provider_market_id=q['provider_market_id'],
                                    jurisdiction=jurisdiction)
                                leg.validate()
                                target=next(t for t in tickets if t['id']==target_id) if target_id else store.create_ticket('My BTA Slip')
                                saved=add_leg(target,leg)
                                st.session_state.ticket_next=saved['id'];st.session_state.nav_next='My Slip'
                                st.rerun()
                            except (ValueError,KeyError,TypeError) as exc:
                                st.error(f'Unable to save this exact selection: {exc}')
    else:
        st.caption('Connect free PropLine or ParlayAPI keys to browse actual published offers. Exact manual lines remain available below.')
    st.markdown('#### Choose exact research threshold')
    st.caption('No current FanDuel, DraftKings, or Polymarket line is being claimed here. Enter the exact market and threshold shown on your own platform.')
    with st.form(f'browse_add_{game.sport}_{game.id}_{group}_{market}'):
        if market in {'moneyline','anytime_td'}:
            direction=st.selectbox('Contract direction',['YES','NO'],help='YES/NO settle according to the named contract, not an assumed conventional over/under.')
        else:
            direction=st.selectbox('Direction',['OVER','UNDER'],help='Exact price and settlement rules are not established by this browser.')
        threshold=None
        inclusive=False
        if market!='moneyline':
            line=st.text_input('Exact threshold (required)',placeholder='e.g. 20.5 or 25',help='Do not assume BTA is showing a verified sportsbook offer.')
            inclusive=st.checkbox('Inclusive threshold (e.g. YES 25+)',value=(market=='anytime_td'))
        else:
            line=''
        c1,c2=st.columns(2)
        with c1:
            platform=st.selectbox('Platform',['User-entered','FanDuel','DraftKings','Polymarket','Other'])
        with c2:
            odds_input=st.text_input('American odds (optional)',placeholder='-110 / +120')
        st.caption('Game lines use the named team or full-game total. Enter an offered spread with its sign (example: -3.5). Exact platform settlement remains unverified.')
        submitted=st.form_submit_button('＋ Add selection to My Slip',type='primary',use_container_width=True)
    if submitted:
        try:
            if not is_game and game.state=='post':
                raise ValueError('This fixture is complete; open a future matchup to add actionable player selections')
            if market != 'moneyline':
                if not line.strip():
                    raise ValueError('Enter the exact threshold before adding')
                threshold=float(line)
            if odds_input.strip():
                odds=int(odds_input.strip())
            else:odds=None
            selection=Selection.new(
                sport=game.sport,game_id=game.id,game_label=f'{game.away} @ {game.home}',
                game_start=game.start_time,game_status=game.state,
                subject=subject,market=market,direction=direction,threshold=threshold,
                inclusive=(True if market=='anytime_td' else inclusive),
                platform=platform,american_odds=odds,athlete_id=athlete_id,
                team_id=team_id,team_role=team_role,market_verified=False,settlement_verified=False,
                notes='',jurisdiction=jurisdiction,
            )
            selection.validate()
            if target_id:
                target=next(t for t in tickets if t['id']==target_id)
            else:
                target=store.create_ticket('My BTA Slip')
            if any(l.get('game_id')==selection.game_id and l.get('subject')==selection.subject
                    and l.get('market')==selection.market and l.get('threshold')==selection.threshold
                    and l.get('direction')==selection.direction for l in target['legs']):
                raise ValueError('This exact selection is already on that slip')
            saved=add_leg(target,selection)
            st.session_state.ticket_next=saved['id']
            st.toast(f'Added {selection.subject} to My Slip')
            st.session_state.nav_next='My Slip'
            st.rerun()
        except (ValueError,OverflowError,TypeError) as exc:
            st.error(f'Could not add selection: {exc}')
        except Exception as exc:
            st.error(f'Unable to save the selection ({type(exc).__name__}). Try again without losing your existing ticket.')
