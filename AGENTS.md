# Codex Project Instructions

## Project

This project is **Oslo Stock web-app**, backed by the repository `keresell-coder/oslo-market-workspace`.

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

It is a local-first Oslo Bors research workspace.

Beta release target:

```text
Beta v0.1.0
```

Remaining beta-release sprints:

```text
1. Hosted Public Access Completion
2. Beta Release Hardening
```

Primary app:

```bash
python3 app/server.py
```

Default URL:

```text
http://127.0.0.1:8765
```

If a stale local server holds the port, stop the old Python process or run a temporary server on another local port. During development, `8768` has often been used.

## Core Principles

- Do not produce buy/sell investment advice.
- Do not label stocks cheap, expensive, or neutral from standalone multiples.
- Valuation context must be relative to peers, sector, and own history.
- Free data is screening-grade only. Show source, timestamp, confidence, and missing data clearly.
- Do not edit the existing Oslo Screener repository unless the user explicitly asks. This app embeds and parses the published dashboard only.

## Current Architecture

- `app/server.py`: Python standard-library HTTP server, environment-based runtime config, optional Basic Auth, SQLite storage, yfinance collection, compact price/own-history chart payloads, strict yfinance quarterly statement parsing, screener parsing, consensus/event APIs, and watchlist-first event monitoring/daily digest metadata.
- `app/static/index.html`: single-page app shell.
- `app/static/app.js`: frontend data loading and rendering; Own History reuses `/api/fundamentals` rather than a separate backend endpoint.
- `app/static/styles.css`: UI styling.
- `app/data/oslo_workspace.sqlite3`: local runtime database, ignored by git.
- `docs/roadmap.md`: sprint plan.
- `docs/project-handoff.md`: continuation context for new Codex chats.
- `docs/links-and-resources.md`: important links and source notes.
- `docs/deployment-sharing.md`: sharing-prep runtime settings, authentication guardrails, database backup/restore workflow, deployment target comparison, HTTPS/reverse-proxy expectations, and production access-control checklist.
- `docs/go-live-readiness.md`: public MVP readiness plan, sprint count, public-address architecture, and data-quality boundary.
- `docs/operator-refresh-checklist.md`: beta refresh/review order and source-quality checks before sharing a view.
- `scripts/backup_database.sh`: SQLite online backup utility with integrity check and checksum output.
- `scripts/restore_database.sh`: SQLite restore utility with backup verification and pre-restore safety backup.
- `scripts/drill_restore_database.sh`: non-destructive restore drill utility that restores a fresh backup to a scratch database.
- `scripts/verify_public_deployment.sh`: hosted/public HTTPS, Basic Auth, health, and README API smoke-test utility.
- `deploy/`: hosted single-instance environment, systemd, Caddy, and backup cron templates for the recommended public-access path.
- `docs/primary-report-verification.md`: manual/source-linked review workflow for quarterly statement periods.
- `.github/workflows/ci.yml`: syntax checks for server and frontend.

## Documentation Discipline

After each completed task, update the relevant project documents so they reflect:

- what changed
- what was verified
- what remains planned next

At minimum, consider `README.md`, `docs/roadmap.md`, `docs/project-handoff.md`, and `docs/links-and-resources.md`.

## Verification Before Finishing Work

Run:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
```

If the local server is running, also check:

```bash
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/event-monitoring" | python3 -m json.tool
```

Use the in-app browser for visual verification when possible.

After every sprint or user-visible update, run:

```bash
scripts/open_in_safari.sh
```

This should leave the app available in Safari at `http://127.0.0.1:8765` unless the user explicitly asks to stop the local server.

## Current State Notes

Consensus Quality is complete:

- Yahoo/yfinance target and rating fields are labeled as provider-row data, not verified consensus
- consensus/source rows have row type, review status, target currency, as-of date, source URL, method note, and limitation note fields
- Fundamentals has a grouped consensus/source row editor and a stored source-row table
- Watchlist and Fundamentals use provider/source row wording and raw rating labels
- rating summaries count raw B/H/S provider rows but do not create a majority or analyst-weighted BUY/HOLD/SELL recommendation
- reported analyst refs may overlap across providers and are not deduplicated
- Own History remains a separate tab between Fundamentals and Technical indicators
- Technical indicators and `/api/technical-indicators` remain separate from the RSI14 screener dashboard tab
- News/Events tab and `/api/event-monitoring` use on-demand NewsWeb rows from the official frontend's `api3.oslo.oslobors.no` endpoint plus manual/source-reviewed rows
- NewsWeb Daily Digest is complete as an on-demand 24-hour watchlist digest grouped by symbol/category with per-symbol fetch status and heuristic duplicate/correction grouping
- Own History includes true quarterly statement history from yfinance quarterly income statement, balance sheet, and cash-flow tables when dated quarter-end rows are returned; missing statement rows stay missing and current summary fields are not used as proxies
- Event categories are earnings, contract/order, financing/private placement, dividend, insider, M&A, guidance/profit warning, and corporate action
- The RSI14 dashboard was refreshed to 05 May 2026 after its served `gh-pages` HTML lagged the current `latest.csv`; if it looks stale again, compare the CSV timestamp with the dashboard date and check `oslo-screener-dashboard` default branch plus `gh-pages` deployment.
- Oslo Screener reliability pass is complete: both screener repos default to `main`; the producer verifies `latest.csv` before publishing; the dashboard runs after the producer with a backup schedule and shows source-generation freshness.
- Sharing prep has environment-based host/port/database settings, optional Basic Auth, SQLite backup/restore/drill scripts, optional backup mirroring, hosted service/reverse-proxy templates, deployment target comparison, HTTPS/reverse-proxy expectations, a hosted verification script, and a production access-control checklist; default local use is unchanged, non-local unauthenticated binds are refused unless explicitly overridden, and no external deployment has been performed.
- Go-live direction: controlled public MVP at a public HTTPS address, behind authentication, on one hosted app instance with persistent SQLite and off-host backups. Estimated from current state: 2 sprints minimum, 3 sprints recommended.
- Quarterly statement primary-report review tracking is available through `/api/quarterly-statement-reviews` and Own History; unreviewed periods remain screening-grade yfinance rows and missing fields stay missing.
- Data Refresh And Source-Quality Readiness has visible refresh status strips on Watchlist, Fundamentals, Own history, Benchmarks, News/Events, Technical indicators, and Sources, plus a Start-tab/operator checklist; NewsWeb digest remains on demand.

## Next Sprint Priority

Hosted Public Access Completion:

- provide or create real domain/subdomain, DNS access, single-host target, SSH/deployment access, and mounted off-host/encrypted backup destination
- install the `deploy/` templates on the host with the Python app bound to localhost behind HTTPS reverse proxy
- configure Basic Auth or stronger upstream access control
- set persistent hosted `OSLO_APP_DB_PATH` and real `OSLO_APP_BACKUP_MIRROR_DIR`
- run hosted backup, mirror copy, restore drill, README API checks, `scripts/verify_public_deployment.sh`, and external-device tab verification
- verify and fix all refresh buttons so refresh actions perform true upstream/source refreshes where supported, rather than only reprocessing old cached data
- run `docs/operator-refresh-checklist.md` against the hosted instance before sharing a beta view
- keep optional sector index/proxy curation explicit and reviewed
- keep all output descriptive and non-advisory
