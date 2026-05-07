# Project Handoff

## Current State

The project is **Oslo Stock web-app**, a working local MVP for an Oslo Bors research workspace.

Beta release target:

```text
Beta v0.1.0
```

Remaining beta-release sprints:

```text
1. Hosted Public Access Completion
2. Beta Release Hardening
```

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
current sprint branch: codex/hosted-public-access-completion
```

Local app:

```text
http://127.0.0.1:8765
```

Go-live direction:

```text
Next target is a controlled public MVP with HTTPS, authentication, one hosted
app instance, persistent SQLite storage, off-host backups, restore drill, and
cross-device verification.
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
- Sharing prep:
  - environment variables configure bind host, port, SQLite path, and optional Basic Auth
  - default run remains local-only at `127.0.0.1:8765`
  - non-local unauthenticated binds are refused unless explicitly overridden
  - `scripts/backup_database.sh`, `scripts/restore_database.sh`, and `scripts/drill_restore_database.sh` provide SQLite backup/restore/drill utilities with integrity checks
  - optional `OSLO_APP_BACKUP_MIRROR_DIR` mirrors backup files and checksums to a mounted off-host path
  - `deploy/oslo-stock.env.example`, `deploy/oslo-stock.service`, `deploy/Caddyfile.example`, and `deploy/oslo-stock-backup.cron.example` provide the single-host service/reverse-proxy/backup templates for the public-access path
  - `docs/hosted-public-access-runbook.md` records the host install, HTTPS/authentication, persistent SQLite, backup/restore drill, hosted refresh verification, another-device browser pass, and release-evidence sequence
  - `scripts/verify_public_deployment.sh` checks HTTPS, Basic Auth blocking, `/api/health`, the README API endpoints, and hosted `refresh=1` paths for Watchlist, Fundamentals, Technical indicators, News/Events, and Benchmarks against a hosted URL
  - `scripts/verify_public_deployment.sh` also supports local HTTP dry runs with `OSLO_ALLOW_HTTP_VERIFY=1` for script/endpoint validation only
  - Start tab plus `docs/operator-refresh-checklist.md` provide the beta refresh/review routine
  - refresh status strips on Watchlist, Fundamentals, Own history, Benchmarks, News/Events, Technical indicators, and Sources show last successful app refresh, source timestamp when available, source/cache details, and warnings/errors
  - Watchlist refresh uses true upstream/source refreshes for yfinance fundamentals, RSI14 dashboard parsing, Oslo Screener `latest.csv`, and on-demand NewsWeb rows; yfinance, RSI14, and technical CSV failures can show `stale-after-error` when old cached rows remain visible
  - `.env.example` and `docs/deployment-sharing.md` document the current sharing guardrails, backup workflow, target comparison, HTTPS/reverse-proxy expectations, and production access-control checklist
  - `docs/go-live-readiness.md` explains the 2-sprint minimum / 3-sprint recommended path to public MVP
  - GitHub Actions CI checks backend compile and frontend syntax
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
  - shows descriptive price-history context, compact price charts, local snapshot trend charts/rows, yfinance dated quarterly statement rows where available, primary-report review tracking, source/freshness/confidence metadata, and missing-data gates
  - `/api/quarterly-statement-reviews` stores manual/source-linked primary company-report review rows by symbol and period
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
  - `/api/event-monitoring`
  - News/Events tab with watchlist-first NewsWeb rows, a 24-hour on-demand daily digest grouped by symbol/category, event categories, source-quality status, source links, per-symbol fetch status, and manual/source-reviewed entry
  - NewsWeb rows are fetched on demand from the `api3.oslo.oslobors.no` endpoint used by the official NewsWeb frontend; scheduled digest automation remains separate

## Important Data Caveats

- Yahoo/yfinance data is free, delayed, rate-limited, and incomplete.
- Quarterly statement history uses yfinance quarterly income statement, balance sheet, and cash-flow tables only when they return dated quarter-end columns. Missing statement rows stay missing, statement values are not inferred from current summary fields, and each period stays not-primary-verified until a source-linked company-report review row is stored. Primary-report value entry/import remains future work.
- Yahoo/yfinance target price and rating-label data is single-source provider-row data by default and not verified consensus.
- The app must not imply majority, analyst-count weighted, or deduplicated BUY/HOLD/SELL consensus.
- Scheduled NewsWeb automation is not implemented. Current NewsWeb use is ticker search links, on-demand NewsWeb rows, an on-demand daily watchlist digest, and manual/source-reviewed significant-event rows.
- Basic Auth is a sharing-prep gate, not a full production security model. Backup/restore/drill, optional backup mirroring, hosted service/reverse-proxy templates, HTTPS/reverse-proxy expectations, target comparison, a hosted verification script, and an access-control checklist are now documented, but actual external deployment still needs a real domain/subdomain, DNS access, host credential, and mounted off-host backup destination.
- Actual hosted Sprint 1 deployment remains blocked until the operator provides a real domain/subdomain, DNS access, single-host SSH/deployment access, and a mounted off-host/encrypted backup destination.
- The app can go live soon as a controlled, authenticated MVP. It is not ready today for public access, and free/open data remains screening-grade rather than fully guaranteed/authoritative.
- NewsWeb source-path status as of 06 May 2026: official Euronext Oslo page identifies NewsWeb as the listed-company news site updated immediately 24/7. The official NewsWeb frontend discovers `api3.oslo.oslobors.no` via `urls.json`, and ticker queries return issuer announcements from `/v1/newsreader/customQuery`.
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

- Added Hosted Public Access Completion host-runbook and hosted refresh
  verification support:
  - `docs/hosted-public-access-runbook.md` now provides the host-side install,
    verification, backup/restore drill, public HTTPS verification, refresh
    verification, operator checklist, another-device browser pass, and
    release-evidence sequence.
  - `scripts/verify_public_deployment.sh` now runs hosted `refresh=1` checks for
    Watchlist, Fundamentals, Technical indicators, News/Events, and Benchmarks
    in addition to the baseline README API checks.
  - Cached/stale/error source states are allowed during hosted verification when
    the API returns usable JSON and keeps the state explicit.
  - Verification passed for backend/frontend/script syntax, README API checks,
    local restore drill, enhanced public verification script local dry run,
    in-app browser tab pass with no console errors, and Safari launch.
  - Real HTTPS, authentication, hosted backup mirror, hosted restore drill,
    operator checklist, and another-device browser checks remain blocked until
    domain/DNS/SSH host and backup-mount details are provided.

## Completed Previous Sprint

- Added Hosted Public Access Completion refresh/verification hardening:
  - `/api/watchlist-overview?refresh=1` now refreshes the source paths used by
    the Watchlist synthesis view instead of only reloading cached rows.
  - Watchlist refresh asks for fresh yfinance fundamentals, RSI14 dashboard
    parsing, Oslo Screener `latest.csv`, and on-demand NewsWeb rows.
  - yfinance, RSI14 dashboard parsing, and technical CSV refreshes now return
    visible `stale-after-error` cached fallback payloads when a live refresh
    fails after a previous successful fetch.
  - Watchlist, Fundamentals, Own history, Benchmarks, and Technical indicators
    refresh strips surface cache summaries and source-refresh errors where the
    API exposes them.
  - `scripts/verify_public_deployment.sh` local dry runs no longer fail on an
    empty auth argument array and keep real hosted HTTPS checks strict.
- Confirmed actual public URL deployment, hosted backup mirror setup, hosted
  restore drill, and another-device verification are still blocked pending real
  domain/DNS/host/backup-mount details.
- Verification passed for backend/frontend/script syntax, README API checks,
  explicit `refresh=1` checks, restore drill, local hosted-verification dry run,
  in-app browser tab checks with no console errors, and Safari launch.

## Completed Previous Sprint

- Added Data Refresh And Source-Quality Readiness UI:
  - Start-tab operator refresh checklist
  - refresh status strips on Watchlist, Fundamentals, Own history, Benchmarks,
    News/Events, Technical indicators, and Sources
  - local persisted last-successful refresh timestamps
  - source timestamp/source-cache details and warning/error surfaces where API
    payloads expose them
- Added `docs/operator-refresh-checklist.md`.
- Kept NewsWeb daily digest on demand, preserved missing-data behavior, added no
  recommendation logic, added no standalone multiple labels, and did not edit
  Oslo Screener repos.
- Verification passed for backend/frontend/script syntax, README API checks,
  restore drill, temporary backup-mirror copy, in-app browser refresh-status
  checks across the main tabs and RSI14 screener, browser console errors, and
  Safari launch.

## Completed Previous Sprint

- Added Public Access Foundation repo assets for the recommended single-host
  path: hosted environment template, systemd service template, Caddy reverse
  proxy template, daily backup cron example, and hosted verification script.
- Kept the app deployment shape to one Python instance bound to localhost behind
  HTTPS with Basic Auth enabled and persistent SQLite outside the git checkout.
- Confirmed actual hosted/public URL access, DNS/HTTPS provisioning,
  off-host/encrypted mirror setup, hosted restore drill, and another-device tab
  verification are blocked until real operator credentials/paths are supplied.
- Preserved all no-advice/no-standalone-verdict guardrails, kept NewsWeb
  automation out of scope, and did not edit the Oslo Screener repos.
- Verification passed for backend/frontend/script syntax, README API checks,
  restore drill, temporary backup-mirror copy, hosted-verification-script dry
  run against a temporary authenticated local instance, in-app browser tab
  checks, browser console errors, and Safari launch.

## Completed Earlier Sprint

- Clarified the go-live direction: public HTTPS address for use from other devices is now the next priority.
- Added `docs/go-live-readiness.md` with the public-access architecture, data-quality boundary, interactive refresh expectations, and sprint count.
- Estimated 2 sprints minimum and 3 sprints recommended from current state: Public Access Foundation, Data Refresh And Source-Quality Readiness, and Beta Release Hardening.
- Reframed "accurate, reliable, credible, and validated" as visible freshness/source/confidence/limitations plus manual/source-linked review paths, not guaranteed correctness from free/open data.

## Completed Earlier Sprint

- Added manual/source-linked primary company-report review tracking for quarterly statement periods.
- Added `quarterly_statement_reviews` storage and `/api/quarterly-statement-reviews` for reading/saving per-symbol, per-period review rows.
- Own History now shows primary-review counts, per-period review status, and a compact primary-review form inside quarterly statement detail.
- Added `docs/primary-report-verification.md` with review statuses, source requirements, API examples, and no-verdict guardrails.
- Added `scripts/drill_restore_database.sh` and optional `OSLO_APP_BACKUP_MIRROR_DIR` support for backup mirroring.
- Kept yfinance quarterly statement rows screening-grade by default; unreviewed periods remain not-primary-verified, missing rows stay missing, primary reviews do not backfill values, and no recommendation logic was added.
- Verification passed for backend/frontend/script syntax, README API checks, `/api/quarterly-statement-reviews?symbol=MOWI.OL`, non-mutating POST validation, restore drill, temporary backup-mirror copy, in-app browser navigation including Own History primary-review UI, browser console errors, and Safari launch.

## Completed Earlier Sprint

- Decided the practical sharing path without deploying externally: local/private remains default, Tailscale/LAN is only for a small trusted pilot, and any later external sharing should use a single EU VPS with the app bound to localhost behind an HTTPS reverse proxy.
- Added `scripts/backup_database.sh` and `scripts/restore_database.sh` for SQLite online backups, integrity checks, timestamped backup files, checksum files, and pre-restore safety backups.
- Added `backups/` to `.gitignore` and documented `OSLO_APP_BACKUP_DIR`.
- Expanded `docs/deployment-sharing.md` with backup cadence, retention target, restore workflow, hosted database path expectations, deployment target comparison, HTTPS/reverse-proxy expectations, and a production access-control checklist.
- Preserved quarterly statement screening-grade wording, explicit sector index/proxy curation, the current on-demand NewsWeb digest, `/api/technical-indicators`, the separate RSI14 screener tab, and no-recommendation behavior.
- Verification passed for script syntax, backend/frontend syntax, README API checks, backup creation/checksum validation, restore to a temporary database path, and Safari launch.

## Completed Prior Sprint

- Added environment-based runtime settings for bind host, port, SQLite database path, and optional Basic Auth.
- Kept default local behavior unchanged at `127.0.0.1:8765` with no auth prompt.
- Added a startup guard that refuses non-local unauthenticated binds unless an explicit override is set.
- Added `.env.example`, `docs/deployment-sharing.md`, and GitHub Actions CI for backend/frontend syntax checks.
- Preserved quarterly statement screening-grade wording, explicit sector index/proxy curation, the current on-demand NewsWeb digest, `/api/technical-indicators`, the separate RSI14 screener tab, and no-recommendation behavior.
- Verification passed for syntax, README API checks, optional Basic Auth on a temporary local port, non-local unauthenticated startup refusal, in-app browser navigation, and Safari launch.

## Completed Older Sprint

- Confirmed yfinance quarterly income statement, balance sheet, and cash-flow tables return dated quarter-end statement columns for Oslo examples including MOWI, NOD, and FRO.
- Added strict quarterly statement parsing for explicit yfinance row labels only; missing periods and fields stay missing, and current yfinance summary fields are not used as statement-history proxies.
- Added a Quarterly statement history section to Own history row details with period count, source path, statement currency when yfinance supplies `financialCurrency`, row coverage, confidence, timestamp, and limitations.
- Added quarterly statement coverage metadata to `/api/fundamentals` validation output.
- Preserved optional sector index/proxy curation as explicit peer rows only, kept the on-demand NewsWeb daily digest unchanged, preserved `/api/technical-indicators`, and added no recommendation logic.
- Verification passed for syntax, README API checks, focused MOWI quarterly payload with 6 dated periods through 2025-12-31 and EUR `financialCurrency`, in-app browser navigation across Watchlist/Fundamentals/Own history/Benchmarks/News/Events/Technical indicators/RSI14 screener, browser console errors, and Safari launch.

- Added a conservative on-demand 24-hour NewsWeb watchlist digest to `/api/event-monitoring`.
- Grouped digest rows by watchlist symbol and event category.
- Added heuristic duplicate/correction grouping for same client announcement IDs, corrections, repeated issuer messages, and same-day title fingerprints.
- Added per-symbol NewsWeb fetch status for fresh, stale, old, error, and stale-after-error cases.
- Kept source links, timestamps, freshness, confidence, limitations, missing-data wording, and no-advice wording visible in the digest and News/Events table.
- Preserved Watchlist, Fundamentals, Own history, Benchmarks, Technical indicators, `/api/technical-indicators`, and the separate RSI14 screener tab.
- Verification passed for syntax, README API checks, `/api/event-monitoring?refresh=1` returning an 8-row 24-hour digest across 5 watchlist symbols during live verification, in-app browser navigation, and Safari launch.

## Completed Historical Sprint

- Added explicit consensus/source row metadata for row type, review status, target currency, as-of date, source URL, method note, and limitation note.
- Kept Yahoo/yfinance target and rating fields labeled as provider-row data, not verified consensus.
- Expanded the Fundamentals consensus editor into grouped source, value, and quality sections.
- Added a source-row table below the editor so stored provider/manual rows are visible without crowding the scan table.
- Changed Watchlist/Fundamentals copy to source-row language and raw rating labels.
- Changed rating summaries so they count raw B/H/S provider rows but do not produce a majority or analyst-weighted BUY/HOLD/SELL recommendation.
- Preserved overlapping analyst-count caveats, missing-data behavior, peer statuses, Technical indicators, `/api/technical-indicators`, Own history, and the separate RSI14 screener tab.

## Completed Maintenance

- Confirmed the technical CSV was current while the embedded RSI14 dashboard page was still showing 28 April 2026 data.
- Root cause: `oslo-screener-dashboard` defaulted to an older setup branch, so scheduled workflow runs did not update the served `gh-pages` dashboard.
- Refreshed and published the dashboard to `gh-pages`; the final verified public page shows **Screener data: 05 May 2026**, **Source generated: 05 May 2026 19:59 UTC**, and **Generated: 05 May 2026 20:02 UTC**.
- Fast-forwarded the dashboard default branch to the fixed `main` workflow state so future scheduled runs should update the served Pages branch.
- Source-news fetches during generation logged Yahoo RSS rate limits and Oslo Bors parse failures; the dashboard keeps those limitations visible.

## Completed Reliability Pass

- Updated `oslo-screener` workflow reliability: concurrency, timeouts, `latest.csv` verification, safer bot push flow, optional dashboard dispatch trigger, and `.DS_Store` cleanup.
- Updated `oslo-screener-dashboard` workflow reliability: default branch set to `main`, later primary schedule plus backup schedule, concurrency, HTML verification, explicit `Pillow` dependency, and source freshness display.
- Published regenerated dashboard content to `gh-pages`.
- Verification passed for screener compile/tests, dashboard compile/generation, generated HTML checks, manual GitHub Actions dispatches for both workflows, GitHub branch state, web-app API checks, and Safari launch.

## Next Sprint Brief

Next priority: complete the host-side half of Hosted Public Access Completion.

Goal:

- Make the dashboard/application available from other devices through a controlled public HTTPS URL.
- Re-run the true-refresh checks against the hosted URL and confirm stale/error
  wording is visible when a hosted source is cached, rate-limited, failing, or
  missing.

Tasks:

- Provide or create the real domain/subdomain, DNS access, single-host target,
  SSH/deployment access, and mounted off-host/encrypted backup destination.
- Install the `deploy/` templates on the host with the Python app bound to
  localhost behind HTTPS and Basic Auth.
- Set persistent hosted `OSLO_APP_DB_PATH` and real
  `OSLO_APP_BACKUP_MIRROR_DIR`.
- Run hosted backup, mirror copy, restore drill, README API checks,
  `scripts/verify_public_deployment.sh`, and external-device tab verification.
- Run hosted refresh-button verification across all tabs.
- Keep optional sector index/proxy curation explicit and reviewed.
- Preserve no-advice/no-verdict language, missing-data discipline, Technical indicators, and the separate RSI14 screener tab.

## Verification Checklist For Next Chat

1. Start server.
2. Open Watchlist tab.
3. Confirm rows render and Watchlist remains scan-first.
4. Open Fundamentals and confirm the grouped scan table uses provider/source target wording and the consensus/source row editor/table renders.
5. Open Own History and confirm price-history context, local snapshot charts/rows, quarterly statement history details, and source/gate metadata render.
6. Open Technical indicators and confirm source date, coverage count, and dashboard alert tags render.
7. Open Benchmarks and confirm peer groups, sector components, minimum-data checks, and sector KPI input editor render without a repeated own-history block.
8. Open News/Events and confirm source-policy status, daily digest grouped by symbol/category, per-symbol NewsWeb fetch status, source links, watchlist rows, and manual editor render.
9. Open RSI14 screener and confirm the embedded dashboard is unchanged.
10. Confirm no cheap/expensive/fair/neutral valuation verdict labels exist.
11. Run README verification commands.
12. Run `scripts/open_in_safari.sh` and confirm Safari opens `http://127.0.0.1:8765`.
