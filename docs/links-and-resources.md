# Links And Resources

## Project

- Repository: https://github.com/keresell-coder/oslo-market-workspace
- Public Pages app: https://keresell-coder.github.io/oslo-market-workspace/
- Local app: http://127.0.0.1:8765
- Alternate local/debug port often used: http://127.0.0.1:8768
- Local folder: `/Users/ke/Documents/Oslo Stock web-app`
- Release target: Beta v0.1.0

## Related Repos And Public Data

- Oslo Screener source repo: https://github.com/keresell-coder/oslo-screener
- Oslo Screener dashboard repo:
  https://github.com/keresell-coder/oslo-screener-dashboard
- Published RSI14 dashboard:
  https://keresell-coder.github.io/oslo-screener-dashboard/
- Published technical CSV:
  https://keresell-coder.github.io/oslo-screener/latest.csv
- Raw technical CSV fallback:
  https://raw.githubusercontent.com/keresell-coder/oslo-screener/main/latest.csv

Screener artifacts used for coverage checks: `latest.csv`, `report_*.csv`,
`summaries/latest.md`, `tickers.txt`, `valid_tickers.txt`,
`invalid_tickers.csv`, and `raw_tickers.txt`.

## Market And News Sources

- NewsWeb: https://newsweb.oslobors.no/
- Euronext Oslo market page: https://www.euronext.com/en/markets/oslo
- Euronext Publication Services / EuroStockNews:
  https://www.euronext.com/en/corporate-services/oslo-bors-publication-service
- Yahoo Finance via `yfinance`
- TradingView search links

NewsWeb source notes:

- Official Euronext Oslo pages identify NewsWeb as the listed-company news site.
- The NewsWeb frontend uses JSON calls under `https://api3.oslo.oslobors.no`.
- The app uses NewsWeb rows as screening-grade source rows with timestamps,
  links, duplicate/correction grouping, and per-symbol fetch status.

## Main Local Files

- `README.md`
- `AGENTS.md`
- `docs/roadmap.md`
- `docs/project-handoff.md`
- `docs/static-github-pages-remake.md`
- `docs/watchlist-edit-workflow.md`
- `docs/peer-group-curation.md`
- `docs/operator-refresh-checklist.md`
- `docs/primary-report-verification.md`
- `docs/deployment-sharing.md`
- `docs/hosted-public-access-runbook.md`
- `scripts/build_static_site_data.py`
- `scripts/validate_static_inputs.py`
- `scripts/open_in_safari.sh`
- `scripts/backup_database.sh`
- `scripts/restore_database.sh`
- `scripts/drill_restore_database.sh`
- `scripts/verify_public_deployment.sh`
- `.github/workflows/ci.yml`
- `.github/workflows/static-data.yml`
- `data/*.yml`
- `docs/data/manifest.json`
- `app/server.py`
- `app/static/`
- `docs/`

## Current Local APIs

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
- `POST /api/peer-groups`
- `POST /api/peer-groups/draft`
- `POST /api/sector-kpi-inputs`
- `GET /api/screener-alerts`
- `GET /api/screener-signals`
- `GET /api/technical-indicators`
- `GET /api/events`
- `POST /api/events`
- `GET /api/event-monitoring`
- `GET /api/quarterly-statement-reviews`
- `POST /api/quarterly-statement-reviews`
- `GET /api/sources`

Refresh-capable endpoints include `refresh=1` where implemented, notably
Watchlist overview, Fundamentals, Technical indicators, News/Events, and
Benchmarks-related hosted verification paths.

## Runtime Configuration

- `OSLO_APP_HOST`: bind host, default `127.0.0.1`.
- `OSLO_APP_PORT`: bind port, default `8765`.
- `OSLO_APP_DB_PATH`: optional SQLite database path.
- `OSLO_APP_BACKUP_DIR`: backup directory.
- `OSLO_APP_BACKUP_MIRROR_DIR`: optional backup mirror.
- `OSLO_APP_REQUIRE_AUTH`: set to `1` for Basic Auth.
- `OSLO_APP_AUTH_USERNAME` / `OSLO_APP_AUTH_PASSWORD`: Basic Auth credentials.
- `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE`: explicit remote unauthenticated bind
  override.

Non-local unauthenticated binds are refused by default.

## Static Pages References

- Static plan: `docs/static-github-pages-remake.md`
- Watchlist edit flow: `docs/watchlist-edit-workflow.md`
- Static builder: `scripts/build_static_site_data.py`
- Static input validator: `scripts/validate_static_inputs.py`
- Static workflow: `.github/workflows/static-data.yml`
- Static entrypoint: `docs/index.html`
- Static manifest: `docs/data/manifest.json`
- GitHub Pages docs:
  https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- GitHub Actions workflow syntax:
  https://docs.github.com/actions/learn-github-actions/workflow-syntax-for-github-actions
- GitHub scheduled workflow behavior:
  https://docs.github.com/actions/reference/events-that-trigger-workflows

Current static status: Pages is live, static data is generated from YAML, and
the public manifest/Watchlist show 15 rows including `BRG.OL` and `NORBT.OL`.
Static Beta Follow-Up is complete: public checks passed and the operator
verified the Pages app from an iPad on 19 May 2026. Low-risk watchlist and
peer-group editing now uses `scripts/validate_static_inputs.py` plus the
YAML/PR/static data workflow. Fundamental frameworks stay deferred while the
external `oslo-quant` framework screener receives final tweaks.

## Legacy Hosted Backend References

- Sharing/deployment notes: `docs/deployment-sharing.md`
- Hosted public access runbook: `docs/hosted-public-access-runbook.md`
- Hosted config template: `deploy/oslo-stock.env.example`
- Systemd template: `deploy/oslo-stock.service`
- Caddy template: `deploy/Caddyfile.example`
- Backup cron template: `deploy/oslo-stock-backup.cron.example`
- SQLite backup API: https://www.sqlite.org/backup.html
- Caddy automatic HTTPS: https://caddyserver.com/docs/automatic-https
- Caddy reverse proxy: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- Tailscale Serve: https://tailscale.com/docs/features/tailscale-serve
- Render disks: https://render.com/docs/disks
- Fly.io volumes: https://fly.io/docs/volumes

The hosted backend path is paused unless explicitly revived.

## Source Notes To Preserve

- Yahoo/yfinance data is screening-grade. Provider target/rating labels are
  provider/source rows, not verified consensus.
- Displayed EV/EBITDA is source-gated from explicit enterprise value, TTM
  EBITDA, and FX inputs where usable; raw provider EV/EBITDA is audit data.
- Quarterly statement history uses dated yfinance quarterly tables only.
- Manual/source-linked primary-report reviews do not backfill missing statement
  rows.
- Oslo Screener dashboard and CSV labels are external source labels.
- Current static technical data covers 14 watchlist rows; `NORBT.OL` is the
  explicit missing-from-latest-CSV row.
