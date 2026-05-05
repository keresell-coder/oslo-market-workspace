# Codex Project Instructions

## Project

This project is **Oslo Stock web-app**, backed by the repository `keresell-coder/oslo-market-workspace`.

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

It is a local-first Oslo Bors research workspace.

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

- `app/server.py`: Python standard-library HTTP server, SQLite storage, yfinance collection, compact price/own-history chart payloads, screener parsing, consensus/event APIs.
- `app/static/index.html`: single-page app shell.
- `app/static/app.js`: frontend data loading and rendering; Own History reuses `/api/fundamentals` rather than a separate backend endpoint.
- `app/static/styles.css`: UI styling.
- `app/data/oslo_workspace.sqlite3`: local runtime database, ignored by git.
- `docs/roadmap.md`: sprint plan.
- `docs/project-handoff.md`: continuation context for new Codex chats.
- `docs/links-and-resources.md`: important links and source notes.

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
- The RSI14 dashboard was refreshed to 05 May 2026 after its served `gh-pages` HTML lagged the current `latest.csv`; if it looks stale again, compare the CSV timestamp with the dashboard date and check `oslo-screener-dashboard` default branch plus `gh-pages` deployment.
- Oslo Screener reliability pass is complete: both screener repos default to `main`; the producer verifies `latest.csv` before publishing; the dashboard runs after the producer with a backup schedule and shows source-generation freshness.

## Next Sprint Priority

NewsWeb And Event Monitoring:

- keep watchlist-first filtering
- confirm reliable/permitted NewsWeb or Euronext source handling before automation
- add event categories and a daily digest only after source path is clear
- keep all output descriptive and non-advisory
