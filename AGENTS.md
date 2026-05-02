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
- `app/static/app.js`: frontend data loading and rendering.
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

Compact Charts And Trends is complete:

- price trend charts use sampled Yahoo/yfinance 1-year daily closes and the existing 120-observation gate
- own-multiple trend charts use local `fundamentals_snapshots` and the existing 5-snapshot gate
- Watchlist trend visuals stay behind expandable Trend preview rows
- Fundamentals and Benchmarks show chart context only as descriptive, source-labeled screening data
- missing chart inputs stay gated/missing

## Next Sprint Priority

Consensus Quality:

- improve consensus table/editor if needed
- add manual override fields for unreliable free-API values
- consider multiple consensus providers only if reliable and permitted
- preserve caveats about overlapping analyst counts across providers
- keep all output descriptive and non-advisory
