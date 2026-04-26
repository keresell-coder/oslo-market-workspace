# Oslo Market Workspace

Local MVP for a personal Oslo Bors research workspace. It combines an editable watchlist, the existing Oslo Screener dashboard, screening alerts, fundamentals data, and early descriptive peer benchmarks.

The app is intentionally conservative: it shows source data and benchmark context, but does not label stocks cheap, expensive, or neutral.

## Run Locally

```bash
python3 app/server.py
```

Then open:

```text
http://127.0.0.1:8765
```

If an old local process is stuck on `8765`, run the server on another port from Python or restart the terminal/session. During development this has also been verified on `http://127.0.0.1:8768`.

On iPhone/Android, open the app in the browser and use "Add to Home Screen" once the app is reachable from the phone. `localhost` only works on the machine running the app; phone access needs same-network hosting or a later deployed version.

## What Works In The MVP

- **Watchlist**
  - SQLite-backed editable watchlist.
  - Initial test watchlist is seeded from the first user list.
  - Add/remove symbols from the app.
  - Watchlist rendering is independent from screener-alert fetching, so a failed alert refresh should not blank the watchlist.

- **Oslo Screener tab**
  - Embeds the existing published Oslo Screener Dashboard:
    `https://keresell-coder.github.io/oslo-screener-dashboard/`
  - This project does not edit the existing screener repository.

- **Watchlist/screener alerts**
  - Parses ticker/signal cards from the published Oslo Screener dashboard.
  - Shows an alert when a watchlist symbol appears in the current screener output.
  - Links each watchlist row back to Yahoo, NewsWeb, and the Oslo Screener.

- **Fundamentals tab**
  - Uses cached `yfinance`/Yahoo Finance data where available.
  - Shows price, market cap, P/E, P/B, EV/EBITDA, EPS, dividend yield, target price, and target upside where available.
  - Labels target price as Yahoo/yfinance source data only.
  - Does not treat Yahoo recommendation fields as verified BUY/HOLD/SELL weighting.
  - Shows consensus quality as low/single-source unless additional reviewed sources are added.

- **Benchmarks tab**
  - Adds a descriptive peer benchmark layer.
  - Uses manually seeded peer groups for selected watchlist stocks.
  - Shows company value, peer median, peer min/max, and relative position for selected metrics.
  - Starts collecting own-history snapshots when fundamentals are refreshed.
  - Shows sector context as "not configured" until a proper sector/index source is added.

- **Source quality tab**
  - Summarizes what each source is used for and its limitations.

## Current Data Sources

- Existing screener: GitHub Pages published Oslo Screener dashboard.
- Screener/watchlist alerts: parsed from the published dashboard cards.
- Fundamentals: Yahoo Finance through `yfinance`.
- Consensus/target provenance: local `consensus_sources` table, currently populated from Yahoo/yfinance and ready for manual/reviewed source entries.
- Benchmarks: manual peer-group seeds plus cached `yfinance` metrics.
- NewsWeb: ticker-specific search links only for now.
- TradingView: search links only for now.

## Reliability Rules

- Free market data is delayed, incomplete, rate-limited, and can change without notice.
- The app treats values as screening inputs, not verified investment facts.
- No cheap/expensive/neutral flagging is allowed from standalone multiples.
- Any future valuation score must show:
  - peer group
  - sector benchmark
  - own-history range
  - source timestamp
  - confidence level
  - exact criteria

## Known Limitations

- Peer groups are manually seeded and not yet reviewed.
- Sector index benchmarking is not implemented.
- Own-history benchmarking needs more refresh snapshots before it is useful.
- Yahoo/yfinance target prices are not enough for verified analyst consensus.
- Sprint 1 consensus infrastructure exists, but multi-source collection is not automated yet.
- P/NAV, NAV discount/premium, fleet values, reserves, EBIT/kg, backlog, ROE, CET1, LTV, WAULT, and similar sector metrics require reports, curated manual inputs, or better data sources.
- The current app is local-first. Sharing with friends needs a hosting/deployment step.

## Repository

GitHub:

```text
keresell-coder/oslo-market-workspace
```

This repository is separate from the existing Oslo Screener project.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).
