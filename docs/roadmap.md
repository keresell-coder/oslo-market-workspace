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
- Backend-assisted draft peer-group creation for new watchlist symbols without an existing group, with reuse of existing groups when the symbol is already a member.
- Source quality tab.
- GitHub repository connected at `keresell-coder/oslo-market-workspace`.

Important current limitations:

- Peer groups are editable and the initial focus groups are reviewed, but not trusted.
- Peer context in Watchlist is marked as missing, draft, reviewed, or trusted.
- New watchlist companies outside the reviewed groups can create draft peer groups, but backend-assisted candidates are screening-grade and require manual research before promotion.
- Sector/index benchmarks are not configured.
- Own-history benchmarking needs more snapshots and may belong primarily in Fundamentals as company-specific historical pricing context.
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

### Watchlist Expansion And Peer Group Creation

- Keep watchlist editing simple: add/remove symbols, edit watchlist notes, and show whether peer context is missing, draft, reviewed, or trusted.
- When a watchlist symbol has no peer group, the Benchmarks tab can create a draft peer group for this company.
- New draft peer-group workflow prefills the focus company and adds candidate peers from local/yfinance sector metadata where available.
- If a selected symbol already belongs to a peer group, reuse the existing group even if the symbol is a peer rather than the original focus company.
- Suggested manual review order for new companies: Oslo-listed peers first, then Nordic, then European, then international.
- Do not auto-assign a company to an unrelated existing peer group based only on sector labels.
- Add a peer-group research checklist in the UI: business fit, geography, listing, segment mix, scale, source quality, missing sector KPIs, and why each peer belongs.
- Consider a later assisted workflow that proposes peer candidates, but keep them marked draft until reviewed.

### Fundamentals Historical Pricing Context

- Evaluate moving own-history benchmarking from Benchmarks into Fundamentals, or duplicating a compact version there while keeping peer/sector context in Benchmarks.
- Add current versus own-history context for common multiples and sector-specific metrics where data is available.
- Start with recent history windows such as last 4 quarters and 52-week high/low, with observation count and data-source caveats.
- Show current value, historical median, min/max, percentile, and largest gaps to own history.
- Highlight only descriptive gaps, for example "above 4-quarter median" or "near 52-week high"; do not label the company cheap, expensive, or fairly valued.
- For Watchlist, surface the single most significant own-history signal only when data quality and observations are sufficient.
- Sector-specific examples to support later: seafood EBIT/kg and harvest volume, tankers NAV/fleet values and spot exposure, offshore backlog/day rates/utilisation, banks ROE/CET1/P/B, real estate LTV/WAULT/NAV, CPaaS gross margin/organic growth/leverage.
- Require freshness, source, and missing-data labels before showing historical context.

### Sector And Own-History Benchmarking

- Add sector benchmark model: Oslo sector peer group, international peer group, optional sector index/proxy.
- Improve own-history charts/tables if not moved fully into Fundamentals: current value, historical median, min/max, percentile, observation count.
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
