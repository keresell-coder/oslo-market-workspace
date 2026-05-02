# Project Handoff

## Current State

The project is **Oslo Stock web-app**, a working local MVP for an Oslo Bors research workspace.

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

Repository:

```text
https://github.com/keresell-coder/oslo-market-workspace
```

Local git status:

```text
current branch: main
```

Local app:

```text
http://127.0.0.1:8765
```

Temporary local app URL often used during debugging:

```text
http://127.0.0.1:8768
```

Existing Oslo Screener Dashboard:

```text
https://keresell-coder.github.io/oslo-screener-dashboard/
```

The existing Oslo Screener repo/project should not be edited unless explicitly requested. This project only embeds/parses the published dashboard.

Published Oslo Screener technical CSV:

```text
https://keresell-coder.github.io/oslo-screener/latest.csv
```

Fallback raw CSV:

```text
https://raw.githubusercontent.com/keresell-coder/oslo-screener/main/latest.csv
```

## What Works

- Editable watchlist backed by SQLite.
- Safari launcher:
  - `scripts/open_in_safari.sh`
  - starts the local server in Terminal if needed, verifies `/api/health`, and opens Safari at `http://127.0.0.1:8765`
- Watchlist overview endpoint:
  - `/api/watchlist-overview`
- Watchlist front page shows:
  - ticker/name
  - sector
  - Oslo Screener signal
  - technical indicator signal from `latest.csv`
  - Fundamentals target
  - target upside
  - source-count recommendation summary
  - source quality, source count, and freshness
  - significant-update status
- Watchlist consensus cell opens the matching Fundamentals row for the ticker.
- Fundamentals endpoint:
  - `/api/fundamentals`
- Consensus source infrastructure:
  - `consensus_sources` table
  - `/api/consensus`
  - consensus source editor in Fundamentals tab
- Benchmark context:
  - `/api/benchmarks`
  - editable peer groups with `draft`, `reviewed`, and `trusted` status
  - explicit Oslo peer, international peer, and optional sector index/proxy components
  - reviewed/source-linked sector KPI input slots
  - `/api/sector-kpi-inputs`
  - descriptive only, no valuation verdict
- Technical indicators:
  - `/api/technical-indicators`
  - separate Technical indicators tab
  - Watchlist Technical column
  - rows overlapping with the RSI14 dashboard are highlighted
- Significant event infrastructure:
  - `significant_events` table
  - `/api/events`
  - manual/tracked entries only for now

## Important Data Caveats

- Yahoo/yfinance data is free, delayed, rate-limited, and incomplete.
- Yahoo/yfinance target price and recommendation data is single-source by default and not verified.
- The app must not imply analyst-count weighted BUY/HOLD/SELL consensus unless reviewed source data supports it.
- NewsWeb automation is not implemented. Current NewsWeb use is ticker search links only.
- Peer groups are editable; initial focus groups are reviewed but not trusted.
- Backend-assisted peer groups stay `draft` until reviewed.
- Sector index/proxy rows are optional and must be explicitly curated as peer items; they are never inferred automatically from sector labels.
- Sector KPI values stay missing in benchmark output until reviewed/trusted manual or source-linked inputs include source context.
- Technical BUY/SELL labels are external screener CSV signal names, not app advice.

## Current Running Server Notes

If refresh fails in Safari or the in-app browser, stale Python server processes are the most likely cause.

Useful check:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
lsof -nP -iTCP:8768 -sTCP:LISTEN
```

Stop stale process:

```bash
kill <PID>
```

Restart:

```bash
python3 app/server.py
```

Normal Safari review after every sprint or visible update:

```bash
scripts/open_in_safari.sh
```

Leave the app available in Safari at `http://127.0.0.1:8765` unless the user asks to stop it.

## Codex Chat/Project Notes

- User requested the Codex project/folder name **Oslo Stock web-app**.
- User requested the chat named **Add GitHub account to Codex** be added to this project. That chat exists locally and was created against the same original generated workspace path, but no supported Codex project/chat membership tool was exposed in this session. If the Codex UI still shows it outside the project after the folder rename, move it manually in the Codex app.
- After each completed task, update relevant documents so `README.md`, `docs/roadmap.md`, `docs/project-handoff.md`, `docs/links-and-resources.md`, and `AGENTS.md` stay aligned with completed work and next plans.

## Completed This Sprint

- Added `/api/sector-kpi-inputs` for reviewed manual/source-linked sector KPI rows with value, unit/currency, period, source name, source URL, note, input type, and review status.
- Added collapsed Benchmark UI for sector KPI editing under Sector context while preserving scan-first peer metric layout.
- Added source-path guidance for shipping NAV/share, fleet value, P/NAV, seafood harvest volume and EBIT/kg, offshore/defence backlog, fleet/utilisation, bank ROE/CET1, and real-estate LTV/WAULT.
- Kept benchmark KPI values missing unless stored inputs are reviewed/trusted and include source context.
- Preserved explicit optional sector index/proxy peer roles, disabled valuation scores, descriptive benchmark language, Technical indicators, and the separate RSI14 screener tab.
- Added `scripts/open_in_safari.sh` and documented that each sprint/user-visible update should leave Safari open at `http://127.0.0.1:8765`.

## Next Sprint Brief

Next priority: Compact Charts And Trends.

Goal:

- Add compact visual context for price and own-history trends without creating recommendation or valuation verdicts.

Tasks:

- Add small price/own-history trend visuals where they clarify context without cluttering Watchlist.
- Keep chart inputs source-labeled, freshness-aware, and observation-gated.
- Place denser charts behind expandable row or tab detail where needed.
- Continue explicit optional sector index/proxy curation through peer rows only; do not infer proxy rows from sector labels.
- Preserve no-advice/no-verdict language and missing-data discipline.

## Verification Checklist For Next Chat

1. Start server.
2. Open Watchlist tab.
3. Confirm rows render and Watchlist remains scan-first.
4. Open Fundamentals and confirm grouped scan table, own-history context, metric guide, and validation panel still render.
5. Open Technical indicators and confirm source date, coverage count, and dashboard alert tags render.
6. Open Benchmarks and confirm peer groups, sector components, minimum-data checks, and sector KPI input editor still render.
7. Open RSI14 screener and confirm the embedded dashboard is unchanged.
8. Confirm no cheap/expensive/fair/neutral valuation verdict labels exist.
9. Run README verification commands.
10. Run `scripts/open_in_safari.sh` and confirm Safari opens `http://127.0.0.1:8765`.
