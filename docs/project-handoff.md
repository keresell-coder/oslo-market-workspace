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
main tracks origin/main
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

## What Works

- Editable watchlist backed by SQLite.
- Watchlist overview endpoint:
  - `/api/watchlist-overview`
- Watchlist front page shows:
  - ticker/name
  - sector
  - Oslo Screener signal
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
- Significant event infrastructure:
  - `significant_events` table
  - `/api/events`
  - manual/tracked entries only for now

## Important Data Caveats

- Yahoo/yfinance data is free, delayed, rate-limited, and incomplete.
- Yahoo/yfinance target price and recommendation data is single-source by default and not verified.
- The app must not imply analyst-count weighted BUY/HOLD/SELL consensus unless reviewed source data supports it.
- NewsWeb automation is not implemented. Current NewsWeb use is ticker search links only.
- Peer groups are seeded but not reviewed.
- Sector index benchmarking is not configured.

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

- Watchlist consensus cell now uses the same Fundamentals target and target upside fields shown in the Fundamentals table.
- The cell shows source-count BUY/HOLD/SELL summary, confidence, source count, freshness, analyst references, and target source.
- Clicking the Watchlist target opens the Fundamentals tab and focuses the matching ticker row.
- The wording avoids implying verified analyst-count weighted advice.

## Next Sprint Brief

Next priority: peer group curation.

Goal:

- Make benchmark context credible enough to use as research context.

Tasks:

- Add editable peer groups in the app.
- Add peer group status: draft, reviewed, trusted.
- Add role labels: focus company, Oslo peer, Nordic peer, international peer, sector index/proxy.
- Review initial peer groups for NOD, MOWI, FRO/HAFNI, DOFG/ODL, KOG, and LINK.
- Add notes explaining why each peer belongs or does not belong.
- Keep unreviewed groups clearly marked as draft.

## Verification Checklist For Next Chat

1. Start server.
2. Open Watchlist tab.
3. Confirm rows render and the Watchlist consensus cells show target, upside, source quality, source count, freshness, and source-count recommendation.
4. Click a Watchlist consensus target and confirm Fundamentals opens at the matching row.
5. Open Benchmarks tab.
6. Confirm current peer groups still render.
7. Confirm no cheap/expensive/neutral labels exist.
