# Codex Project Instructions

## Project

This repository is `keresell-coder/oslo-market-workspace`, a local-first Oslo Bors research workspace.

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

- `app/server.py`: Python standard-library HTTP server, SQLite storage, yfinance collection, screener parsing, consensus/event APIs.
- `app/static/index.html`: single-page app shell.
- `app/static/app.js`: frontend data loading and rendering.
- `app/static/styles.css`: UI styling.
- `app/data/oslo_workspace.sqlite3`: local runtime database, ignored by git.
- `docs/roadmap.md`: sprint plan.
- `docs/project-handoff.md`: continuation context for new Codex chats.
- `docs/links-and-resources.md`: important links and source notes.

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
```

Use the in-app browser for visual verification when possible.

## Next Sprint Priority

Tweak the watchlist consensus column. The watchlist result must be based on the other tabs/source data:

- consensus target price should link directly to the fundamentals target field
- target upside should be visible on the watchlist
- BUY/HOLD/SELL should clearly show source quality and not imply verified weighted consensus unless the data supports it
- clicking/using the consensus cell should make it easy to inspect the underlying fundamentals/consensus sources

