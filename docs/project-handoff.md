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
default branch: main
current sprint branch: codex/consensus-quality
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

Dashboard source repository:

```text
https://github.com/keresell-coder/oslo-screener-dashboard
```

Dashboard default branch is now `main`; published site content is served from `gh-pages`.

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
  - provider/source-row target
  - target upside from available source rows
  - raw rating-label row counts without a weighted recommendation
  - source quality, source count, and freshness
  - Own history entry point that opens the dedicated Own History tab
  - significant-update status
- Watchlist consensus cell opens the matching Fundamentals row for the ticker.
- Fundamentals endpoint:
  - `/api/fundamentals`
- Own History tab:
  - reuses `/api/fundamentals`
  - shows descriptive price-history context, compact price charts, local snapshot trend charts/rows, source/freshness/confidence metadata, and true-quarterly-history requirements
- Consensus source infrastructure:
  - `consensus_sources` table
  - `/api/consensus`
  - consensus/source row editor and stored source-row table in Fundamentals tab
  - row type, review status, target currency, as-of date, source URL, method note, and limitation note fields
- Benchmark context:
  - `/api/benchmarks`
  - editable peer groups with `draft`, `reviewed`, and `trusted` status
  - explicit Oslo peer, international peer, and optional sector index/proxy components
  - reviewed/source-linked sector KPI input slots
  - `/api/sector-kpi-inputs`
  - descriptive only, no valuation verdict
  - minimum-data checks still include own-history coverage, but detailed own-history context lives in the Own History tab
- Technical indicators:
  - `/api/technical-indicators`
  - separate Technical indicators tab
  - Watchlist Technical column
  - rows overlapping with the RSI14 dashboard are highlighted
- RSI14 screener dashboard:
  - embedded from `https://keresell-coder.github.io/oslo-screener-dashboard/`
  - refreshed to 05 May 2026 after the dashboard `gh-pages` branch lagged the current `latest.csv`
  - now renders `latest.csv` source-generation freshness from the CSV metadata header
  - dashboard workflow runs at 09:30 UTC and 12:30 UTC weekdays, after the screener producer, with manual dispatch support
  - source labels remain external screener labels only, not app advice
- Significant event infrastructure:
  - `significant_events` table
  - `/api/events`
  - manual/tracked entries only for now

## Important Data Caveats

- Yahoo/yfinance data is free, delayed, rate-limited, and incomplete.
- Yahoo/yfinance target price and rating-label data is single-source provider-row data by default and not verified consensus.
- The app must not imply majority, analyst-count weighted, or deduplicated BUY/HOLD/SELL consensus.
- NewsWeb automation is not implemented. Current NewsWeb use is ticker search links only.
- Peer groups are editable; initial focus groups are reviewed but not trusted.
- Backend-assisted peer groups stay `draft` until reviewed.
- Sector index/proxy rows are optional and must be explicitly curated as peer items; they are never inferred automatically from sector labels.
- Sector KPI values stay missing in benchmark output until reviewed/trusted manual or source-linked inputs include source context.
- Technical BUY/SELL labels are external screener CSV signal names, not app advice.
- The Oslo Screener CSV and the separate dashboard HTML can become stale independently. If the RSI14 tab date is old, compare `https://keresell-coder.github.io/oslo-screener/latest.csv` with `https://keresell-coder.github.io/oslo-screener-dashboard/` and check the dashboard repo default branch plus `gh-pages` deployment.
- `oslo-screener` daily workflow now verifies `latest.csv` metadata/columns/rows before publishing and can trigger dashboard refresh if `DASHBOARD_WORKFLOW_TOKEN` is configured in GitHub secrets.
- Compact chart lines are descriptive context only. Price charts use sampled Yahoo/yfinance daily closes and local own-multiple charts use `fundamentals_snapshots`; both stay gated when observation counts are below the configured minimums.

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

- Added explicit consensus/source row metadata for row type, review status, target currency, as-of date, source URL, method note, and limitation note.
- Kept Yahoo/yfinance target and rating fields labeled as provider-row data, not verified consensus.
- Expanded the Fundamentals consensus editor into grouped source, value, and quality sections.
- Added a source-row table below the editor so stored provider/manual rows are visible without crowding the scan table.
- Changed Watchlist/Fundamentals copy to source-row language and raw rating labels.
- Changed rating summaries so they count raw B/H/S provider rows but do not produce a majority or analyst-weighted BUY/HOLD/SELL recommendation.
- Preserved overlapping analyst-count caveats, missing-data behavior, peer statuses, Technical indicators, `/api/technical-indicators`, Own history, and the separate RSI14 screener tab.

## Completed Maintenance

- Confirmed the technical CSV was current at `generated_at=2026-05-05T08:26:03Z`, while the embedded RSI14 dashboard page was still showing 28 April 2026 data.
- Root cause: `oslo-screener-dashboard` defaulted to an older setup branch, so scheduled workflow runs did not update the served `gh-pages` dashboard.
- Refreshed and published the dashboard to `gh-pages`; the public page now shows **Screener data: 05 May 2026** and **Generated: 05 May 2026 18:58 UTC**.
- Fast-forwarded the dashboard default branch to the fixed `main` workflow state so future scheduled runs should update the served Pages branch.
- Source-news fetches during generation logged Yahoo RSS rate limits and Oslo Bors parse failures; the dashboard keeps those limitations visible.

## Completed Reliability Pass

- Updated `oslo-screener` workflow reliability: concurrency, timeouts, `latest.csv` verification, safer bot push flow, optional dashboard dispatch trigger, and `.DS_Store` cleanup.
- Updated `oslo-screener-dashboard` workflow reliability: default branch set to `main`, later primary schedule plus backup schedule, concurrency, HTML verification, explicit `Pillow` dependency, and source freshness display.
- Published regenerated dashboard content to `gh-pages`.
- Verification passed for screener compile/tests, dashboard compile/generation, generated HTML checks, GitHub branch state, web-app API checks, and Safari launch.

## Next Sprint Brief

Next priority: NewsWeb And Event Monitoring.

Goal:

- Add watchlist-first significant event monitoring only after a reliable and permitted source path is confirmed.

Tasks:

- Keep NewsWeb/Euronext collection source-aware and manual-friendly until automation is reliable.
- Add event categories such as earnings, contracts/orders, financing/private placements, dividends, insider activity, M&A, guidance/profit warnings, and corporate actions.
- Consider a daily watchlist digest.
- Preserve no-advice/no-verdict language, missing-data discipline, Technical indicators, and the separate RSI14 screener tab.

## Verification Checklist For Next Chat

1. Start server.
2. Open Watchlist tab.
3. Confirm rows render and Watchlist remains scan-first.
4. Open Fundamentals and confirm the grouped scan table uses provider/source target wording and the consensus/source row editor/table renders.
5. Open Own History and confirm price-history context, local snapshot charts/rows, and source/gate metadata render.
6. Open Technical indicators and confirm source date, coverage count, and dashboard alert tags render.
7. Open Benchmarks and confirm peer groups, sector components, minimum-data checks, and sector KPI input editor render without a repeated own-history block.
8. Open RSI14 screener and confirm the embedded dashboard is unchanged.
9. Confirm no cheap/expensive/fair/neutral valuation verdict labels exist.
10. Run README verification commands.
11. Run `scripts/open_in_safari.sh` and confirm Safari opens `http://127.0.0.1:8765`.
