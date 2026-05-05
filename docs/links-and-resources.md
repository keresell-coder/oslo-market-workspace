# Links And Resources

## Project Links

- Project name: Oslo Stock web-app
- Local folder: `/Users/ke/Documents/Oslo Stock web-app`
- Repository: https://github.com/keresell-coder/oslo-market-workspace
- Published RSI14/Oslo Screener Dashboard: https://keresell-coder.github.io/oslo-screener-dashboard/
- Oslo Screener source repo: https://github.com/keresell-coder/oslo-screener
- Published Oslo Screener technical CSV: https://keresell-coder.github.io/oslo-screener/latest.csv
- Raw GitHub fallback technical CSV: https://raw.githubusercontent.com/keresell-coder/oslo-screener/main/latest.csv
- Local app default: http://127.0.0.1:8765
- Local app alternate/debug: http://127.0.0.1:8768
- Safari launcher: `scripts/open_in_safari.sh`

## Main Local Files

- `README.md`
- `AGENTS.md`
- `docs/roadmap.md`
- `docs/project-handoff.md`
- `docs/links-and-resources.md`
- `scripts/open_in_safari.sh`
- `app/server.py`
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`
- `requirements.txt`

## Codex Chats

- Current sprint branch: `codex/consensus-quality`
- Related chat requested for this project: Add GitHub account to Codex.
- The related chat exists locally and was created against the same original generated workspace path. No supported Codex project/chat membership tool was exposed in this session, so move it manually in the Codex UI if it is not grouped under Oslo Stock web-app after the folder rename.

## Current API Endpoints

- `GET /api/health`
- `GET /api/tickers`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist`
- `GET /api/watchlist-overview`
- `GET /api/fundamentals`
  - also backs the dedicated Own History tab
- `GET /api/consensus`
  - returns provider/manual source rows with row type, review status, as-of date, target currency, source URL, method note, limitation note, freshness, and overlap caveats
- `POST /api/consensus`
- `GET /api/benchmarks`
- `POST /api/sector-kpi-inputs`
- `GET /api/peer-groups`
- `POST /api/peer-groups`
- `POST /api/peer-groups/draft`
- `GET /api/screener-alerts`
- `GET /api/screener-signals`
- `GET /api/technical-indicators`
- `GET /api/events`
- `POST /api/events`
- `GET /api/sources`

## External Sources In Use

- Yahoo Finance via `yfinance`
- Yahoo/yfinance target and rating-label fields are stored as provider-row consensus/source rows, not verified consensus.
- Yahoo/yfinance 1-year daily closes for sampled compact price charts, with observation count, freshness, confidence, and limitations shown in the app
- Published RSI14/Oslo Screener Dashboard HTML
- Published Oslo Screener `latest.csv` technical indicator output
- Manual/source-linked sector KPI inputs, reviewed locally before values appear in benchmark output
- Manual consensus/source rows for target/rating references when source URL, as-of date, method, and limitations reduce ambiguity from free provider data
- Local `fundamentals_snapshots` for own-multiple trend charts, gated by minimum observation count
- NewsWeb ticker search links
- TradingView search links

## External Sources Considered But Not Automated

- TradingView analyst/target-price pages
- MarketScreener consensus pages
- NewsWeb/Euronext announcement feeds
These should only be automated if a reliable, permitted, and stable source path is confirmed. Until then, use manual/reviewed source entries and preserve overlapping analyst-count caveats.
