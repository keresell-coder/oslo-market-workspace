# Oslo Stock web-app

Local-first Oslo Bors research workspace for a personal watchlist, later shareable with friends/investment-club style users. The goal is to keep the most relevant screening data and synthesis in one app: screener signals, source-labeled fundamentals, peer context, consensus data, and significant updates.

The app is intentionally conservative. It must not produce buy/sell investment advice, and it must not label stocks cheap, expensive, or neutral from standalone multiples. Valuation context must be relative to peers, sector, own history, source quality, and missing data.

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

- **Start**: first page, with short intent text, metric/source summary, current limitations, and a not-investment-advice disclaimer.
- **Watchlist**: main synthesis table. Current columns: company, last price, RSI14 screener dashboard alert, technical indicators, multiples, own history, peer context, consensus target range, consensus rating, updates, and actions.
- **Fundamentals**: cached Yahoo/yfinance fields in grouped scan columns, watchlist or full ticker-database universe, manual consensus source editor, and descriptive own-history context from 52-week daily closes plus local fundamentals snapshots.
- **Technical indicators**: parses the published Oslo Screener `latest.csv` for RSI14, RSI6, MACD histogram, SMA50 distance, ADX14, MFI14, source signal, risk, and sizing fields. Rows that also appear in the RSI14 dashboard are highlighted, and indicator values use green/white/red status dots with a threshold guide.
- **Benchmarks**: descriptive peer context with editable peer groups, curation status, role labels, and peer notes. Initial watchlist peer groups have been researched and marked reviewed, not trusted. New symbols can create backend-assisted draft peer groups from local/yfinance sector metadata.
- **RSI14 screener**: embeds/parses the published Oslo screener dashboard only. Do not edit the existing Oslo Screener repository unless explicitly requested.
- **Sources**: source quality and limitations.

## Data And Wording Rules

- Free data is screening-grade only: delayed, incomplete, rate-limited, and sometimes wrong.
- Show source, timestamp/freshness, confidence, and missing data clearly.
- Yahoo/yfinance target and recommendation data is one provider row by default, not verified consensus.
- “Reported analyst refs” are provider-reported analyst counts; they may overlap across providers and are not deduplicated.
- Peer group statuses are local curation markers only: draft, reviewed, or trusted. They do not create a valuation verdict.
- Reviewed peer groups still depend on source quality, sector KPIs, and missing-data context.
- Fundamentals own-history context is descriptive only. Watchlist own-history signals require minimum observation counts and must not be read as valuation conclusions.
- 52-week price ranges come from Yahoo/yfinance daily closes when data is refreshed; local multiple history depends on repeated fundamentals refresh snapshots.
- RSI14 dashboard values are parsed only from cards present in the published dashboard. Broader technical indicator coverage comes from the published Oslo Screener `latest.csv`.
- Technical BUY/SELL/BUY-watch/SELL-watch labels are source signal names from the screener CSV, not app investment advice.
- Future consensus work should combine multiple providers carefully and preserve overlap/deduplication caveats.
- NewsWeb automation is not implemented; current use is ticker search links and manual event entries.

## Current Historical Context State

- The Fundamentals table has streamlined default columns: company, price/size, valuation multiples, earnings/yield, own history, consensus refs, source, and links.
- The **Own history** default cell is compact: signal label, 52-week range position, snapshot count/status, observation count, and confidence.
- Price history uses Yahoo/yfinance 1-year daily close data, including observation count, low/high range, percentile, source, freshness, confidence, and limitations.
- Price history also exposes last-four-calendar-quarter windows from the same daily close source.
- Local multiple history uses dated `fundamentals_snapshots`; it starts as insufficient until enough refresh snapshots exist, but the Fundamentals detail view still shows available observations.
- The Watchlist Fundamentals cell can show one descriptive own-history signal only when the price window or snapshot history passes minimum observation requirements.
- Fundamentals rows include expandable own-history detail tables for price windows, largest own-multiple gaps, and snapshot history.
- Refresh actions show a visible spinner in the clicked control and status pill while loading.
- Current signals are descriptive labels such as “near 52-week high/low” or “P/B above own-history median”; they are not buy/sell/hold guidance and do not label valuation cheap, expensive, or fair.
- Remaining gaps: true quarterly fundamental history, sector-specific metrics, sector/index benchmarks, charts, and manual sector KPI inputs.

## Completed Sprint: Fundamentals Tab Streamlining

Goal: make the Fundamentals tab easier to scan and review by reducing table clutter, standardizing column purpose and width, and moving dense context into deliberate grouped views.

Completed:

- Reduced the default Fundamentals table from 18 columns to 8 purposeful grouped columns.
- Bundled standalone metrics into valuation multiples, earnings/yield, price/size, consensus refs, source, and links.
- Redesigned **Own history** as a compact top-level summary with detailed price-window, quarterly-window, largest-gap, and snapshot tables behind an expandable control.
- Added stable width rules for the grouped Fundamentals columns.
- Kept source, freshness/timestamp, confidence, limitations, and missing values visible without adding valuation verdicts.

Verified:

- Backend syntax with `python3 -m py_compile app/server.py`.
- Frontend syntax with `node --check app/static/app.js`.
- Required local API checks for Watchlist overview and MOWI fundamentals.
- In-app browser check of the Fundamentals tab, including the compact default table and expanded own-history detail.
- Local browser screenshots at desktop and narrower widths for the Fundamentals tab.

## Completed Sprint: RSI14 Screener Coverage

Goal: use the full Oslo Screener CSV output for technical indicator coverage while keeping the embedded RSI14 dashboard as a separate tab/tool.

Completed:

- Located `latest.csv` in `keresell-coder/oslo-screener`, published at `https://keresell-coder.github.io/oslo-screener/latest.csv` with GitHub raw fallback.
- Added `/api/technical-indicators` with watchlist/full-universe filtering, source timestamps, coverage count, confidence/limitations text, and dashboard-alert annotations.
- Added a **Technical indicators** tab for RSI14, RSI6, MACD histogram, SMA50 distance, ADX14, MFI14, source signal, risk, stop-loss, and position fields.
- Added a Watchlist **Technical** column while leaving the existing **RSI14 screener** dashboard-alert column unchanged.
- Highlighted source BUY/BUY-watch signals in green and SELL/SELL-watch signals in red; dashboard-overlap rows get an additional dashboard alert marker.
- Added a Technical Indicator Guide with common screening thresholds and per-indicator status dots: green for supportive, white for neutral, and red for not supportive.

Verified:

- Backend syntax with `python3 -m py_compile app/server.py`.
- Frontend syntax with `node --check app/static/app.js`.
- `/api/technical-indicators?universe=watchlist` and `universe=all`.
- `/api/watchlist-overview` includes `technicalSignal`.
- In-app browser checks of Watchlist, Technical indicators, and unchanged RSI14 screener dashboard tabs.

## Next Sprint Candidate

**Watchlist Expansion And Peer Group Creation**

- Keep watchlist editing simple: add/remove symbols, edit watchlist notes, and show whether peer context is missing, draft, reviewed, or trusted.
- Add a peer-group research checklist in the UI: business fit, geography, listing, segment mix, scale, source quality, missing sector KPIs, and why each peer belongs.
- Keep backend-assisted peer groups marked draft until reviewed.

## Later Sprint Note

**Fundamentals Metric Guide And Data Validation**

- Add a Fundamentals metric guide/fact box similar to the Technical Indicator Guide, explaining each displayed metric, what it indicates, common use cases, and key limitations.
- Review Fundamentals data quality and source mapping before adding more interpretation.
- Review sector-specific missing metrics, especially P/NAV for shipping names such as `HAFNI.OL` and `FRO.OL`, where NAV context is commonly used.
- Reassess which metrics belong in the default Fundamentals table versus expandable detail, while preserving no-advice wording and source/missing-data caveats.

## Verification

Before finishing code changes, run:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
```

Use the in-app browser for visual checks when UI changes.

## Current Peer Curation State

- Peer groups can be edited in the Benchmarks tab.
- If a symbol already belongs to a peer group, including as a peer rather than the original focus company, the app reuses that group.
- If a symbol has no peer group, the Benchmarks tab can create a `draft` group with the symbol as focus and screening-grade candidate peers from local/yfinance sector metadata.
- Group-level fields: name, description, status, and curation note.
- Peer-level fields: symbol, role, market, and note.
- Supported role labels: focus company, Oslo peer, Nordic peer, European peer, international peer, and sector index/proxy.
- Initial groups for NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK are marked `reviewed`.
- Tankers and offshore energy were split into tighter groups: crude tankers for FRO, product tankers for HAFNI, subsea/offshore services for DOFG, and offshore drilling rigs for ODL.
- Backend-assisted draft groups are not reviewed research. They must be checked for business fit, geography, segment mix, scale, source quality, and missing sector KPIs before promotion.
- See `docs/peer-group-curation.md` for the researched peer rationale and source notes.

## Continue In A New Chat

Load only:

- `README.md`
- `docs/roadmap.md`

Recommended prompt:

```text
Please read README.md and docs/roadmap.md in /Users/ke/Documents/Oslo Stock web-app, then continue from the current project state.

Use only those two files as the default continuation context unless more detail is needed.

Next sprint: Watchlist Expansion And Peer Group Creation.

Important constraints:
- Do not provide buy/sell investment advice.
- Do not label stocks cheap, expensive, or neutral from standalone multiples.
- Keep valuation context relative to peers, sector, own history, source quality, and missing data.
- Free data is screening-grade only; show source, timestamp/freshness, confidence, and limitations.
- Preserve peer status labels: missing, draft, reviewed, trusted.
- Keep backend-assisted peer groups marked draft until reviewed.
- Do not auto-assign a company to an unrelated existing peer group based only on sector labels.
- Leave the later Fundamentals Metric Guide And Data Validation sprint for a future pass; it should cover a Fundamentals fact box, P/NAV for shipping names such as HAFNI/FRO, and validation of current fundamentals data.
- Use the in-app browser for visual verification.
- After changes, update README.md and docs/roadmap.md if project state or next steps changed.
- Run the verification commands listed in README.md before finishing.
```
