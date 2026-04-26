# Roadmap

## Current MVP Status

**Oslo Stock web-app** is a local-first Oslo Bors workspace with:

- Editable SQLite-backed watchlist.
- Embedded Oslo Screener Dashboard tab.
- Watchlist alerts when published Oslo Screener signals overlap with watched stocks.
- Front-page watchlist dashboard with ticker/name, sector, screener signal, Fundamentals target, target upside, source-count recommendation summary, source quality, freshness, and significant-update status.
- Fundamentals table backed by cached Yahoo/yfinance data.
- Explicit source/provenance notes for target prices.
- Consensus/source table added for target-price provenance.
- Consensus source editor added for manual/reviewed source entry.
- Significant-events table added for manually tracked alerts.
- Descriptive peer benchmark tab.
- Own-history snapshot collection started.
- Source quality page.
- GitHub repository established at `keresell-coder/oslo-market-workspace`.
- Local `main` branch connected to `origin/main`.
- Local project folder renamed to `/Users/ke/Documents/Oslo Stock web-app`.

## Documentation Practice

After each completed task, update the relevant documents so the project record stays current:

- `README.md` for current behavior and limitations.
- `docs/roadmap.md` for completed work and next planned work.
- `docs/project-handoff.md` for continuation context.
- `docs/links-and-resources.md` when locations, links, endpoints, or source notes change.

## Design Principles

- Do not show cheap/expensive/neutral labels from standalone multiples.
- Valuation is relative to business model, sector, peers, cycle, and history.
- Any future score must expose its criteria, data source, timestamp, and confidence.
- Missing data should stay missing; do not manufacture values.
- Free data is acceptable for screening, but not for verified investment conclusions.

## Sprint 1: Data Provenance And Consensus Quality

Status: complete for MVP scope.

Completed:

- Added local `consensus_sources` table.
- Added `/api/consensus` read endpoint.
- Added manual consensus/source write endpoint.
- Added consensus source editor UI.
- Fundamentals rows now expose:
  - target source count
  - target confidence
  - target status
  - consensus source stale status
  - Yahoo/yfinance method warning
- Watchlist front page now shows consensus target and recommendation summary.
- Watchlist loading no longer depends on screener-alert loading.
- Benchmark loading now shows UI errors instead of silently failing.

Goal: make the fundamentals tab more trustworthy before expanding the analysis.

Carried forward:

- Add manual override fields for values not reliably available from free APIs.
- Automate collection from additional sources only if reliable and permitted.
- Improve consensus source display into a dedicated sortable table if the current editor becomes too cramped.

Deliverable:

- Fundamentals tab shows source quality per target/consensus field.
- No consensus value is presented as verified unless at least the source and timestamp are visible.

## Sprint 2: Peer Group Curation

### Watchlist Consensus Column

Status: complete.

Goal: make the Watchlist consensus cell clearly derive from the Fundamentals/consensus data.

Completed:

- Show consensus target price and target upside together in the Watchlist row.
- Show BUY/HOLD/SELL summary with source count, confidence, and freshness.
- Make the cell link to or focus the corresponding Fundamentals/consensus detail.
- Ensure the result is based on the same data shown in the Fundamentals tab.
- Keep the wording clear that this is source data, not verified investment advice.

Deliverable:

- Watchlist consensus column is compact, traceable, and consistent with Fundamentals.

### Peer Group Curation

Goal: make the benchmark tab credible enough to use as research context.

Tasks:

- Add editable peer groups in the app.
- Add peer group status:
  - draft
  - reviewed
  - trusted
- Add role labels:
  - focus company
  - Oslo peer
  - Nordic peer
  - international peer
  - sector index/proxy
- Review initial peer groups:
  - NOD: semiconductors
  - MOWI: seafood
  - FRO/HAFNI: tankers
  - DOFG/ODL: offshore energy services
  - KOG: defence/aerospace
  - LINK: communications software
- Add notes explaining why each peer belongs or does not belong.
- Keep unreviewed groups clearly marked as draft.

Deliverable:

- Benchmark tab distinguishes draft peer context from reviewed peer context.

## Sprint 3: Sector And Own-History Benchmarking

Goal: add the missing valuation context that makes relative analysis useful.

Tasks:

- Add sector benchmark model:
  - Oslo sector peer group
  - international sector peer group
  - optional sector index/proxy
- Add own-history charts/tables:
  - current value
  - historical median
  - historical min/max
  - percentile in own history
  - observation count
- Add minimum-data requirements before displaying any derived valuation score.
- Add sector-specific metric placeholders:
  - shipping/tankers: NAV discount/premium, fleet exposure, day-rate sensitivity
  - seafood: EBIT/kg, harvest volume, biomass, feed cost exposure
  - offshore/oil service: backlog, book-to-bill, net debt/EBITDA
  - financials: P/B, ROE, CET1
  - real estate: P/NAV, LTV, occupancy, WAULT
  - technology/software: EV/Sales, growth, gross margin, FCF margin

Deliverable:

- Benchmark tab can compare a company against peers, sector context, and own history without producing a simplistic verdict.

## Sprint 4: NewsWeb And Event Monitoring

Goal: monitor relevant company events without becoming a noisy news site.

Status: data model started; automated collection not started.

Completed foundation:

- Added local `significant_events` table.
- Added `/api/events` read/write endpoint.
- Watchlist front page displays significant-update alert status.

Tasks:

- Keep watchlist-first filtering.
- Add event categories:
  - earnings
  - contract/order
  - financing/private placement
  - dividend
  - insider
  - M&A
  - guidance/profit warning
  - corporate action
- Confirm a reliable and acceptable NewsWeb/Euronext fetch method before automated collection.
- Store event metadata:
  - symbol
  - title
  - URL
  - published time
  - category
  - source
  - importance
- Add daily watchlist digest.

Deliverable:

- Relevant watchlist events are surfaced without copying the whole NewsWeb feed.

## Sprint 5: Sharing And Deployment

Goal: make the app usable beyond the local machine.

Options:

- Same-network local access for phone testing.
- Small private VPS.
- Private cloud app.
- PWA polish for home-screen shortcut.

Tasks:

- Add environment-based configuration.
- Add basic authentication before sharing externally.
- Decide database path and backup strategy.
- Add deployment documentation.
- Add GitHub Actions checks.

Deliverable:

- A shareable private version suitable for a small group of friends.

## Deferred

- Paid real-time market data.
- Automated broker-estimate scraping.
- Any buy/sell recommendation engine.
- Financial transaction or portfolio execution features.
