# Links And Resources

## Project Links

- Repository: https://github.com/keresell-coder/oslo-market-workspace
- Existing Oslo Screener Dashboard: https://keresell-coder.github.io/oslo-screener-dashboard/
- Local app default: http://127.0.0.1:8765
- Local app alternate/debug: http://127.0.0.1:8768

## Main Local Files

- `README.md`
- `AGENTS.md`
- `docs/roadmap.md`
- `docs/project-handoff.md`
- `app/server.py`
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`
- `requirements.txt`

## Current API Endpoints

- `GET /api/health`
- `GET /api/tickers`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist`
- `GET /api/watchlist-overview`
- `GET /api/fundamentals`
- `GET /api/consensus`
- `POST /api/consensus`
- `GET /api/benchmarks`
- `GET /api/peer-groups`
- `GET /api/screener-alerts`
- `GET /api/screener-signals`
- `GET /api/events`
- `POST /api/events`
- `GET /api/sources`

## External Sources In Use

- Yahoo Finance via `yfinance`
- Published Oslo Screener Dashboard HTML
- NewsWeb ticker search links
- TradingView search links

## External Sources Considered But Not Automated

- TradingView analyst/target-price pages
- MarketScreener consensus pages
- NewsWeb/Euronext announcement feeds

These should only be automated if a reliable, permitted, and stable source path is confirmed. Until then, use manual/reviewed source entries.

