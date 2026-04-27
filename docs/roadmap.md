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
- Watchlist synthesis table with company, last price, screener, fundamentals highlight, peer context, consensus target range, consensus rating, updates, and actions.
- Published Oslo Screener dashboard embedded and parsed for watchlist signal matches.
- Fundamentals table backed by cached Yahoo/yfinance data.
- Consensus/source table and manual source editor.
- Significant-events table and manual event API.
- Descriptive benchmark tab with seeded peer groups and early own-history snapshots.
- Editable peer-group curation in the Benchmarks tab: group status, curation notes, peer role labels, and peer notes.
- Reviewed initial peer groups for NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK; tanker and offshore-service groups were split into tighter business-model groups.
- Source quality tab.
- GitHub repository connected at `keresell-coder/oslo-market-workspace`.

Important current limitations:

- Peer groups are editable and the initial focus groups are reviewed, but not trusted.
- Peer context in Watchlist is marked as missing, draft, reviewed, or trusted.
- Sector/index benchmarks are not configured.
- Own-history benchmarking needs more snapshots.
- Consensus data is provider-row based; reported analyst refs are not deduplicated across providers.
- Automated NewsWeb/event collection is not implemented.
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

## Later Sprints

### Sector And Own-History Benchmarking

- Add sector benchmark model: Oslo sector peer group, international peer group, optional sector index/proxy.
- Improve own-history charts/tables: current value, historical median, min/max, percentile, observation count.
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
