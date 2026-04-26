# Oslo Market Workspace MVP

Local MVP for a personal Oslo Bors workspace. It embeds the existing Oslo Screener Dashboard as one tab and adds editable watchlists plus a fundamentals screener backed by cached open/free data.

## Run Locally

```bash
python3 app/server.py
```

Then open:

```text
http://127.0.0.1:8765
```

On iPhone/Android, open the same URL in the browser and use "Add to Home Screen" once the app is reachable from the phone. Localhost only works on the machine running the app; phone access needs either same-network hosting or a deployed version.

## Current Data Sources

- Existing screener: embedded from `https://keresell-coder.github.io/oslo-screener-dashboard/`.
- Screener/watchlist alerts: parsed from the published Oslo Screener dashboard cards and matched to the editable watchlist.
- Fundamentals: `yfinance` where Yahoo Finance has coverage for `.OL` symbols.
- Benchmarks: manual peer-group seeds plus cached `yfinance` metrics for descriptive peer context.
- NewsWeb: MVP provides ticker-specific NewsWeb search links and classification structure; direct automated collection is intentionally conservative until we confirm a stable public endpoint/terms.

## Reliability Notes

Free market data is delayed, incomplete, rate-limited, and can change without notice. The app stores source labels and timestamps so values can be treated as screening inputs, not verified investment facts.

The Oslo Screener alert layer only links symbols from the published dashboard to the local watchlist. It does not verify that the underlying technical signal is correct.

The fundamentals tab intentionally does not label stocks cheap, expensive, or neutral yet. Valuation judgments should only be shown after peer, sector, and own-history benchmarks are implemented and visible.

The benchmark tab is descriptive. Peer groups are manually seeded and must be reviewed before relying on them. Own-history context starts from locally stored refresh snapshots and is not meaningful until enough observations accumulate.

Metrics such as P/NAV, sector-specific NAV, fleet values, reserves, and detailed consensus estimates usually require company reports, broker data, paid APIs, or curated manual inputs. The MVP leaves these fields visible as "n/a" rather than inventing values.

## Planned Repository

Target GitHub repository:

```text
keresell-coder/oslo-market-workspace
```

This repository is separate from the existing Oslo Screener project. The existing dashboard is embedded by URL and not edited here.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).
