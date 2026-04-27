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
- Watchlist synthesis table with company, last price, RSI14 screener dashboard alert, technical indicators, multiples, own-history, peer context, consensus target range, consensus rating, updates, and actions.
- Published RSI14/Oslo Screener dashboard embedded and parsed for dashboard-alert matches plus visible RSI 14 values where cards are present.
- Published Oslo Screener `latest.csv` parsed for broader technical indicator coverage across the screener universe.
- Fundamentals table backed by cached Yahoo/yfinance data with grouped scan columns for price/size, valuation multiples, earnings/yield, own history, consensus refs, source, and links.
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
- Own-history context now appears primarily in Fundamentals, and the tab uses grouped scan columns; true quarterly fundamental history, charts, sector-specific metric history, and richer sector/index benchmarks still need more data and design work.
- Consensus data is provider-row based; reported analyst refs are not deduplicated across providers.
- Automated NewsWeb/event collection is not implemented.
- RSI14 dashboard coverage is limited to cards present in the published dashboard; broader technical coverage is available through `latest.csv`.
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

## Completed Sprint: Fundamentals Tab Streamlining

Goal: make the Fundamentals tab clean enough for repeated review by clarifying the purpose of each default column and moving dense context into grouped or expandable views.

Completed:

- Reviewed the default Fundamentals table purpose and reduced it from 18 top-level columns to 8 grouped columns: company, price/size, valuation multiples, earnings/yield, own history, consensus refs, source, and links.
- Bundled standalone valuation metrics into one compact multiple group while keeping missing P/NAV and EV/EBIT values explicit.
- Bundled EPS and dividend yield into a compact earnings/yield group.
- Moved market cap into price/size and target/source quality into consensus/source groups.
- Redesigned **Own history** so the default cell shows a compact signal, 52-week range position, snapshot count/status, observation count, and confidence.
- Kept price-window, quarterly-window, largest-gap, and snapshot-history tables available in expandable row details.
- Added stable table-layout and column-width rules for more consistent row density.
- Preserved descriptive, source-aware wording. No cheap/expensive/fair labels or buy/sell guidance were added.

Verified:

- Backend syntax with `python3 -m py_compile app/server.py`.
- Frontend syntax with `node --check app/static/app.js`.
- Required local API checks for Watchlist overview and MOWI fundamentals.
- In-app browser check of the Fundamentals tab default table and expanded own-history detail.
- Local browser screenshots at desktop and narrower widths.

Closed sprint boundaries:

- The streamlining sprint did not add new metrics or new data sources.
- Desktop/narrow behavior still relies on the table's horizontal scrolling model; a later design pass can add a separate small-screen card layout if repeated mobile use becomes important.
- True quarterly fundamental statements, charts, and sector-specific KPIs remain later work.

## Completed Sprint: RSI14 Screener Coverage

Goal: fill technical indicators from the Oslo Screener CSV output while preserving the embedded RSI14 dashboard as its own separate tool.

Completed:

- Located the current `latest.csv` in `keresell-coder/oslo-screener`, published at `https://keresell-coder.github.io/oslo-screener/latest.csv` with raw GitHub fallback.
- Added backend parsing for 111 screener rows with source generated time, data date, fetch timestamp, coverage count, and limitations.
- Added `/api/technical-indicators` with watchlist/full-universe filtering.
- Added a separate **Technical indicators** tab with RSI14, RSI6, RSI direction, MACD histogram, SMA50 distance, ADX14, MFI14, source signal, risk, stop-loss, and position fields.
- Added a Watchlist **Technical** column populated from `latest.csv`.
- Kept the existing **RSI14 screener** dashboard tab unchanged.
- Marked rows that also appear in the dashboard screener output with a dashboard alert tag.
- Used green highlighting for source BUY/BUY-watch signals and red for SELL/SELL-watch signals. Labels remain source signal names, not investment advice.
- Added a Technical Indicator Guide covering common threshold bands and used green/white/red dots on indicator values for supportive/neutral/not-supportive status.

Verified:

- Backend syntax with `python3 -m py_compile app/server.py`.
- Frontend syntax with `node --check app/static/app.js`.
- `/api/technical-indicators?universe=watchlist` and `universe=all`.
- `/api/watchlist-overview` includes `technicalSignal`.
- In-app browser checks of Watchlist, Technical indicators, and unchanged RSI14 screener dashboard tabs.

Closed sprint boundaries:

- No changes were made to the `keresell-coder/oslo-screener` repo or the embedded dashboard.
- Technical signals are displayed as external screening labels only.
- Deployment remains a later sprint.

## Later Sprints

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

### Fundamentals Metric Guide And Data Validation

- Add a Fundamentals metric guide/fact box similar to the Technical Indicator Guide.
- For each Fundamentals metric, explain what it shows, where it is commonly useful, common interpretation caveats, source quality, and missing-data limitations.
- Validate current yfinance-derived fields before adding more interpretation or visual status markers.
- Review sector-specific metrics and data sources, especially P/NAV for shipping companies such as HAFNI and FRO where NAV is a common valuation context.
- Decide whether P/NAV, NAV/fleet values, and other sector KPIs should be manual inputs, source-linked fields, or computed fields.
- Reassess which Fundamentals metrics belong in the default table versus expandable detail.
- Preserve the rule that standalone multiples cannot produce cheap/expensive/fair labels or buy/sell guidance.

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
