# Roadmap

## Product Intent

Build a local-first Oslo Bors research workspace where the Watchlist is the main synthesis view. Each major research tab should contribute a compact Watchlist column so the user can scan what deserves deeper research.

Audience is primarily personal use, later shareable with friends/investment-club style users. The app should be practical, source-aware, and clear about limitations.

## Non-Negotiable Principles

- Do not provide buy/sell investment advice.
- Do not label stocks cheap, expensive, fair, or neutral from standalone multiples.
- Relative valuation needs peers, sector, own history, source quality, and missing-data context.
- Free data is screening-grade only; show source, timestamp/freshness, confidence, and limitations.
- Missing data should stay missing.
- Do not edit the existing Oslo Screener repository unless explicitly requested; this app only embeds/parses the published dashboard.

## Current State

Completed MVP pieces:

- Local Python/SQLite app with static frontend.
- Start page with disclaimer, intent, metric/source summary, and limitations.
- Editable SQLite-backed Watchlist with inline notes, add/remove flow, price, RSI14 screener alert, technical indicators, multiples, own history, peer context status/counts, consensus target/rating, updates, and actions.
- Published RSI14/Oslo Screener dashboard embedded and parsed for dashboard-alert matches.
- Published Oslo Screener `latest.csv` parsed through `/api/technical-indicators` for broader technical indicator coverage.
- Fundamentals tab with cached Yahoo/yfinance grouped scan columns, metric guide, validation panel, manual consensus source editor, descriptive own-history context, local snapshot trend rows, and true-quarterly-fundamental-window requirements.
- Benchmarks tab with editable peer groups, peer statuses, role labels, peer notes, sector benchmark components, sector KPI placeholders, and minimum-data checks.
- Manual consensus/source table and significant-event table/API.
- Source quality tab and loading indicators.
- GitHub repository connected at `keresell-coder/oslo-market-workspace`.

Important current limitations:

- Peer groups are editable; researched groups can be marked `reviewed` or `trusted` locally, but all peer metrics remain descriptive.
- Backend-assisted peer groups stay `draft` until reviewed.
- Sector benchmark components are modeled, but optional sector index/proxy rows are only present when explicitly added.
- Sector KPI placeholders exist, but values such as NAV/fleet/P/NAV, EBIT/kg, backlog, ROE/CET1, LTV/WAULT, and fleet values still need reviewed manual or source-linked inputs.
- Derived valuation scores remain disabled; the app currently shows minimum-data requirements only.
- Own-history context uses daily price history and local snapshots. True quarterly fundamental statement history and charts remain future work.
- Consensus data is provider-row based; reported analyst refs are not deduplicated across providers.
- Automated NewsWeb/event collection is not implemented.
- RSI14 dashboard coverage is limited to cards present in the published dashboard; broader technical coverage comes from `latest.csv`.

Continuation guardrails:

- Preserve the **Technical indicators** tab and `/api/technical-indicators`.
- Keep the **RSI14 screener** dashboard as a separate embedded dashboard tab.
- Before completing UI/tab work, verify Watchlist, Fundamentals, Benchmarks, Technical indicators, and RSI14 screener in the in-app browser.
- If README or this roadmap omits a major tab/API, update the docs before proceeding.

## Completed Sprints

### Peer Group Curation

- Added editable peer groups with statuses `draft`, `reviewed`, and `trusted`.
- Added peer role labels: focus company, Oslo peer, Nordic peer, European peer, international peer, and sector index/proxy.
- Added peer notes and a research checklist covering business fit, geography, listing, segment mix, scale, source quality, missing sector KPIs, and why each peer belongs.
- Researched initial groups for NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK; tanker and offshore groups were split into tighter business-model groups.
- Documented peer rationale in `docs/peer-group-curation.md`.

### Fundamentals Historical Pricing Context

- Added Fundamentals own-history context from Yahoo/yfinance 1-year daily closes and local `fundamentals_snapshots`.
- Added 52-week price range, last-four-calendar-quarter price windows, local multiple history, largest-gap detail, observation counts, source quality, and Watchlist signal gating.
- Kept language descriptive only, such as near 52-week high/low or above/below own-history median.

### Fundamentals Tab Streamlining

- Reduced the default Fundamentals table to grouped columns: company, price/size, valuation multiples, earnings/yield, own history, consensus refs, source, and links.
- Moved dense historical detail into expandable row sections.
- Preserved source, freshness/timestamp, confidence, limitations, and explicit missing values.

### RSI14 Screener Coverage

- Added `/api/technical-indicators` from Oslo Screener `latest.csv`, with watchlist/full-universe filtering, source timestamps, coverage, confidence/limitations, and dashboard-alert annotations.
- Added the **Technical indicators** tab and Watchlist technical column.
- Kept the existing **RSI14 screener** dashboard tab unchanged.
- Displayed source BUY/SELL/BUY-watch/SELL-watch labels as external screening labels only.

### Watchlist Expansion And Peer Group Creation

- Added simple watchlist editing and peer context status in Watchlist.
- Added draft peer-group creation for symbols without existing groups.
- Reused existing groups when a symbol is already a member.
- Preserved the rule that sector labels alone must not auto-assign unrelated peer groups.

### Fundamentals Metric Guide And Data Validation

- Added Fundamentals Metric Guide and `/api/fundamentals` metadata for displayed fields.
- Added loaded-row field coverage, fetched range, cache status, and missing-field validation.
- Kept P/NAV, EV/EBIT, NAV/fleet values, and sector KPIs missing until reviewed manual/source-linked input paths exist.
- Kept validation as source/mapping review only, not a scoring model.

### Sector And Own-History Benchmarking

- Added explicit sector benchmark components: Oslo peer group, international peer group, optional sector index/proxy.
- Added minimum-data checks for peer review status, loaded peer rows, peer metric coverage, 52-week price observations, local snapshots, and sector KPI inputs.
- Added sector KPI placeholders/input structure for shipping, seafood, offshore, defence, banks, and real estate.
- Improved own-history detail with snapshot trend rows and true-quarterly-window requirements.
- Kept valuation scores disabled and did not infer sector KPI values or sector index/proxy rows.

### UI Simplification And Progressive Disclosure

- Put Watchlist, Fundamentals, Benchmarks, and Technical indicators into a scan-first layout.
- Collapsed Watchlist note editing and add-symbol controls.
- Moved Fundamentals policy text, metric guide, data-validation coverage, and consensus editor below the primary table or behind details controls.
- Moved the Technical Indicator Guide behind a details control below the indicator table while keeping source date, fetch freshness, coverage, and no-advice wording visible in the summary.
- Reordered Benchmarks so peer metric tables appear before sector/checklist support blocks; sector KPI placeholders and peer data remain available behind details controls.
- Preserved all current tabs and APIs, including Technical indicators and the separate RSI14 screener dashboard.
- Added lightweight tab-load caching so heavier tabs are not refetched on every tab click.
- Replaced repeated dynamic event binding for Watchlist and Benchmark rows with delegated handlers, and removed unused frontend helpers.
- Process note: use `README.md` plus this roadmap as the default continuation context; open detailed docs or source files only when they are directly needed for the current task.

Verified:

- Ran the README verification commands.
- Used the in-app browser to verify Watchlist, Fundamentals, Benchmarks, Technical indicators, and the RSI14 screener tab.
- Checked the narrow in-app browser layout for readable wrapped labels, horizontal table scrolling, and collapsed support sections.
- After the delegated-handler cleanup, repeated syntax/API checks passed; a second in-app browser pass was blocked because the browser-control tool was unavailable in the active tool list.

## Next Sprint

### Reviewed Sector KPI Inputs And Benchmark Polish

Goal: replace placeholder-only sector KPI scaffolding with reviewed manual/source-linked inputs while preserving missing-data discipline.

Scope:

- Add UI/API flow for reviewed manual/source-linked sector KPI values with source URL, source name, period, unit/currency, note, and review status.
- Review source paths for shipping NAV/fleet values, seafood EBIT/kg, offshore/defence backlog, bank ROE/CET1, and real-estate LTV/WAULT.
- Explicitly curate optional sector index/proxy rows where useful.
- Consider compact own-history charts after trend data and true quarterly windows are stable.

## Later Sprints

### Compact Charts And Trends

- Add small price/own-history trend visuals where they clarify context without creating valuation labels.
- Keep chart inputs source-labeled and observation-gated.
- Avoid cluttering Watchlist; use expandable row or tab detail for dense charts.

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
