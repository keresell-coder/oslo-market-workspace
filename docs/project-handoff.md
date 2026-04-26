# Project Handoff

## Current State

The project is a working local MVP for an Oslo Bors research workspace.

Repository:

```text
https://github.com/keresell-coder/oslo-market-workspace
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
  - consensus target
  - consensus recommendation summary
  - significant-update status
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

## Next Sprint Brief

First priority: tweak the consensus column in the Watchlist tab.

Problem:

- The current watchlist consensus cell is too detached from the Fundamentals tab.
- The target price shown on Watchlist should clearly derive from the same target/consensus data shown in Fundamentals.
- Target upside should be visible on Watchlist.
- BUY/HOLD/SELL should be visibly source-quality-aware.

Expected direction:

- Watchlist consensus cell should show:
  - target price
  - target upside
  - BUY/HOLD/SELL summary
  - confidence/source-count badge
  - stale/fresh status
- The consensus cell should link or navigate to the relevant Fundamentals/consensus detail for that ticker.
- The implementation should continue to avoid investment advice or valuation flags.

## Verification Checklist For Next Chat

1. Start server.
2. Open Watchlist tab.
3. Confirm rows render.
4. Confirm MOWI or NOD row shows consensus target and recommendation.
5. Open Fundamentals tab.
6. Confirm same target/consensus data appears there.
7. Confirm no cheap/expensive/neutral labels exist.

