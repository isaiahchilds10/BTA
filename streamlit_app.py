"""BTA 2.0 | Belt To Ass — Google OIDC private member edition.
No Gmail SMTP, emailed magic links, or publicly open signup flow.
Private mode requires Google OAuth + Supabase with migration 003 installed.
No fabricated lines, official injuries, model probabilities, grades or settlements.
"""
from __future__ import annotations
import html
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any
from uuid import uuid4
import pandas as pd
import streamlit as st

from bta.config import setting, mode, auth_ready, admin_ready
from bta.domain import Selection, Game, SPORT_MARKETS, SPORTS, utcnow
from bta.sources.espn import scoreboard, roster, summary, SourceError
from bta.storage.local import LocalStore
from bta.research.engine import analyze, assess_ticket
from bta.ui.quickadd import parse_bulk
from bta.ui.style import apply
from bta.ui.browser import render_market_browser

st.set_page_config(page_title="BTA 2.0 | Belt To Ass", page_icon="🎟️", layout="wide", initial_sidebar_state="collapsed")
apply()

PAGES = ["Home", "NBA", "NFL", "College Football", "My Slip"]
GRADE_COLOR = {"TAIG":"#a779fa", "BTA+":"#36d49a", "BTA":"#48d5a3", "CONDITIONAL":"#f0cc70", "CUT":"#ff6278", "PENDING VERIFICATION":"#adb4c3"}


def escape(value: Any) -> str:
    return html.escape(str(value or ""))


def fmt_time(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZoneInfo("America/New_York")).strftime("%a %b %d · %I:%M %p %Z")
    except (ValueError, TypeError):
        return iso or "Time unavailable"


def title(heading: str, subtitle: str, kicker: str = "BTA / BELT TO ASS") -> None:
    st.markdown(f'<div class="bta-eyebrow">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.title(heading)
    st.markdown(f'<p class="bta-sub">{escape(subtitle)}</p>', unsafe_allow_html=True)


def mode_banner() -> None:
    if mode() == "demo":
        st.warning("DEMO / SINGLE USER — this local prototype has no account isolation and Streamlit Cloud storage can reset. Do not store private data or share this deployment as a member app.", icon="⚠️")
    else:
        st.caption("PRIVATE MODE · Google OIDC + server-scoped Supabase storage · Live integration verification still required")


def login() -> Any:
    """Google OIDC authentication plus Supabase owner-approved membership.

    No email delivery service is used. Streamlit handles Google's signed OIDC
    identity cookie. Supabase service-role calls are server-only and routed
    through explicit owner-scoped storage methods. Both identity and membership
    are required; Google authentication alone never grants app access.
    """
    if mode() == "demo":
        return LocalStore()
    if not admin_ready():
        st.error("Private BTA is locked until the owner configures Supabase URL and the server-only secret in Streamlit Secrets.")
        st.stop()
    from bta.security.google_identity import validate_google_claims
    from bta.security.google_membership import require_member
    from bta.storage.google_oidc import GoogleCloudStore
    from bta.security.membership import owner_bootstrap

    try:
        owner_bootstrap()
    except Exception:
        st.error("Owner provisioning is not ready. Apply all three SQL migrations and configure BTA_OWNER_EMAIL.")
        st.stop()

    try:
        logged_in = bool(st.user.is_logged_in)
    except Exception:
        st.error("Google OIDC is not configured. Add the [auth] settings in private Streamlit Secrets before launching BTA.")
        st.stop()
    if not logged_in:
        a,b=st.columns([1,1.7],gap="large")
        with a:
            st.image("assets/bta_belt_branding_logo.png",use_container_width=True)
        with b:
            title("Welcome to BTA", "Private sports intelligence for approved members.", "SECURE · INVITE ONLY")
            st.caption("No passwords. No sign-in emails. Continue with your Google account.")
            if st.button("Continue with Google", type="primary", use_container_width=True):
                st.login()
            st.caption("Only Google accounts pre-approved by the BTA owner can open private tickets.")
        st.stop()
    try:
        # st.user claims have already passed Streamlit's Google OIDC verification.
        claims = dict(st.user)
        identity = validate_google_claims(claims)
        member = require_member(identity)
        st.session_state.bta_email = identity.email
        return GoogleCloudStore(member)
    except PermissionError as exc:
        st.error(str(exc))
        st.caption("If you were invited, use the exact Google account email the BTA owner approved.")
        if st.button("Sign out / choose another Google account",use_container_width=True):
            st.logout()
        st.stop()
    except Exception:
        st.error("Private account verification is temporarily unavailable. No data has been opened.")
        st.caption("Check Supabase configuration, SQL migration 003 and the project status.")
        if st.button("Sign out",use_container_width=True):
            st.logout()
        st.stop()

store = login()


@st.cache_data(ttl=120, show_spinner=False)
def cached_games(sport: str, dt: date | None):
    return scoreboard(sport, dt)


def load_games(sport: str, dt: date | None = None, refresh: bool = False):
    try:
        if refresh:
            cached_games.clear()
            return scoreboard(sport, dt, refresh=True)
        return cached_games(sport, dt)
    except (SourceError, ValueError) as exc:
        return [], f"Feed unavailable: {exc}"


def sidebar() -> None:
    with st.sidebar:
        st.image("assets/bta_belt_branding_logo.png", use_container_width=True)
        st.markdown("**BELT TO ASS 2.0**")
        st.caption("NBA · NFL · COLLEGE FOOTBALL")
        st.divider()
        st.caption(f"Storage: {'Local prototype' if mode()=='demo' else 'Private Google OIDC / Supabase'}")
        if mode() == "private":
            st.caption(f"Signed in: {st.session_state.get('bta_email','Member')}")
            if st.button("Sign out", use_container_width=True):
                st.session_state.pop("bta_email",None)
                st.logout()
        with st.expander("Source and AI health"):
            st.caption("Games: ESPN public web endpoint — unofficial; availability varies")
            st.caption("Odds: optional published third-party PropLine/ParlayAPI quote adapter; independent rule/price recheck required")
            st.caption("Official injury: NBA league PDF adapter, only where exact player/game report matches")
            st.caption("AI: optional critical explanation, not grading authority")
            st.caption("Autonomous jobs: GitHub schedule (private mode only, if configured)")
        if mode() == "private" and store.role == "owner":
            owner_panel()


def owner_panel() -> None:
    with st.expander("Owner controls · Members / Health"):
        if not admin_ready():
            st.warning("Configure service credentials in Streamlit secrets to enable owner controls.")
            return
        from bta.security.membership import invite_member, set_member_enabled, renew_member_invitation
        from bta.storage.cloud import make_client
        st.markdown("**Approve a Google account**")
        st.caption("Enter the exact email on your friend’s Google account. Approval is recorded in Supabase; no email provider is needed. Share your BTA website URL manually.")
        email=st.text_input("Member email",key="owner_invite_email",placeholder="friend@example.com")
        if st.button("Approve Google account",key="owner_invite_action"):
            try:
                invite_member(store.uid,email)
                st.success("Member email approved for seven days. Share your BTA app URL directly with this person. No invitation email is sent.")
            except Exception as exc:
                st.error(f"Unable to approve member: {type(exc).__name__}. Check the address or account status.")
        admin=make_client(service=True)
        try:
            members=admin.table("members").select("id,email,role,enabled,activated_at,invite_expires_at").order("created_at",desc=True).limit(100).execute().data or []
            st.caption(f"{len(members)} members returned (up to 100). Access is restricted to invited accounts.")
            for person in members:
                if person['role']=='owner': continue
                cols=st.columns([3,1,1])
                cols[0].caption(f"{person['email']} · {'Activated' if person.get('activated_at') else 'Pending'}")
                cols[1].caption('Enabled' if person['enabled'] else 'Disabled')
                if cols[2].button("Disable" if person['enabled'] else "Renew",key='member_'+person['id']):
                    if person['enabled']:
                        set_member_enabled(store.uid,person['id'],False)
                    else:
                        renew_member_invitation(store.uid,person['id'])
                    st.rerun()
                if not person.get('activated_at') and person.get('enabled'):
                    if cols[2].button('Renew 7d',key='renew_'+person['id']):
                        renew_member_invitation(store.uid,person['id']); st.rerun()
        except Exception:
            st.caption("Member status unavailable. Database and setup should be checked.")
        try:
            jobs=admin.table("jobs").select("state").limit(500).execute().data or []
            counts={}
            for job in jobs:counts[job['state']]=counts.get(job['state'],0)+1
            st.caption(f"Research jobs: {counts}")
        except Exception: st.caption("Worker health is unverified")
        from bta.ai.providers import providers
        st.caption(f"Configured AI providers: {len(providers())}/3. Real quotas and available models depend on your account.")
        from bta.ai.providers import provider_health
        for name,health in provider_health().items():
            st.caption(f"{name}: {health['successes']} completed / {health['attempts']} attempts; "
                       f"cooldown {health['cooldown_seconds']}s. No account quota is inferred.")
        with st.popover("Backup encryption key setup"):
            st.caption("Optional: generate a fresh secret to paste into the private GitHub Actions repository secret BTA_BACKUP_KEY. The app cannot save it to GitHub for you.")
            if st.button("Generate a new encryption key",key="generate_fernet_key"):
                from cryptography.fernet import Fernet
                st.session_state.bta_new_backup_key=Fernet.generate_key().decode()
            if st.session_state.get("bta_new_backup_key"):
                st.code(st.session_state.bta_new_backup_key)
                st.caption("Copy now and store securely. Do not put the key in source code or send it in chat.")
        st.warning("A genuine isolated Supabase/Postgres restore and multiuser security test are still required before production launch.")


def nav() -> str:
    if st.session_state.get("nav_next"):
        st.session_state.nav = st.session_state.pop("nav_next")
    if "nav" not in st.session_state:
        st.session_state.nav = "Home"
    with st.container(key="bta_primary_nav"):
        return st.segmented_control("Navigation", PAGES, key="nav", selection_mode="single", label_visibility="collapsed") or "Home"


def render_game(g: Game, sport: str) -> None:
    """A concise scoreboard card. The full market browser opens only on demand."""
    state_name = "LIVE" if g.state == "in" else "FINAL" if g.state == "post" else "UPCOMING"
    color = "#ff5066" if g.state == "in" else "#a8b3c6" if g.state == "post" else "#55dbaa"
    with st.container(border=True):
        info, action = st.columns([4,1.25],vertical_alignment="center")
        with info:
            st.markdown(f'<span style="font-weight:850;font-size:1.05rem">{escape(g.away)}</span> '
                        f'<span style="color:#8793a9">at</span> '
                        f'<span style="font-weight:850;font-size:1.05rem">{escape(g.home)}</span>',unsafe_allow_html=True)
            st.markdown(f'<span style="color:{color};font-weight:850;font-size:.75rem;letter-spacing:.09em">{state_name}</span> '
                        f'<span style="color:#abb3c2;font-size:.82rem">· {escape(g.score) if g.score else escape(fmt_time(g.start_time))} · {escape(g.detail)}</span>',unsafe_allow_html=True)
            st.caption(f"Source observed {fmt_time(g.checked_at)} · game feed is not a sportsbook line or official injury report")
        with action:
            if st.button("Browse markets",key=f"open_{sport}_{g.id}",type="primary",use_container_width=True):
                st.session_state[f"open_game_{sport}"]=g.__dict__
                st.rerun()


def league_page(sport: str) -> None:
    headings={"NBA":("NBA", "Games, player props and research markets"),
              "NFL":("NFL", "Passing, receiving, rushing and touchdowns"),
              "CFB":("College Football", "FBS matchups, game lines and research")}
    heading,subtitle=headings[sport]
    opened=st.session_state.get(f"open_game_{sport}")
    if opened:
        if st.button("← All games",key=f"back_to_{sport}"):
            st.session_state.pop(f"open_game_{sport}",None)
            st.rerun()
        render_market_browser(Game(**opened),store=store,add_leg=persist_add,fmt_time=fmt_time)
        with st.expander("Matchup research / current observed statistics"):
            g=Game(**opened)
            if st.button("Compare completed team results",key=f"side_{g.id}"):
                from bta.research.matchup import side_by_side
                comparison=side_by_side(sport,g.away_id,g.home_id,g.start_time)
                for side in comparison['teams']:
                    st.markdown(f"**{side['side']}** · {side['games']} completed games · {side['wins']} wins")
                    if side['rows']:
                        st.dataframe(pd.DataFrame(side['rows']),hide_index=True,use_container_width=True)
                for warning in comparison['warnings']:st.warning(warning)
                st.caption(comparison['limits'])
            if g.state in {'in','post'} and st.button('Retrieve observed box score',key=f'box_{g.id}'):
                try:
                    from bta.research.live import fetch_live
                    # Matchup-level summary is observation, not a bookmaker-market feed.
                    live,url=fetch_live(Selection.new(sport=sport,game_id=g.id,game_label=f'{g.away} @ {g.home}',game_start=g.start_time,
                                subject=g.home,market='moneyline',direction='YES',threshold=None))
                    st.write(live.get('score'),live.get('detail'))
                    st.caption(f"Checked {fmt_time(live['checked_at'])} · third-party source")
                    freshness=live.get('freshness') or {}
                    st.caption('Upstream freshness: '+freshness.get('state','UNAVAILABLE')+' · '+freshness.get('reason',''))
                    st.link_button('See provider source',url)
                except (SourceError,ValueError) as exc:st.warning(f'Observed data unavailable: {exc}')
        return
    title(heading,subtitle,"MARKET BROWSER · NBA / NFL / CFB")
    filters=st.columns([1.6,1.6,1.2])
    with filters[0]:
        if sport=='NBA':
            selected_day=st.date_input('Game date',value=datetime.now(ZoneInfo('America/New_York')).date(),key='date_NBA')
        else:
            period=st.segmented_control('Schedule',['Active week','Choose date'],default='Active week',key=f'period_{sport}')
            selected_day=st.date_input('Game date',value=datetime.now(ZoneInfo('America/New_York')).date(),key=f'date_{sport}') if period=='Choose date' else None
    with filters[1]:
        search=st.text_input('Find a team',placeholder='Search matchups',key=f'filter_{sport}')
    with filters[2]:
        st.write(' ')
        refresh=st.button('↻ Refresh scores',key=f'refresh_{sport}',use_container_width=True)
    st.caption('Scoreboard checks recur approximately every two minutes while this page is open. Provider updates may be slower or unavailable.')
    league_scoreboard(sport,selected_day,search,refresh)


@st.fragment(run_every='120s')
def league_scoreboard(sport:str,selected_day:date|None,search:str,refresh:bool=False)->None:
    games,source=load_games(sport,selected_day,refresh)
    if source.startswith('Feed unavailable'):
        st.warning(source)
        st.caption('The game feed is unavailable. Existing slips remain saved; you can still use My Slip → Quick Add.')
        return
    if not games:
        st.info('No games returned for this period. Try another date or active week.')
        return
    shown=[g for g in games if not search or search.casefold() in (g.away+' '+g.home).casefold()]
    live=[g for g in shown if g.state=='in']
    upcoming=[g for g in shown if g.state=='pre']
    other=[g for g in shown if g.state not in ('in','pre')]
    for label,items in [('LIVE NOW',live),('UPCOMING',upcoming),('FINAL / OTHER',other)]:
        if items:
            st.markdown(f'### {label} <span class="bta-count">{len(items)}</span>',unsafe_allow_html=True)
            for g in items[:80]:render_game(g,sport)
            if len(items)>80:st.caption('Showing first 80 games; narrow the team filter for more.')
    st.caption('These are observed schedule/score records, not a live odds feed. Click Browse markets to select an exact proposition. Player positions are filtered from the actual available roster data.')



def home() -> None:
    st.markdown('<div class="bta-hero"><div class="bta-eyebrow">INDEPENDENT SPORTS INTELLIGENCE</div><strong>BTA 2.0 · BELT TO ASS</strong><p class="bta-sub">Research every angle. Challenge every leg. Protect the ticket.</p><span class="bta-chip red">EVIDENCE FIRST</span>&nbsp;<span class="bta-chip">NBA</span>&nbsp;<span class="bta-chip">NFL</span>&nbsp;<span class="bta-chip">COLLEGE FOOTBALL</span></div>',unsafe_allow_html=True)
    tickets = store.list_tickets()
    pending_count = 0
    certified_count = 0
    total = 0
    for ticket in tickets:
        total += len(ticket["legs"])
        saved_reports = store.list_reports(ticket["id"])
        pending_count += sum(1 for l in ticket["legs"] if l["id"] not in saved_reports)
        certified_count += sum(1 for l in ticket["legs"] if saved_reports.get(l["id"],{}).get("grade")=="TAIG")
    cols = st.columns(4)
    for col,value,label in zip(cols,[len(tickets),total,pending_count,certified_count],["Saved slips","Saved legs","Awaiting reports","Certified TAIG picks"]):
        with col: st.markdown(f'<div class="bta-kpi"><b>{value}</b><span>{label}</span></div>',unsafe_allow_html=True)
    st.divider()
    st.markdown("### Upcoming games & live scores")
    for sport in SPORTS:
        games, source = load_games(sport,datetime.now(ZoneInfo("America/New_York")).date() if sport == "NBA" else None)
        with st.expander(f"{sport}  ·  {len(games)} fixtures returned", expanded=False):
            if source.startswith("Feed unavailable"):
                st.caption(source)
            elif games:
                for g in games[:5]:
                    st.write(f"**{g.away} @ {g.home}** · {fmt_time(g.start_time)} · {g.detail}")
                if len(games) > 5: st.caption("Open the league page for more games")
            else:
                st.caption("No current fixtures from this feed")
    st.markdown("### BTA Finds · Evidence-ranked")
    qualified=[]
    for ticket in tickets:
        reports=store.list_reports(ticket['id'])
        for leg in ticket['legs']:
            report=reports.get(leg['id'],{})
            if report.get('grade') in {'TAIG','BTA+','BTA'}:
                qualified.append((report['grade'],leg,report))
    qualified.sort(key=lambda x: {'TAIG':0,'BTA+':1,'BTA':2}.get(x[0],9))
    if qualified:
        st.caption('Only previously researched qualifying selections from your private saved slips are shown here. They are not a guarantee of availability or value.')
        for grade,leg,report in qualified[:8]:
            st.write(f"**{grade} · {leg['subject']}** · {leg['market'].replace('_',' ')} · {report.get('grade_reason','')}")
    else:
        st.info('No independently certified BTA Finds yet. BTA never fills the board with fake picks.')
    candidates=[]
    for ticket in tickets:
        reports=store.list_reports(ticket['id'])
        for leg in ticket['legs']:
            report=reports.get(leg['id'],{})
            if report.get('grade') in {'TAIG','BTA+','BTA'}:continue
            preliminary=report.get('preliminary_screen') or {}
            if preliminary.get('status') in ('STRONG_RESEARCH_CANDIDATE','WORTH_INVESTIGATING'):
                candidates.append((preliminary['status'],leg,report))
    if candidates:
        st.markdown('#### Research candidates · NOT certified')
        st.caption('These have useful observed statistics but have not cleared every required verification gate. They are not strict-ticket selections.')
        for label,leg,report in candidates[:8]:
            st.write(f"**{leg['subject']}** · {leg['market'].replace('_',' ')} · {label.replace('_',' ').title()}")
    st.markdown("### Your research")
    st.write("Automated research queues are persisted in private mode when Supabase is configured. Scheduled processing runs only when the GitHub Actions worker is installed with credentials and observed running.")
    if tickets:
        recent = tickets[0]
        st.caption(f"Latest ticket: {recent['name']} · {len(recent['legs'])} legs · {recent['state']}")


def get_ticket() -> dict | None:
    if st.session_state.get("ticket_next"):
        st.session_state.ticket_id = st.session_state.pop("ticket_next")
    tickets = store.list_tickets()
    if not tickets:
        return None
    known_ids = [t["id"] for t in tickets]
    if st.session_state.get("ticket_id") not in known_ids:
        st.session_state.ticket_id = known_ids[0]
    names = {t["id"]:f"{t['name']} · {len(t['legs'])}/30 · {t['state']}" for t in tickets}
    ticket_id = st.selectbox("Selected slip", known_ids, format_func=lambda k:names[k], key="ticket_id")
    return next(t for t in tickets if t["id"] == ticket_id)


def persist_add(ticket: dict, selection: Selection) -> dict:
    selection.validate()
    if len(ticket["legs"]) >= 30:
        raise ValueError("This ticket already has 30 legs")
    new = dict(ticket)
    new["legs"] = [*ticket["legs"], selection.asdict()]
    saved = store.save_ticket(new)
    store.add_job(saved["id"], selection.id)
    if mode() == "demo":
        # Owner-run prototype only; cloud worker must persist trusted reports in private mode.
        result = analyze(selection)
        store.add_report(saved["id"], selection.id, result)
        for j in store.list_jobs(saved["id"]):
            if j["selection_id"] == selection.id and j["state"] == "queued":
                store.update_job(j["id"], "pending_evidence" if result["grade"]=="PENDING VERIFICATION" else "complete")
    return saved


def new_ticket_panel() -> None:
    c1,c2 = st.columns([3,1])
    with c1:
        new_name = st.text_input("New slip name", value="BTA Research Slip", max_chars=100, key="new_ticket_name")
    with c2:
        st.write(" ")
        if st.button("+ Create slip", type="primary",use_container_width=True):
            try:
                t = store.create_ticket(new_name or "BTA Research Slip")
                st.session_state.ticket_id = t["id"]
                st.rerun()
            except Exception as exc: st.error(f"Could not create slip: {exc}")


def add_selection_ui(ticket: dict) -> None:
    st.markdown("### Add a selection")
    pending = st.session_state.get("pending_game") or {}
    initial_sport = pending.get("sport", "NBA")
    sport = st.selectbox("League", SPORTS, index=SPORTS.index(initial_sport),key="leg_sport")
    match = pending if pending.get("sport") == sport else {}
    if match:
        st.caption(f"Selected match: {match['away']} @ {match['home']} · {fmt_time(match['start_time'])}")
    else:
        st.caption("No game selected. Manual entry is allowed, but matchup and market remain unverified.")
    athlete_options = st.session_state.get("roster_for_"+str(match.get("id")), [])
    if match and st.button("Load available player roster (best effort)"):
        loaded = []
        try:
            for tid, side in ((match.get("away_id", ""),"away"),(match.get("home_id",""),"home")):
                if tid:
                    players, _ = roster(sport,str(tid))
                    loaded += [{**p, "side":side} for p in players]
            st.session_state["roster_for_"+str(match.get("id"))] = loaded
            athlete_options = loaded
            if not loaded: st.info("No roster returned. Manual athlete ID remains optional.")
        except SourceError as exc:
            st.warning(f"Roster feed unavailable: {exc}")
    athlete_choice = None
    if athlete_options:
        athlete_choice = st.selectbox("Optional roster player",[None]+list(range(len(athlete_options))),format_func=lambda x:"Choose a player" if x is None else athlete_options[x]["name"])
    with st.form("add_leg", clear_on_submit=False):
        subject_default = athlete_options[athlete_choice]["name"] if athlete_choice is not None else ""
        subject = st.text_input("Player or team (exact name)",value=subject_default,max_chars=100)
        market = st.selectbox("Exact market family",SPORT_MARKETS[sport],format_func=lambda s:s.replace("_"," ").title())
        c1,c2,c3 = st.columns(3)
        with c1:
            dirs = ["YES", "NO"] if market in {"moneyline", "anytime_td"} else ["OVER","UNDER","YES","NO"]
            direction = st.selectbox("Direction",dirs)
        with c2:
            threshold = None if market == "moneyline" else st.number_input("Threshold", min_value=-10000.0 if market=="spread" else 0.0, max_value=10000.0, step=0.5, value=-3.5 if market=="spread" else 20.5, format="%.1f")
        with c3:
            inclusive_choice = st.checkbox("Inclusive threshold (e.g. 20+)",value=False,disabled=market=="moneyline")
        c4,c5 = st.columns(2)
        with c4: platform = st.selectbox("Market source",["User-entered","FanDuel","DraftKings","Polymarket","Other"])
        with c5: odds = st.text_input("Optional American odds (e.g. -110)", placeholder="No verified price")
        c6,c7 = st.columns(2)
        with c6: athlete_id = st.text_input("ESPN player ID (optional)",value=athlete_options[athlete_choice]["id"] if athlete_choice is not None else "")
        with c7: manual_game_id = st.text_input("ESPN game ID (optional)", value=str(match.get("id", "")))
        notes = st.text_input("Private note (optional)", max_chars=1000)
        submit = st.form_submit_button("Add to My Slip",type="primary")
    if submit:
        try:
            odds_val = int(odds.strip()) if odds.strip() else None
            if athlete_choice is not None and subject.strip() != athlete_options[athlete_choice]["name"]:
                raise ValueError("The selected ESPN athlete ID does not match the entered player name")
            game_label = f"{match.get('away','')} @ {match.get('home','')}" if match else "Matchup not verified"
            team_role = athlete_options[athlete_choice]["side"] if athlete_choice is not None else ""
            leg = Selection.new(sport=sport,game_id=manual_game_id.strip(),game_label=game_label,
                game_start=match.get("start_time", ""), subject=subject,market=market,direction=direction,
                threshold=threshold,inclusive=True if direction in {"YES","NO"} else inclusive_choice,platform=platform,american_odds=odds_val,
                athlete_id=athlete_id.strip(),team_role=team_role,team_id="",market_verified=False,
                settlement_verified=False,notes=notes,game_status=match.get("state", ""))
            persist_add(ticket,leg)
            st.session_state.pop("pending_game", None)
            st.success("Selection saved unchanged. Research queued; only supported verifiable facts will be analyzed.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not add selection: {exc}")

    with st.expander("Quick Add · paste multiple exact-threshold player props"):
        st.caption("Example: John Smith 20+ receiving yards; Jane Smith over 15.5 points. Every parsed field must be reviewed; no market offer is inferred.")
        bulk_sport = st.selectbox("Quick Add league", SPORTS, key="bulk_sport")
        lines = st.text_area("One proposition per line",height=130,key="bulk_lines")
        if st.button("Parse & preview",key="parsebulk"):
            parsed,errors = parse_bulk(lines,bulk_sport)
            st.session_state.bulk_preview = {"sport":bulk_sport,"parsed":parsed,"errors":errors,"game":match if match.get("sport")==bulk_sport else {}}
        preview = st.session_state.get("bulk_preview")
        if preview:
            for err in preview["errors"]: st.warning(err)
            if preview["parsed"]:
                st.dataframe(pd.DataFrame(preview["parsed"])[["subject","market","direction","threshold","inclusive"]],hide_index=True,use_container_width=True)
                st.caption("All markets USER ENTERED / NOT VERIFIED. Unclear team assignment or participation blocks high grades.")
                if st.button(f"Confirm add {len(preview['parsed'])} selections",key="commitbulk"):
                    if len(preview["parsed"])+len(ticket["legs"]) > 30:
                        st.error("This would exceed the 30-leg maximum")
                    else:
                        try:
                            current = ticket
                            for item in preview["parsed"]:
                                g = preview["game"]
                                leg = Selection.new(sport=preview["sport"], game_id=str(g.get("id", "")),
                                    game_label=f"{g.get('away')} @ {g.get('home')}" if g else "Matchup not verified",
                                    game_start=g.get("start_time", ""), subject=item["subject"],market=item["market"],
                                    direction=item["direction"],threshold=item["threshold"],inclusive=item["inclusive"],
                                    notes=item["notes"],game_status=g.get("state",""))
                                current = persist_add(current,leg)
                            st.session_state.pop("bulk_preview",None)
                            st.success("Confirmed selections saved")
                            st.rerun()
                        except Exception as exc: st.error(f"Could not complete import: {exc}")


def selection_title(leg: Selection) -> str:
    if leg.market == "moneyline":
        return f"{leg.subject} · {leg.direction} MONEYLINE"
    if leg.market == "spread" and leg.threshold is not None:
        return f"{leg.subject} · {leg.threshold:+g} SPREAD · {leg.direction} / cover"
    direction = f"{leg.direction} {leg.threshold:g}" if leg.threshold is not None else leg.direction
    if leg.inclusive and leg.threshold is not None:
        direction += " (inclusive)"
    return f"{leg.subject} · {direction} {leg.market.replace('_',' ')}"


def report_details(leg: Selection, report: dict) -> None:
    st.caption(f"Checked {fmt_time(report.get('checked_at',''))} · Evidence {report.get('evidence_quality','INCOMPLETE')} · {report.get('market_status','NOT VERIFIED')}")
    st.markdown(f"**Grade:** :{ 'gray' if report.get('grade')=='PENDING VERIFICATION' else 'green'}[{escape(report.get('grade'))}] · {escape(report.get('grade_reason'))}")
    st.write(report.get("summary",""))
    preview=report.get('preliminary_screen') or {}
    if preview:
        st.info(f"Preliminary research: **{preview.get('status','NOT ASSESSED').replace('_',' ')}** · {preview.get('message','')} — this is NOT a certified BTA grade.")
    gates=report.get('verification_gates') or {}
    if gates:
        with st.expander('Evidence verification · certification gates',expanded=False):
            st.dataframe(pd.DataFrame([{'Check':name.replace('_',' ').title(),
                'Verified':'YES' if item.get('passed') else 'NO',
                'Details':item.get('reason') or 'Server evidence supports this gate'}
                for name,item in gates.items()]),hide_index=True,use_container_width=True)
            injury=report.get('official_availability') or {}
            if injury:st.caption('Official injury-report observation: '+injury.get('state','UNKNOWN')+(' · '+injury.get('status','') if injury.get('status') else ''))
            if injury.get('source_url'):st.link_button('Read NBA official injury PDF',injury['source_url'])
            opp=report.get('opponent_evidence') or {}
            if opp:st.caption('Position-adjusted opponent sample: '+opp.get('state','UNKNOWN')+' · '+opp.get('reason',''))
            terms=report.get('settlement_evidence') or {}
            if terms.get('source_url'):st.link_button('Operator terms for selected jurisdiction',terms['source_url'])

    football=report.get('football_evidence') or {}
    if football.get('sport')=='NFL':
        official=football.get('official_injury') or {}
        secondary=football.get('injury') or {}
        with st.expander('NFL injury sources and status',expanded=False):
            st.write(f"**League page:** {official.get('state','UNAVAILABLE').replace('_',' ')}"
                     + (f" · {official['status']}" if official.get('status') else ''))
            st.caption(official.get('reason','League injury status unverified'))
            if official.get('source_url'):st.link_button('Open official NFL injury page',official['source_url'])
            st.write(f"**nflverse report transcription:** {secondary.get('state','UNAVAILABLE').replace('_',' ')}"
                     + (f" · {secondary['status']}" if secondary.get('status') else ''))
            st.caption(secondary.get('reason','Secondary source unavailable'))
            if secondary.get('source_url'):st.link_button('Open nflverse injury dataset',secondary['source_url'])
            editorial=football.get('editorial_injury') or {}
            st.write(f"**NFL weekly editorial fallback:** {editorial.get('state','UNAVAILABLE').replace('_',' ')}"
                     + (f" · {editorial['status']}" if editorial.get('status') else ''))
            st.caption(editorial.get('reason','No verified weekly editorial report'))
            if editorial.get('source_url'):st.link_button('Open NFL-published weekly summary',editorial['source_url'])
            reconciled=football.get('participation_reconciliation') or {}
            st.caption('Participation evidence: '+reconciled.get('state','UNVERIFIED')+' · '+reconciled.get('reason','Not established'))
            st.caption('Neither a practice report nor absence from the report establishes unrestricted playing time.')
    if football.get('sport')=='CFB':
        cf=football.get('matchup') or {}
        with st.expander('College football FBS team research',expanded=False):
            st.caption(cf.get('state','UNAVAILABLE')+' · '+cf.get('reason','No comparable FBS observations'))
            if cf.get('fixture_verified'):st.caption(f"CFBD fixture ID: {cf.get('cfbd_game_id')}")
            st.caption('FBS classification: '+('confirmed from event record' if cf.get('fbs_verified') else 'not independently established'))
            for name,team in (cf.get('teams') or {}).items():
                st.write(f"**{name}** · {team.get('sample',0)} completed pregame contests")
                for metric in ('points_for','points_against','yards_per_play','rushing_yards','passing_yards','turnovers','opponent_other_games_win_rate'):
                    if team.get(metric) is not None:st.caption(f"{metric.replace('_',' ').title()}: {team[metric]}")
            st.caption('Historical aggregates are not a verified starting-QB, injuries, opponent-adjusted, or trench evaluation.')
            availability_sources=football.get('official_availability_hubs') or {}
            for conf,hub in availability_sources.items():
                if hub.get('state')=='OFFICIAL_HUB_IDENTIFIED':
                    st.caption(f'{conf} official availability reporting hub · specific player status still needs a dated report')
                    if hub.get('source_url'):st.link_button(f'Open {conf} official reporting hub',hub['source_url'])
            adversities=football.get('historical_adversity') or {}
            if adversities.get('state')=='OBSERVED_SAMPLES':
                st.caption('Historical play-by-play situations:')
                for side,team_sample in (adversities.get('teams') or {}).items():
                    a=team_sample.get('adversity') or {}
                    st.caption(f'{side.title()}: {a.get("state","UNAVAILABLE")} · {a.get("games",0)} linked pregame games observed')
    weekly=report.get('nfl_weekly_evidence') or {}
    if weekly.get('state')=='HISTORICAL_WEEKLY_RESEARCH':
        st.caption('NFL player history: nflverse weekly source · a secondary postgame-updated dataset, not a timestamped historical offer.')
        if weekly.get('source_url'):st.link_button('View nflverse weekly source',weekly['source_url'])
    fav=report.get('favorite_evidence') or {}
    if fav.get('state')=='OBSERVED_MARKET_FAVORITE':
        st.caption('Observed pregame market favorite: '+fav.get('favorite_team','')+' · no independent win probability inferred.')

    hist = report.get("history", {})
    if hist.get("available"):
        c1,c2,c3 = st.columns(3)
        c1.metric("Observed clears", f"{hist['hits']}/{hist['sample']}")
        c2.metric("Recent median", f"{hist['median']:g}")
        c3.metric("Median cushion", f"{hist['median_clearance']:+g}")
        st.caption("Observed historical fraction and Wilson uncertainty are DESCRIPTIVE, not a calibrated future hit probability.")
        if hist.get("three_for_three") is not None:
            st.caption(f"First three recent games shown: {hist['three_for_three']}/3 clear exact threshold")
        st.dataframe(pd.DataFrame(hist["rows"])[["date","opponent","value","result","clearance_margin"]],hide_index=True,use_container_width=True)
    else:
        st.info(hist.get("reason","No historical numeric sample for this market"))
    context=report.get('source_context') or {}
    if context.get('status')=='THIRD_PARTY_CONTEXT_AVAILABLE':
        with st.popover("Matchup sources and team context"):
            st.caption("ESPN public data is a third-party snapshot, not a verified official injury or bookmaker feed.")
            for t in (context.get('team_comparison') or {}).get('teams',[]):
                st.write(f"**{t.get('side')}** · {t.get('wins')}/{t.get('games')} recent listed games won · average margin {t.get('avg_margin')}")
            if (context.get('team_comparison') or {}).get('warnings'):
                st.write((context.get('team_comparison') or {}).get('warnings'))
            for source in context.get('sources',[]):
                st.caption(f"{source.get('provider')} · checked {fmt_time(source.get('retrieved_at',''))}")
            for w in context.get('warnings',[]):st.caption(w)
    st.markdown("**Five-script stress matrix**")
    st.dataframe(pd.DataFrame([{"Scenario":s["scenario"],"Verdict":s["verdict"],"Reason":s["mechanism"]} for s in report.get("scripts",[])]),hide_index=True,use_container_width=True)
    ai=report.get("ai") or {}
    if ai:
        with st.popover("AI specialist and independent critic"):
            for label,key in (("Evidence research","researcher"),("Adversarial second perspective","critic")):
                data=ai.get(key) or {}
                st.markdown(f"**{label} · {data.get('status','UNAVAILABLE')}**")
                st.write(data.get('text',"AI assessment not available"))
                st.caption(f"Model: {data.get('provider') or 'none'} · Not a verified source or authoritative grade")
    st.markdown("**Independent failure-path audit**")
    for risk in report.get("failure_paths",[]): st.write("•",risk)
    st.markdown("**What prevents certification**")
    for issue in report.get("blockers",[]): st.write("•",issue)
    if report.get("data_issue"): st.caption(report["data_issue"])
    if report.get("source_url"):
        st.link_button("View source endpoint",report["source_url"])
    audit=report.get('independent_audit','PENDING')
    audit_label=audit.get('status','PENDING') if isinstance(audit,dict) else str(audit)
    st.caption(f"Independent second pass: {audit_label}; model true probability: not validated; break-even quoted odds: {f'{report['price_break_even']:.1%}' if report.get('price_break_even') is not None else 'unavailable'}. This break-even number is not a forecast.")
    with st.popover("Ask BTA about this leg"):
        prompt = st.text_input("Question about this evidence",value="What is the strongest plausible ordinary failure path?",key=f"aiq_{leg.id}")
        if st.button("Ask AI critic",key=f"ask_{leg.id}"):
            from bta.ai.providers import explain_report, AIUnavailable
            try:
                with st.spinner("Checking optional model availability"):
                    response,provider = explain_report(report,prompt)
                st.write(response)
                st.caption(provider + " · Opinion cannot upgrade grades or verify injuries/markets")
            except AIUnavailable as exc:
                st.info(str(exc))


@st.fragment(run_every='45s')
def ticket_work_status(ticket_id:str)->None:
    """Read real durable worker state, no synthetic percentages or fake progress bars."""
    try:
        jobs=store.list_jobs(ticket_id)
        counts={}
        for job in jobs:counts[job['state']]=counts.get(job['state'],0)+1
        if counts:
            st.caption('Research worker status · '+', '.join(f'{key.replace("_"," ")}: {value}' for key,value in sorted(counts.items())))
        else:
            st.caption('No research jobs recorded for this ticket')
        if st.button('↻ Refresh completed analyses',key=f'refresh_analysis_{ticket_id}',use_container_width=True):
            st.rerun()
    except Exception:
        st.warning('Research job status unavailable. Previously saved results remain intact.')


def ticket_ui(ticket: dict) -> None:
    reports = store.list_reports(ticket["id"])
    st.markdown("### Current ticket")
    col1,col2,col3 = st.columns([2,1,1])
    with col1:
        new_name = st.text_input("Ticket title",value=ticket["name"],key="rename_ticket")
    with col2:
        state = st.selectbox("Status", ["DRAFT","ACTIVE","ARCHIVED"],index=["DRAFT","ACTIVE","ARCHIVED"].index(ticket["state"]))
    with col3:
        st.write(" ")
        if st.button("Save ticket details",key="save_ticket_details"):
            store.save_ticket(dict(ticket,name=new_name or ticket["name"],state=state))
            st.rerun()
    st.caption(f"{len(ticket['legs'])}/30 legs · {ticket['version']} saved versions · Updated {fmt_time(ticket.get('updated_at',''))}")
    if not ticket["legs"]:
        st.info("Your ticket has no selections. Add a player prop, team line, or verified game selection below.")
    else:
        for number, raw in enumerate(ticket["legs"],1):
            leg = Selection(**raw)
            report = reports.get(leg.id)
            badge = report["grade"] if report else "QUEUED / NO REPORT"
            label = f"{number}. {selection_title(leg)}   |   {badge}"
            with st.expander(label):
                st.caption(f"{leg.sport} · {leg.game_label} · {fmt_time(leg.game_start)} · {leg.platform} · "
                        + (f"Vendor quote observed {fmt_time(leg.market_observed_at)}; current availability and settlement not reverified" if leg.market_observed_at else "Exact line user-entered; bookmaker offer not verified"))
                if report:
                    report_details(leg,report)
                else:
                    st.info("Research is queued or pending the scheduled worker. No grade assigned.")
                if leg.game_id.isdigit():
                    with st.popover("BTA Live · observed statistics"):
                        if st.button("Refresh observed game/player progress",key=f"live_{leg.id}"):
                            from bta.research.live import fetch_live
                            try:
                                live,url = fetch_live(leg)
                                st.write(f"**{live['score']}** · {live['detail']} · {live['state']}")
                                st.write(live['progress'])
                                st.caption(f"Fetched {fmt_time(live['checked_at'])} · {live['provider']} · Settlement {live['settlement']}")
                                fresh=live.get('freshness') or {}
                                st.caption('Score-feed freshness: '+fresh.get('state','UNAVAILABLE')+' · '+fresh.get('reason',''))
                                player_fresh=live.get('player_stat_freshness') or {}
                                st.caption('Player-stat freshness: '+player_fresh.get('state','UNAVAILABLE')+' · '+player_fresh.get('reason',''))
                                if live.get('official_scoreboard'):
                                    league=live['official_scoreboard']
                                    st.caption('NBA league-score crosscheck: '+league.get('state','UNAVAILABLE')+' · '+league.get('reason',''))
                                st.link_button("Open underlying summary",url)
                            except (SourceError,ValueError) as exc:
                                st.warning(f"Live evidence unavailable: {exc}")
                left,right,third = st.columns([1,1,1])
                with left:
                    if st.button("Recheck",key=f"rerun_{leg.id}",use_container_width=True):
                        store.add_job(ticket["id"],leg.id)
                        if mode()=="demo":
                            store.add_report(ticket["id"],leg.id,analyze(leg))
                        st.success("Recheck requested; prior reports preserved")
                        st.rerun()
                with right:
                    with st.popover("Adjust threshold"):
                        if leg.market == "moneyline":
                            st.caption("Moneyline YES/NO is not a numeric threshold. Add a new exact selection.")
                        else:
                            t = st.number_input("New exact target",value=float(leg.threshold or 0),min_value=0.0,max_value=10000.0,step=0.5,key=f"adj_{leg.id}")
                            if st.button("Approve new line",key=f"saveadj_{leg.id}"):
                                new = Selection.new(**{k:v for k,v in leg.asdict().items() if k not in {"id","created_at","market_verified","settlement_verified"}},)
                                new.threshold=t
                                new.market_verified=False
                                new.settlement_verified=False
                                replacement = dict(ticket)
                                replacement["legs"] = [new.asdict() if x["id"]==leg.id else x for x in ticket["legs"]]
                                saved = store.save_ticket(replacement)
                                store.add_job(saved["id"],new.id)
                                if mode()=="demo": store.add_report(saved["id"],new.id,analyze(new))
                                st.success("Exact revised threshold saved as new selection ID; original version retained")
                                st.rerun()
                with third:
                    with st.popover("Cut leg"):
                        st.write("Remove only after your approval. Version history keeps a snapshot.")
                        if st.button("Confirm cut",key=f"cut_{leg.id}",type="primary"):
                            new = dict(ticket)
                            new["legs"] = [x for x in ticket["legs"] if x["id"] != leg.id]
                            store.save_ticket(new)
                            st.rerun()
    st.divider()
    st.markdown("### Ticket assessment")
    st.caption("One action runs each exact leg through available verified statistics, sport-specific stress gates, optional AI specialist + independent critic, then checks the combined ticket. This may take time with large slips or busy free AI services.")
    if st.button("🚀 SUBMIT TICKET · FULL BTA ASSESSMENT",type="primary",use_container_width=True,disabled=not bool(ticket['legs'])):
        if mode()=='private':
            from bta.research.workflow import enqueue_full_ticket
            result=enqueue_full_ticket(store,ticket)
            st.session_state[f"assess_{ticket['id']}"]=True
            st.session_state[f"last_audit_{ticket['id']}"]=result['parlay']
            if result['failed_to_queue']:
                st.warning(f"{result['failed_to_queue']} selections could not be queued. Existing legs and reports remain saved.")
            st.info(f"Submission accepted: {result['new_queued']} newly queued; {result['already_queued']} already awaiting research. Results will appear as the background worker processes available sources and AI, subject to free service availability.")
            st.caption('Ticket submissions queue immediately. Full AI and verified evidence evaluation are not instant. GitHub scheduled-job delays and external quotas may apply.')
        else:
            from bta.research.workflow import submit_full_ticket
            with st.status("Local prototype evaluating available evidence",expanded=True) as statusbox:
                def progress(index,total,leg):
                    st.write(f"Analyzing {index}/{total}: {leg.subject} · {leg.market.replace('_',' ')}")
                result=submit_full_ticket(store,ticket,progress=progress,with_ai=True)
                statusbox.update(label="Local research pass finished; pending evidence noted.",state="complete")
            st.session_state[f"assess_{ticket['id']}"]=True
            st.session_state[f"last_audit_{ticket['id']}"]=result['parlay']
            st.rerun()
    if mode()=='private':
        ticket_work_status(ticket['id'])
    if st.button("Assess saved results without rerunning AI",key="ticket_audit_saved",use_container_width=True):
        st.session_state[f"assess_{ticket['id']}"]=True
    if st.session_state.get(f"assess_{ticket['id']}"):
        reports=store.list_reports(ticket['id'])
        audit=assess_ticket([Selection(**a) for a in ticket['legs']],reports)
        st.markdown("#### Complete parlay audit")
        cols=st.columns(4)
        cols[0].metric("Legs",audit['total'])
        cols[1].metric("Qualified",audit['qualified'])
        cols[2].metric("Pending",audit['incomplete'])
        cols[3].metric("Shared exposures",len(audit['overlaps']))
        st.warning(audit['risk_summary'])
        if audit['overlaps']:
            st.markdown("**Correlated / nested exposure**")
            for risk in audit['overlaps']:
                st.write(f"**{risk['a_name']} + {risk['b_name']}** — {'; '.join(risk['reasons'])}")
        else:st.caption("No obvious same-game or nested alternate-line overlap detected. This does not prove independence.")
        st.caption(f"Illustrative strict ticket excluding incomplete legs: {audit['what_if_remove_incomplete']['illustrative_remaining']} legs remain. Your original ticket was not changed.")
        st.markdown("**Individual verdicts**")
        for raw in ticket['legs']:
            leg=Selection(**raw)
            report=reports.get(leg.id,{})
            grade=report.get('grade','PENDING VERIFICATION')
            recommendation=report.get('recommendation','PENDING')
            st.write(f"{leg.subject} · {leg.market.replace('_',' ')} — **{grade}** · {recommendation}")
    with st.expander("Immutable slip version history and export"):
        versions = store.list_versions(ticket["id"])
        for row in versions[:30]: st.write(f"Version {row['version']} · {fmt_time(row['created_at'])} · {len(row['snapshot']['legs'])} legs")
        import json
        st.download_button("Export my ticket JSON",json.dumps({"ticket":ticket,"reports":reports},indent=2),file_name="bta_ticket_export.json",mime="application/json")
    if mode() == "private":
        with st.expander("Read-only sharing"):
            from bta.storage.cloud import lookup_member_for_sharing
            st.caption("Share a frozen snapshot with another pre-approved BTA member. Private notes are excluded.")
            if not admin_ready():
                st.caption("Private sharing is not configured")
            else:
                recipient = st.text_input("Recipient member email",key="share_recipient")
                if st.button("Share frozen snapshot"):
                    try:
                        people = lookup_member_for_sharing(store.uid,recipient.strip())
                        if len(people)!=1 or not people[0]["enabled"]:
                            raise ValueError("Recipient is not an active member")
                        store.share_ticket(ticket,people[0]["id"])
                        st.success("Frozen snapshot shared. Recipient must be signed in.")
                    except Exception as exc: st.error(f"Share unavailable: {exc}")
            for share in store.list_shares():
                if share["owner_id"] == store.uid:
                    st.write(f"Snapshot {share['id'][:8]} · {'Revoked' if share['revoked'] else 'Shared'}")
                    if not share["revoked"] and st.button("Revoke",key="revoke_"+share["id"]):
                        store.revoke_share(share["id"]);st.rerun()
                elif share["recipient_id"] == store.uid:
                    st.write(f"Received frozen slip: {share['frozen_snapshot'].get('name','Shared slip')}")
                    if st.button("Copy into my private slips",key="copy_"+share["id"]):
                        try:
                            copied = store.create_ticket("Copy · " + share["frozen_snapshot"].get("name","Shared")[:60])
                            # Fresh identities, no stale certifications; user approved copy.
                            new_legs=[]
                            for raw in share["frozen_snapshot"].get("legs",[])[:30]:
                                raw = {**raw, "id":str(uuid4()),"market_verified":False,"settlement_verified":False,"created_at":utcnow()}
                                new_legs.append(Selection(**raw).asdict())
                            copied = store.save_ticket(dict(copied,legs=new_legs))
                            for leg in new_legs: store.add_job(copied["id"],leg["id"])
                            st.session_state.ticket_next=copied["id"]
                            st.rerun()
                        except Exception as exc: st.error(f"Copy unavailable: {exc}")


def my_slip() -> None:
    title("My Slip","Your exact markets, independent leg research, and whole-ticket risk in one place.","BETTER TICKETS / FEWER BAD LEGS")
    new_ticket_panel()
    ticket = get_ticket()
    if not ticket:
        st.info("Create your first slip above to begin.")
        return
    ticket_ui(ticket)
    st.divider()
    add_selection_ui(ticket)

sidebar()
with st.container(key="bta_brand_bar"):
    logo,heading,slip_action=st.columns([0.6,3.2,1.2],vertical_alignment="center")
    with logo:
        st.image("assets/bta_belt_branding_logo.png",width=74)
    with heading:
        st.markdown('<div class="bta-brand-name">BTA <span>2.0</span></div><div class="bta-brand-tag">BELT TO ASS · SPORTS RESEARCH</div>',unsafe_allow_html=True)
    with slip_action:
        try:
            known_tickets=store.list_tickets()
            active_id=st.session_state.get('ticket_id')
            active=next((t for t in known_tickets if t['id']==active_id),known_tickets[0] if known_tickets else None)
            count=len(active['legs']) if active else 0
        except Exception:
            count=0
        if st.button(f"🎟️ My Slip · {count}/30",key="header_go_slip",use_container_width=True):
            st.session_state.nav_next="My Slip"
            st.rerun()
mode_banner()
page = nav()
if page == "Home":
    home()
elif page == "NBA":
    league_page("NBA")
elif page == "NFL":
    league_page("NFL")
elif page == "College Football":
    league_page("CFB")
else:
    my_slip()


def floating_chat() -> None:
    """Persistent across the five pages; accessible bubble rather than sixth navigation page."""
    with st.container(key="bta_float_button"):
        with st.popover("💬 Ask BTA",use_container_width=False):
            st.markdown("#### Ask BTA")
            st.caption("Ask about verified research, your current ticket, matchup risks, or why a leg is pending. AI does not change grades.")
            tickets=store.list_tickets()
            selected=tickets[0] if tickets else None
            reports=store.list_reports(selected['id']) if selected else {}
            if reports:
                keys=list(reports)
                selected_id=st.selectbox("Research report",keys,format_func=lambda i:next((l['subject']+' · '+l['market'] for l in selected['legs'] if l['id']==i),i),key="chat_report")
                report=reports[selected_id]
            else:
                report={"status":"NO RESEARCH YET","grade":"PENDING VERIFICATION","blockers":["Submit a ticket first to get evidence-backed answers"]}
            if "bta_chat_history" not in st.session_state:st.session_state.bta_chat_history=[]
            for item in st.session_state.bta_chat_history[-6:]:
                with st.chat_message(item['role']):st.write(item['text'])
            with st.form("float_chat_input",clear_on_submit=True):
                question=st.text_input("Question",placeholder="What could make my pick lose?",max_chars=1000)
                send=st.form_submit_button("Ask AI",type="primary")
            if send and question.strip():
                from bta.ai.providers import explain_report,AIUnavailable
                st.session_state.bta_chat_history.append({'role':'user','text':question.strip()})
                try:
                    reply,provider=explain_report(report,question.strip())
                    reply += f"\n\n*{provider}*"
                except AIUnavailable as exc:
                    reply=str(exc)
                st.session_state.bta_chat_history.append({'role':'assistant','text':reply})
                st.rerun()

floating_chat()
