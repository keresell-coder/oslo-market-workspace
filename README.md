# Oslo Stock web-app

Local-first Oslo Bors research workspace for a personal watchlist, later shareable with friends/investment-club style users. The goal is to keep the most relevant screening data and synthesis in one app: screener signals, source-labeled fundamentals, peer context, consensus data, and significant updates.

The app is intentionally conservative. It must not produce buy/sell investment advice, and it must not label stocks cheap, expensive, or neutral from standalone multiples. Valuation context must be relative to peers, sector, own history, source quality, and missing data.

## Run

```bash
python3 app/server.py
```

Open:

```text
http://127.0.0.1:8765
```

If the port is busy, stop the stale Python process or use a temporary local port. During development `8768` has often been used.

Repository: `keresell-coder/oslo-market-workspace`

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

## Current App

- **Start**: first page, with short intent text, metric/source summary, current limitations, and a not-investment-advice disclaimer.
- **Watchlist**: main synthesis table. Current columns: company, last price, screener, fundamentals highlight, peer context, consensus target range, consensus rating, updates, and actions.
- **Fundamentals**: cached Yahoo/yfinance fields, watchlist or full ticker-database universe, and manual consensus source editor.
- **Benchmarks**: descriptive peer/own-history context with editable peer groups, curation status, role labels, and peer notes. Initial watchlist peer groups have been researched and marked reviewed, not trusted. New symbols can create backend-assisted draft peer groups from local/yfinance sector metadata.
- **Oslo Screener**: embeds/parses the published dashboard only. Do not edit the existing Oslo Screener repository unless explicitly requested.
- **Sources**: source quality and limitations.

## Data And Wording Rules

- Free data is screening-grade only: delayed, incomplete, rate-limited, and sometimes wrong.
- Show source, timestamp/freshness, confidence, and missing data clearly.
- Yahoo/yfinance target and recommendation data is one provider row by default, not verified consensus.
- “Reported analyst refs” are provider-reported analyst counts; they may overlap across providers and are not deduplicated.
- Peer group statuses are local curation markers only: draft, reviewed, or trusted. They do not create a valuation verdict.
- Reviewed peer groups still depend on source quality, sector KPIs, and missing-data context.
- Future consensus work should combine multiple providers carefully and preserve overlap/deduplication caveats.
- NewsWeb automation is not implemented; current use is ticker search links and manual event entries.

## Verification

Before finishing code changes, run:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
```

Use the in-app browser for visual checks when UI changes.

## Current Peer Curation State

- Peer groups can be edited in the Benchmarks tab.
- If a symbol already belongs to a peer group, including as a peer rather than the original focus company, the app reuses that group.
- If a symbol has no peer group, the Benchmarks tab can create a `draft` group with the symbol as focus and screening-grade candidate peers from local/yfinance sector metadata.
- Group-level fields: name, description, status, and curation note.
- Peer-level fields: symbol, role, market, and note.
- Supported role labels: focus company, Oslo peer, Nordic peer, European peer, international peer, and sector index/proxy.
- Initial groups for NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK are marked `reviewed`.
- Tankers and offshore energy were split into tighter groups: crude tankers for FRO, product tankers for HAFNI, subsea/offshore services for DOFG, and offshore drilling rigs for ODL.
- Backend-assisted draft groups are not reviewed research. They must be checked for business fit, geography, segment mix, scale, source quality, and missing sector KPIs before promotion.
- See `docs/peer-group-curation.md` for the researched peer rationale and source notes.

## Continue In A New Chat

Load only:

- `README.md`
- `docs/roadmap.md`

Recommended prompt:

```text
Please read README.md and docs/roadmap.md, then continue with the next sprint.
```
