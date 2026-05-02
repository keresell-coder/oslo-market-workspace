# Oslo Stock web-app

Local-first Oslo Bors research workspace for a personal watchlist, later shareable with friends/investment-club style users. The Watchlist is the synthesis view; deeper tabs hold source detail, peer context, fundamentals, technical indicators, and event/consensus context.

The app is intentionally conservative. It must not produce buy/sell investment advice, and it must not label stocks cheap, expensive, fair, or neutral from standalone multiples. Valuation context must be relative to peers, sector, own history, source quality, and missing data.

## Run

```bash
python3 app/server.py
```

Open:

```text
http://127.0.0.1:8765
```

If the port is busy, stop the stale Python process or use a temporary local port. During development `8768` has often been used.

Repository: `keresell-coder/oslo-market-workspace`

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

## Current App

- **Start**: concise intent, source/metric summary, limitations, and not-investment-advice disclaimer.
- **Watchlist**: main scan table with collapsed note editing, add/remove symbols, price, RSI14 dashboard alert, technical indicators, multiples, own history, peer context status/counts, consensus target/rating, updates, and actions.
- **Fundamentals**: cached Yahoo/yfinance fields in grouped columns, metric guide/data-validation panel below the primary table, manual consensus source editor, descriptive own-history context, local snapshot trend rows, and true-quarterly-history requirements.
- **Technical indicators**: `/api/technical-indicators` parses Oslo Screener `latest.csv` for RSI14, RSI6, MACD histogram, SMA50 distance, ADX14, MFI14, source signal, risk, stop-loss, and position sizing fields; the indicator guide sits behind a collapsed details control.
- **Benchmarks**: editable peer groups with curation status, role labels, peer notes, sector benchmark components, minimum-data checks, and sector KPI placeholders; peer metric tables are shown before supporting checklist and sector details.
- **RSI14 screener**: separate embedded/parsing tab for the published Oslo Screener dashboard. Do not edit the Oslo Screener repository unless explicitly requested.
- **Sources**: source quality and limitations.

## Rules And Guardrails

- Free data is screening-grade only: delayed, incomplete, rate-limited, and sometimes wrong.
- Show source, timestamp/freshness, confidence, limitations, and missing data clearly.
- Missing data stays missing. Do not infer NAV/fleet values, P/NAV, EBIT/kg, backlog, ROE/CET1, LTV/WAULT, or sector KPIs from generic sector labels.
- Yahoo/yfinance target and recommendation data is one provider row by default, not verified consensus. Reported analyst refs may overlap across providers and are not deduplicated.
- Peer statuses are local curation markers only: `missing`, `draft`, `reviewed`, `trusted`. They do not create valuation verdicts.
- Backend-assisted peer groups stay `draft` until reviewed. Do not auto-assign a company to an unrelated existing peer group based only on sector labels.
- Sector benchmark components are explicit: Oslo peer group, international peer group, and optional sector index/proxy. Sector index/proxy rows are never inferred automatically.
- Minimum-data checks are visible before any derived valuation score/status marker is considered. Valuation scores remain disabled.
- Technical BUY/SELL/BUY-watch/SELL-watch labels are source signal names from the screener CSV/dashboard, not app investment advice.
- Preserve the **Technical indicators** tab and `/api/technical-indicators`; the RSI14 screener dashboard remains a separate tab.

## Current Data State

- Price history uses Yahoo/yfinance 1-year daily closes with observation count, range, percentile, source, freshness, confidence, and limitations.
- Fundamentals own-history uses local `fundamentals_snapshots`; Watchlist signals require minimum observations.
- Fundamentals table default columns are grouped: company, price/size, valuation multiples, earnings/yield, own history, consensus refs, source, and links.
- Fundamentals metric guide and validation panel explain fields, coverage, source quality, and missing-data caveats behind progressive disclosure below the main scan table.
- Peer groups can be edited in Benchmarks. Existing researched groups cover NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK; local database status may be `reviewed` or `trusted`.
- Tankers and offshore energy are split into tighter groups: crude tankers for FRO, product tankers for HAFNI, subsea/offshore services for DOFG, and offshore drilling rigs for ODL.
- Sector KPI placeholders exist for shipping NAV/fleet/P/NAV, seafood EBIT/kg and harvest volume, offshore/defence backlog, bank ROE/CET1, and real-estate LTV/WAULT. Values remain missing until reviewed manual/source-linked inputs exist.
- Remaining major gaps: reviewed sector KPI inputs, true quarterly fundamental statement history, compact charts, optional sector index/proxy curation, consensus quality improvements, NewsWeb/event automation, and deployment/sharing.

## Verification

Before finishing code changes, run:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
```

Use the in-app browser for visual checks when UI changes. Specifically verify Watchlist, Fundamentals, Benchmarks, Technical indicators, and the separate RSI14 screener tab.

## Documentation Discipline

After each completed task, update the relevant docs so they reflect what changed, what was verified, and what remains planned. Default continuation context is this `README.md` plus `docs/roadmap.md`; use more detailed docs only when needed.

## Recently Completed

**UI Simplification And Progressive Disclosure**

- Watchlist scan now appears first; note editing and add-symbol controls are collapsed behind details controls.
- Fundamentals and Technical indicators show the primary scan table before metric/indicator guides.
- Benchmarks show peer metric context before checklist and sector support blocks.
- Supporting explanations, policies, validation coverage, indicator thresholds, sector KPI placeholders, and editors remain available without dominating the first view.
- Frontend tab loading now avoids repeat fetches after a tab is already loaded, and dynamic Watchlist/Benchmark controls use delegated handlers instead of rebinding after every render.
- Two unused frontend helpers were removed. Future continuation should keep `README.md` and `docs/roadmap.md` as the default context and open deeper docs only for a specific implementation need.

## Next Sprint

**Reviewed Sector KPI Inputs And Benchmark Polish**

- Add reviewed manual/source-linked sector KPI inputs with source URL, source name, period, unit/currency, note, and review status.
- Review source paths for shipping NAV/fleet values, seafood EBIT/kg, offshore/defence backlog, bank ROE/CET1, and real-estate LTV/WAULT.
- Keep sector KPIs missing until reviewed inputs exist.
- Explicitly curate optional sector index/proxy rows where useful.

See `docs/roadmap.md` for the broader sprint plan.
