# BTA market browser contract

**UX**: Home / NBA / NFL / College Football / My Slip only. On a league page, choose an observed fixture, then the market family, a supported player or game line, the precise threshold and direction, and add to a saved 30-leg slip. Research launches on ticket Submit. There is no wagering action.

**Market families**: NBA points, threes, rebounds, assists, PRA and other combos, steals/blocks/defense, game lines. NFL passing (QB), receiving (WR/TE/RB/FB), rushing (RB/FB/QB), touchdowns, game lines. College football FBS-first game lines and limited role-filtered props.

**Player filters**: An explicit roster position is required; unknown position = not shown. NFL receivers do not appear as routine passing selections, QBs do not appear as routine receiving selections, and WR/TE do not appear as routine rushing selections. This filters UI categories, not actual role eligibility or participation; active/inactive status still requires dated authoritative evidence.

**Quote handling**: Without `SPORTSGAMEODDS_API_KEY`, BTA presents a **manual exact-market input**. With an allowed API key, `SportsGameOdds v2` may show timestamped FanDuel/DraftKings quotes for a matched game/player. Join requires exact normalized team names, home/away match, event time within four hours, unambiguous name-to-position matching, available=true, a recognized full-game market, American odds, and a published price timestamp no more than 25 minutes old. The free quota is tiny and the feed publishes at a delay. These observed quotes are NOT proof that a sportsbook still accepts a bet or that all void/settlement conditions match; neither alone authorizes certified BTA grades.

**Explicitly unsupported**: automated comprehensive exact lines for every game and player, all specialty markets, confidently active game rosters, continuous no-delay score streams, official injury status across all leagues, and calibrated future betting probabilities. These cannot be fabricated. The report must show pending when a decisive gate cannot be verified.


## New no-credit-card feed adapters (November 8, 2026)

The current market browser prefers optional PropLine (`PROPLINE_API_KEY`) with ParlayAPI (`PARLAY_API_KEY`) as fallback, fetched only after a member requests published lines. Only market keys with defined canonical full-game semantics are parsed. Player identities must exactly match observed rosters. A stale, reversed or ambiguous fixture, unrecognized period, truncated prop board or suspended market cannot establish a current offer. The server independently rechecks an original saved selection and price before considering the current market gate; an old price cannot silently pass if repriced. The earlier SportsGameOdds sections above describe the retained legacy adapter, not the new default. See `NEXT_SYSTEMS_ENGINEERING.md`.
