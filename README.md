# Oslo Stock web-app

Local-first Oslo Bors research workspace for a personal watchlist, later shareable with friends/investment-club style users. The Watchlist is the synthesis view; deeper tabs hold source detail, peer context, fundamentals, own-history context, technical indicators, and event/consensus context.

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

To open the app for normal Safari review after a sprint or update:

```bash
scripts/open_in_safari.sh
```

The script starts the local server in Terminal if needed, verifies `http://127.0.0.1:8765/api/health`, and opens Safari at `http://127.0.0.1:8765`.

Repository: `keresell-coder/oslo-market-workspace`

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

## Current App

- **Start**: concise intent, source/metric summary, limitations, and not-investment-advice disclaimer.
- **Watchlist**: main scan table with collapsed note editing, add/remove symbols, price, RSI14 dashboard alert, technical indicators, multiples, own history entry point, peer context status/counts, provider target/rating source rows, updates, and actions.
- **Fundamentals**: cached Yahoo/yfinance fields in grouped columns, metric guide/data-validation panel below the primary table, and expanded consensus/source row editor.
- **Own history**: dedicated tab for descriptive price-history context, compact price charts, local snapshot trend charts/rows, source/freshness/confidence metadata, and true-quarterly-history requirements.
- **Technical indicators**: `/api/technical-indicators` parses Oslo Screener `latest.csv` for RSI14, RSI6, MACD histogram, SMA50 distance, ADX14, MFI14, source signal, risk, stop-loss, and position sizing fields; the indicator guide sits behind a collapsed details control.
- **Benchmarks**: editable peer groups with curation status, role labels, peer notes, sector benchmark components, minimum-data checks, and reviewed manual/source-linked sector KPI input slots; peer metric tables are shown before supporting checklist and sector details.
- **RSI14 screener**: separate embedded/parsing tab for the published Oslo Screener dashboard. The dashboard was refreshed to the 05 May 2026 screener data after its Pages branch lagged the current `latest.csv`. Do not edit the Oslo Screener repository unless explicitly requested.
- **Sources**: source quality and limitations.

## Rules And Guardrails

- Free data is screening-grade only: delayed, incomplete, rate-limited, and sometimes wrong.
- Show source, timestamp/freshness, confidence, limitations, and missing data clearly.
- Missing data stays missing. Do not infer NAV/fleet values, P/NAV, EBIT/kg, backlog, ROE/CET1, LTV/WAULT, or sector KPIs from generic sector labels.
- Yahoo/yfinance target and rating-label data is one provider row by default, not verified consensus. Reported analyst refs may overlap across providers and are not deduplicated.
- Consensus/source rows may be `provider-row`, `manual-source`, or `manual-override`; manual rows carry review status, source URL, as-of date, currency, method note, and limitation note when known.
- Peer statuses are local curation markers only: `missing`, `draft`, `reviewed`, `trusted`. They do not create valuation verdicts.
- Backend-assisted peer groups stay `draft` until reviewed. Do not auto-assign a company to an unrelated existing peer group based only on sector labels.
- Sector benchmark components are explicit: Oslo peer group, international peer group, and optional sector index/proxy. Sector index/proxy rows are never inferred automatically.
- Minimum-data checks are visible before any derived valuation score/status marker is considered. Valuation scores remain disabled.
- Technical BUY/SELL/BUY-watch/SELL-watch labels are source signal names from the screener CSV/dashboard, not app investment advice.
- Preserve the **Technical indicators** tab and `/api/technical-indicators`; the RSI14 screener dashboard remains a separate tab.

## Current Data State

- Price history uses Yahoo/yfinance 1-year daily closes with observation count, range, percentile, sampled chart points, source, freshness, confidence, and limitations.
- Own-history uses local `fundamentals_snapshots`; Watchlist signals and compact snapshot charts require minimum observations.
- Fundamentals table default columns are grouped: company, price/size, valuation multiples, earnings/yield, consensus/source refs, source, and links.
- Fundamentals metric guide and validation panel explain fields, coverage, source quality, and missing-data caveats behind progressive disclosure below the main scan table.
- Peer groups can be edited in Benchmarks. Existing researched groups cover NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK; local database status may be `reviewed` or `trusted`.
- Tankers and offshore energy are split into tighter groups: crude tankers for FRO, product tankers for HAFNI, subsea/offshore services for DOFG, and offshore drilling rigs for ODL.
- Sector KPI input slots exist for shipping NAV/fleet/P/NAV, seafood EBIT/kg and harvest volume, offshore/defence backlog, bank ROE/CET1, and real-estate LTV/WAULT. Values remain missing in benchmark output until reviewed/trusted manual or source-linked inputs have source context.
- Remaining major gaps: true quarterly fundamental statement history, optional sector index/proxy curation, NewsWeb/event automation, and deployment/sharing.

## Verification

Before finishing code changes, run:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
```

Use the in-app browser for visual checks when UI changes. Specifically verify Watchlist, Fundamentals, Own history, Benchmarks, Technical indicators, and the separate RSI14 screener tab.

After every sprint or user-visible update, also run:

```bash
scripts/open_in_safari.sh
```

Leave the app available in Safari at `http://127.0.0.1:8765` unless the user asks to stop the local server.

## Documentation Discipline

After each completed task, update the relevant docs so they reflect what changed, what was verified, and what remains planned. Default continuation context is this `README.md` plus `docs/roadmap.md`; use more detailed docs only when needed.

## Recently Completed

**Own History Tab Streamlining**

- Moved the dense own-history surface out of the Fundamentals matrix and Benchmark page into a dedicated **Own history** tab between Fundamentals and Technical indicators.
- Kept the Watchlist Own history column as the entry point and changed it to open the matching row in the Own history tab.
- Split the Own history table into separate Company, Context signal, Price history, Local snapshots, Source/gate, and Detail columns.
- Fundamentals now focuses on current source fields, consensus refs, source metadata, and links.
- Benchmarks now focuses on peer/sector context; minimum-data checks still show own-history coverage requirements, but the detailed own-history component lives in the dedicated tab.
- Reused the existing `/api/fundamentals` payload and historical-context renderer, avoiding a new backend endpoint.

**Compact Charts And Trends**

- Added observation-gated compact price sparklines from sampled Yahoo/yfinance 1-year daily closes.
- Added compact own-multiple sparklines from local `fundamentals_snapshots`; charts stay gated until the existing local-snapshot minimum is met.
- Watchlist keeps its scan-first table and uses the Own history column as an entry point to the dedicated tab.
- Own history shows compact price trend context and keeps denser price/snapshot chart detail in row details.
- Benchmarks no longer repeats the own-history chart block; minimum-data gates still reference own-history coverage.
- Chart cards include source, freshness/timestamp, confidence, observation count/gates, and limitations through visible metadata or tooltip copy; no valuation verdict or recommendation language was added.
- Preserved peer status labels, explicit sector index/proxy curation, Technical indicators, `/api/technical-indicators`, and the separate RSI14 screener tab.
- Verified syntax, README API checks, Watchlist/Fundamentals/Benchmarks/Technical indicators/RSI14 navigation in the in-app browser, and Safari launch.

**Consensus Quality**

- Added explicit consensus/source row metadata for row type, review status, target currency, as-of date, source URL, method note, and limitation note.
- Kept Yahoo/yfinance target and rating fields labeled as provider-row data, not verified consensus.
- Changed Watchlist and Fundamentals wording from consensus conclusions toward provider/source rows and raw rating labels.
- Changed rating summaries so the app counts raw B/H/S provider rows but does not produce a majority or analyst-weighted BUY/HOLD/SELL recommendation.
- Expanded the Fundamentals consensus editor into grouped source, value, and quality sections, with a source-row table for reviewing stored rows.
- Preserved overlapping-analyst caveats, missing-data behavior, peer status labels, Technical indicators, `/api/technical-indicators`, Own history, and the separate RSI14 screener tab.
- Verified syntax, README API checks, in-app browser navigation for Watchlist/Fundamentals/Own history/Benchmarks/Technical indicators/RSI14 screener, and Safari launch.

**RSI14 Screener Dashboard Refresh**

- Confirmed the published Oslo Screener `latest.csv` was current at `generated_at=2026-05-05T08:26:03Z`, while the separate dashboard HTML was still showing 28 April 2026 data.
- Root cause: the `oslo-screener-dashboard` repository default branch was an older setup branch, so scheduled runs used stale workflow code and did not update the `gh-pages` branch served by GitHub Pages.
- Refreshed the dashboard to **Screener data: 05 May 2026** / **Generated: 05 May 2026 18:58 UTC**, pushed the fixed dashboard branch state, and published the refreshed `gh-pages` site.
- The refreshed dashboard shows source screener labels only: BUY 2, SELL 4, BUY-watch 4, SELL-watch 11, across 111 screened rows.
- Yahoo RSS and Oslo Bors news subfetches had rate-limit/source parse failures during generation; those limitations are visible in the dashboard source notes and do not change the screener data freshness.
- Verified the public dashboard URL, GitHub Pages deployment success, README API checks, and Safari launch.

**Oslo Screener Reliability Pass**

- Set `oslo-screener-dashboard` default branch to `main` so scheduled workflows run from the intended branch.
- Hardened `oslo-screener` daily/weekly workflows with concurrency, timeouts, `latest.csv` metadata/row verification, safer `git pull --rebase` before bot pushes, and optional dashboard workflow triggering when `DASHBOARD_WORKFLOW_TOKEN` is configured.
- Removed tracked `.DS_Store` from `oslo-screener` and ignored it going forward.
- Hardened `oslo-screener-dashboard` with later 09:30 UTC and backup 12:30 UTC weekday schedules, concurrency, output verification, `Pillow` in requirements, and dashboard source freshness rendering from the `latest.csv` `generated_at` metadata.
- Published the regenerated dashboard to `gh-pages`; the RSI14 tab should now show both the screener data date and source-generation freshness.
- Verified screener compile/tests, dashboard compile/generation, workflow YAML parsing, GitHub default branches, public dashboard output, web-app API checks, and Safari launch.

**Reviewed Sector KPI Inputs And Benchmark Polish**

- Added `/api/sector-kpi-inputs` for saving sector KPI input rows with value, unit/currency, period, source name, source URL, note, input type, and review status.
- Benchmark sector KPI rows now carry source-path guidance for shipping NAV/fleet/P/NAV, seafood harvest volume and EBIT/kg, offshore/defence backlog and utilisation, bank ROE/CET1, and real-estate LTV/WAULT.
- Unreviewed or unsourced KPI values stay missing in benchmark output; reviewed/trusted values appear only when source context is present.
- Benchmarks now include a collapsed sector KPI input editor while preserving peer status labels, explicit sector index/proxy rows, disabled valuation scores, and descriptive no-verdict language.
- Verified syntax, Watchlist, Fundamentals, Benchmarks, Technical indicators, the separate RSI14 screener tab, and the README API checks.
- Added a Safari launcher script and sprint closeout rule so the app is opened in Safari after future iterations.

**UI Simplification And Progressive Disclosure**

- Watchlist scan now appears first; note editing and add-symbol controls are collapsed behind details controls.
- Fundamentals and Technical indicators show the primary scan table before metric/indicator guides.
- Benchmarks show peer metric context before checklist and sector support blocks.
- Supporting explanations, policies, validation coverage, indicator thresholds, sector KPI placeholders, and editors remain available without dominating the first view.
- Frontend tab loading now avoids repeat fetches after a tab is already loaded, and dynamic Watchlist/Benchmark controls use delegated handlers instead of rebinding after every render.
- Two unused frontend helpers were removed. Future continuation should keep `README.md` and `docs/roadmap.md` as the default context and open deeper docs only for a specific implementation need.

## Next Sprint

**NewsWeb And Event Monitoring**

- Keep watchlist-first filtering.
- Confirm a reliable and permitted NewsWeb/Euronext source path before automation.
- Add event categories and a daily watchlist digest only after source handling is clear.

See `docs/roadmap.md` for the broader sprint plan.
