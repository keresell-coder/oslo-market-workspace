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
- Editable SQLite-backed Watchlist with inline notes, add/remove flow, price, RSI14 screener alert, technical indicators, multiples, own history with expandable trend previews, peer context status/counts, consensus target/rating, updates, and actions.
- Published RSI14/Oslo Screener dashboard embedded and parsed for dashboard-alert matches.
- Published Oslo Screener `latest.csv` parsed through `/api/technical-indicators` for broader technical indicator coverage.
- Fundamentals tab with cached Yahoo/yfinance grouped scan columns, metric guide, validation panel, manual consensus source editor, descriptive own-history context, compact price charts, local snapshot trend charts/rows, and true-quarterly-fundamental-window requirements.
- Benchmarks tab with editable peer groups, peer statuses, role labels, peer notes, sector benchmark components, reviewed/source-linked sector KPI input slots, and minimum-data checks.
- Manual consensus/source table and significant-event table/API.
- Source quality tab and loading indicators.
- GitHub repository connected at `keresell-coder/oslo-market-workspace`.

Important current limitations:

- Peer groups are editable; researched groups can be marked `reviewed` or `trusted` locally, but all peer metrics remain descriptive.
- Backend-assisted peer groups stay `draft` until reviewed.
- Sector benchmark components are modeled, but optional sector index/proxy rows are only present when explicitly added.
- Sector KPI input slots exist for NAV/fleet/P/NAV, EBIT/kg, backlog, ROE/CET1, LTV/WAULT, and fleet values. Benchmark values stay missing until reviewed/trusted manual or source-linked inputs include source context.
- Derived valuation scores remain disabled; the app currently shows minimum-data requirements only.
- Own-history context uses daily price history, compact sampled price charts, local snapshots, and gated local snapshot charts. True quarterly fundamental statement history remains future work.
- Consensus data is provider-row based; reported analyst refs are not deduplicated across providers.
- Automated NewsWeb/event collection is not implemented.
- RSI14 dashboard coverage is limited to cards present in the published dashboard; broader technical coverage comes from `latest.csv`.

Continuation guardrails:

- Preserve the **Technical indicators** tab and `/api/technical-indicators`.
- Keep the **RSI14 screener** dashboard as a separate embedded dashboard tab.
- Before completing UI/tab work, verify Watchlist, Fundamentals, Benchmarks, Technical indicators, and RSI14 screener in the in-app browser.
- After every sprint or user-visible update, run `scripts/open_in_safari.sh` so Safari opens `http://127.0.0.1:8765`; leave the local server available unless the user asks to stop it.
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

### Reviewed Sector KPI Inputs And Benchmark Polish

- Added `/api/sector-kpi-inputs` for sector KPI rows with value, unit/currency, period, source name, source URL, note, input type, and review status.
- Added Benchmark UI for collapsed sector KPI editing under Sector context while preserving the scan-first peer metric layout.
- Added source-path guidance for shipping NAV/share, fleet value, P/NAV, seafood harvest volume and EBIT/kg, offshore/defence backlog, fleet/utilisation, bank ROE/CET1, and real-estate LTV/WAULT.
- Kept benchmark KPI values missing unless stored inputs are reviewed/trusted and include source context; draft values can be stored for review but are not surfaced as reviewed benchmark values.
- Kept optional sector index/proxy rows explicit through peer roles only; no automatic proxy inference was added.
- Preserved disabled valuation scores and descriptive benchmark output.
- Added `scripts/open_in_safari.sh` and documented Safari availability as a sprint closeout requirement.

Verified:

- Ran `python3 -m py_compile app/server.py`.
- Ran `node --check app/static/app.js`.
- Ran the README API checks for Watchlist, MOWI fundamentals, and watchlist technical indicators.
- Checked `/api/benchmarks?symbol=DOFG.OL` for source-path KPI rows, missing unreviewed values, and disabled valuation scores.
- Checked `/api/sector-kpi-inputs` with an empty non-mutating save payload.
- Used the in-app browser to verify Watchlist, Fundamentals, Benchmarks including the KPI editor, Technical indicators, and the separate RSI14 screener tab.
- Opened the app in Safari at `http://127.0.0.1:8765` for normal browser review.

### Compact Charts And Trends

Goal: add compact visual context for price and own-history trends without creating recommendation or valuation verdicts.

Scope:

- Add small price/own-history trend visuals where they clarify context without cluttering Watchlist.
- Keep chart inputs source-labeled, freshness-aware, and observation-gated.
- Place denser charts behind expandable row or tab detail where needed.
- Continue explicit optional sector index/proxy curation through peer rows only; do not infer proxy rows from sector labels.

Completed:

- Added sampled compact price chart payloads to Yahoo/yfinance 1-year daily close history, gated by the existing 120-observation price-history minimum.
- Added local own-multiple chart payloads from `fundamentals_snapshots`, gated by the existing 5-snapshot own-history minimum.
- Added expandable Watchlist Trend preview rows so compact charts are available without adding another scan column.
- Added compact price trend visuals to Fundamentals own-history cells and denser price/snapshot chart detail inside existing row details.
- Added Benchmarks own-history trend charts behind a details control.
- Kept chart metadata source-labeled, timestamp/freshness-aware, confidence-aware, and limitation-aware.
- Preserved no-advice/no-verdict language, peer status labels, explicit sector index/proxy rows only, Technical indicators, `/api/technical-indicators`, and the separate RSI14 screener tab.

Verified:

- Ran `python3 -m py_compile app/server.py`.
- Ran `node --check app/static/app.js`.
- Ran the README API checks for Watchlist, MOWI fundamentals, and watchlist technical indicators.
- Used the in-app browser to verify Watchlist including Trend preview, Fundamentals including chart rendering, Benchmarks including own-history chart details, Technical indicators, and the separate RSI14 screener tab.
- Opened the app in Safari at `http://127.0.0.1:8765` for normal browser review.

## Next Sprint

### Consensus Quality

- Improve consensus table/editor if current form becomes cramped.
- Add manual override fields for values not reliable from free APIs.
- Consider multiple consensus providers only if reliable and permitted.
- Preserve caveats about overlapping analyst counts across providers.

## Later Sprints

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
