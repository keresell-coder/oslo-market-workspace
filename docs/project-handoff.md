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
current sprint branch: codex/rsi14-screener-coverage
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
- Sector index benchmarking is not configured.
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

## Codex Chat/Project Notes

- User requested the Codex project/folder name **Oslo Stock web-app**.
- User requested the chat named **Add GitHub account to Codex** be added to this project. That chat exists locally and was created against the same original generated workspace path, but no supported Codex project/chat membership tool was exposed in this session. If the Codex UI still shows it outside the project after the folder rename, move it manually in the Codex app.
- After each completed task, update relevant documents so `README.md`, `docs/roadmap.md`, `docs/project-handoff.md`, and `docs/links-and-resources.md` stay aligned with completed work and next plans.

## Completed This Sprint

- Added the Technical indicators tab using the Oslo Screener `latest.csv`.
- Added `/api/technical-indicators` with watchlist/full-universe filtering, source timestamps, coverage count, and source limitations.
- Added the Watchlist Technical column, separate from the existing RSI14 dashboard-alert column.
- Kept the embedded RSI14 screener dashboard tab unchanged.
- Dashboard-overlap rows are highlighted, and source BUY/BUY-watch labels use green while SELL/SELL-watch labels use red.
- Added a Technical Indicator Guide with common threshold bands and green/white/red dots on interpretive indicator values.
- The wording keeps technical signals as screening context only, not investment advice.

## Next Sprint Brief

Next priority: watchlist expansion and peer group workflow cleanup.

Goal:

- Keep watchlist and peer-group workflows efficient while preserving draft/reviewed/trusted source discipline.

Tasks:

- Keep watchlist editing simple: add/remove symbols, edit notes, and show peer context state.
- Add a peer-group research checklist in the UI.
- Keep backend-assisted peer groups marked draft until reviewed.
- Do not auto-assign a company to an unrelated existing peer group based only on sector labels.

## Verification Checklist For Next Chat

1. Start server.
2. Open Watchlist tab.
3. Confirm rows render and the Watchlist consensus cells show target, upside, source quality, source count, freshness, and source-count recommendation.
4. Confirm the Watchlist Technical column renders from `latest.csv`.
5. Open Technical indicators tab and confirm source date, coverage count, and dashboard alert tags render.
6. Open RSI14 screener tab and confirm the embedded dashboard is unchanged.
7. Click a Watchlist consensus target and confirm Fundamentals opens at the matching row.
8. Open Benchmarks tab and confirm current peer groups still render.
9. Confirm no cheap/expensive/neutral labels exist.
