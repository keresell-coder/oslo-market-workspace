# Roadmap

## Product Intent

Build a local-first Oslo Bors research workspace where the Watchlist is the main synthesis view. Each major research tab should contribute a compact Watchlist column so the user can scan the most relevant data and decide what deserves deeper research.

Audience is primarily personal use, later shareable with friends/investment-club style users. The app should be practical, source-aware, and clear about limitations.

## Non-Negotiable Principles

- Do not provide buy/sell investment advice.
- Do not label stocks cheap, expensive, or neutral from standalone multiples.
- Relative valuation needs peers, sector, own history, source quality, and missing-data context.
- Free data is screening-grade only; show source, timestamp/freshness, confidence, and limitations.
- Missing data should stay missing.
- Do not edit the existing Oslo Screener repository unless explicitly requested; this app only embeds/parses the published dashboard.

## Current State

Completed MVP pieces:

- Local Python/SQLite app with static frontend.
- Start page with concise disclaimer, intent, metric/source summary, and limitations.
- Editable watchlist backed by SQLite.
- Watchlist synthesis table with company, last price, RSI14 screener, multiples, own-history, peer context, consensus target range, consensus rating, updates, and actions.
- Published RSI14/Oslo Screener dashboard embedded and parsed for watchlist signal matches plus visible RSI 14 values where cards are present.
- Fundamentals table backed by cached Yahoo/yfinance data.
- Fundamentals historical context column with Yahoo/yfinance 52-week daily close range, local fundamentals snapshot history, source/freshness/confidence labels, and minimum-observation Watchlist signal gating.
- Consensus/source table and manual source editor.
- Significant-events table and manual event API.
- Descriptive benchmark tab with seeded peer groups and early own-history snapshots.
- Editable peer-group curation in the Benchmarks tab: group status, curation notes, peer role labels, and peer notes.
- Reviewed initial peer groups for NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK; tanker and offshore-service groups were split into tighter business-model groups.
- Backend-assisted draft peer-group creation for new watchlist symbols without an existing group, with reuse of existing groups when the symbol is already a member.
- Source quality tab.
- Loading indicators on refresh buttons, main data panes, and the status pill while async refreshes are running.
- GitHub repository connected at `keresell-coder/oslo-market-workspace`.

Important current limitations:

- Peer groups are editable and the initial focus groups are reviewed, but not trusted.
- Peer context in Watchlist is marked as missing, draft, reviewed, or trusted.
- New watchlist companies outside the reviewed groups can create draft peer groups, but backend-assisted candidates are screening-grade and require manual research before promotion.
- Sector/index benchmarks are not configured.
- Own-history context now appears primarily in Fundamentals, but true quarterly fundamental history, charts, and sector-specific metric history still need more data and design work.
- Consensus data is provider-row based; reported analyst refs are not deduplicated across providers.
- Automated NewsWeb/event collection is not implemented.
- RSI14 coverage is limited to cards present in the published dashboard; a published `latest.csv` or equivalent full dataset is still needed for all 111 screened stocks.
- Sector-specific metrics such as NAV, EBIT/kg, backlog, ROE/CET1, LTV/WAULT, and fleet values need better data or manual inputs.

## Completed Sprint: Peer Group Curation

Goal: make benchmark context credible enough to use as research context without creating a valuation verdict.

Completed:

- Add editable peer groups in the app.
- Add peer group status: draft, reviewed, trusted.
- Add peer role labels: focus company, Oslo peer, Nordic peer, international peer, sector index/proxy.
- Add peer notes explaining why each peer belongs or does not belong.
- Keep unreviewed peer groups clearly marked.
- Review initial groups for:
  - NOD: semiconductors
  - MOWI: seafood
  - FRO: crude tankers
  - HAFNI: product tankers
  - DOFG: subsea and offshore services
  - ODL: offshore drilling rigs
  - KOG: defence/aerospace
  - LINK: communications software

Deliverable:

- Benchmark tab and Watchlist peer column distinguish missing, draft, reviewed, and trusted peer context.
- Peer rationale and source notes are documented in `docs/peer-group-curation.md`.

## Completed Sprint: Fundamentals Historical Pricing Context

Goal: move own-history context into Fundamentals and keep any Watchlist signal descriptive, source-aware, and observation-gated.

Completed:

- Add a Fundamentals own-history column.
- Add Yahoo/yfinance 1-year daily close context with current value, median, low/high range, percentile/range position, observation count, source, confidence, freshness, and limitations.
- Add last-four-calendar-quarter price windows from Yahoo/yfinance daily closes.
- Add local fundamentals snapshot context for common multiples, including current value, historical median, min/max, percentile, observation count, and versus-history median gap.
- Add expandable Fundamentals detail tables for 52-week price range, quarterly price windows, largest own-multiple gaps, and snapshot history.
- Surface one Watchlist own-history signal only when minimum observation thresholds are met.
- Keep language descriptive, for example near 52-week high/low or above/below own-history median, without cheap/expensive/fair or buy/sell/hold conclusions.

Verified:

- Backend syntax with `python3 -m py_compile app/server.py`.
- Frontend syntax with `node --check app/static/app.js`.
- Required local API checks for Watchlist overview and MOWI fundamentals.
- In-app browser check of the Fundamentals tab.

Closed sprint boundaries:

- True quarterly fundamental statement history remains a later data-model task; this sprint uses daily price windows plus local fundamentals refresh snapshots.
- Sector-specific historical KPIs such as EBIT/kg, NAV/fleet values, backlog, ROE/CET1, LTV/WAULT, and CPaaS margin/growth/leverage remain later manual/source-data work.
- Sector and peer context remain separate from own-history signals until source quality and missing-data rules are stronger.

## Later Sprints

### RSI14 Screener Coverage

- Publish or locate the screener `latest.csv` / full output dataset.
- Parse RSI14 for every watchlist symbol that is part of the 111-stock screener universe, not only symbols shown as current dashboard cards.
- Keep RSI14 as technical screening context only; no buy/sell recommendation should be inferred from RSI alone.
- Show source date, source coverage count, and missing-status labels for symbols outside the published dataset.

### Watchlist Expansion And Peer Group Creation

- Keep watchlist editing simple: add/remove symbols, edit watchlist notes, and show whether peer context is missing, draft, reviewed, or trusted.
- When a watchlist symbol has no peer group, the Benchmarks tab can create a draft peer group for this company.
- New draft peer-group workflow prefills the focus company and adds candidate peers from local/yfinance sector metadata where available.
- If a selected symbol already belongs to a peer group, reuse the existing group even if the symbol is a peer rather than the original focus company.
- Suggested manual review order for new companies: Oslo-listed peers first, then Nordic, then European, then international.
- Do not auto-assign a company to an unrelated existing peer group based only on sector labels.
- Add a peer-group research checklist in the UI: business fit, geography, listing, segment mix, scale, source quality, missing sector KPIs, and why each peer belongs.
- Consider a later assisted workflow that proposes peer candidates, but keep them marked draft until reviewed.

### Sector And Own-History Benchmarking

- Add sector benchmark model: Oslo sector peer group, international peer group, optional sector index/proxy.
- Improve own-history charts/tables in Fundamentals: trend view, true quarterly windows, and clearer missing-data states.
- Add minimum-data requirements before any derived valuation score.
- Add sector-specific metric placeholders and manual inputs where needed.

### Consensus Quality

- Improve consensus table/editor if current form becomes cramped.
- Add manual override fields for values not reliable from free APIs.
- Consider multiple consensus providers only if reliable and permitted.
- Preserve caveats about overlapping analyst counts across providers.

### NewsWeb And Event Monitoring

- Keep watchlist-first filtering.
- Add event categories: earnings, contract/order, financing/private placement, dividend, insider, M&A, guidance/profit warning, corporate action.
- Confirm reliable/permitted NewsWeb or Euronext fetch method before automation.
- Add daily watchlist digest.

### Sharing And Deployment

- Add environment-based config.
- Add basic authentication before external sharing.
- Decide database path and backup strategy.
- Add deployment documentation.
- Add GitHub Actions checks.

## Deferred

- Paid real-time market data.
- Automated broker-estimate scraping unless source rights and stability are clear.
- Any recommendation engine.
- Financial transaction or portfolio execution features.
