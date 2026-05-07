# Links And Resources

## Project Links

- Project name: Oslo Stock web-app
- Beta release target: Beta v0.1.0
- Local folder: `/Users/ke/Documents/Oslo Stock web-app`
- Repository: https://github.com/keresell-coder/oslo-market-workspace
- Published RSI14/Oslo Screener Dashboard: https://keresell-coder.github.io/oslo-screener-dashboard/
- RSI14 dashboard source repo: https://github.com/keresell-coder/oslo-screener-dashboard
- Oslo Screener source repo: https://github.com/keresell-coder/oslo-screener
- Published Oslo Screener technical CSV: https://keresell-coder.github.io/oslo-screener/latest.csv
- Raw GitHub fallback technical CSV: https://raw.githubusercontent.com/keresell-coder/oslo-screener/main/latest.csv
- NewsWeb official site: https://newsweb.oslobors.no/
- Euronext Oslo market page: https://www.euronext.com/en/markets/oslo
- Euronext Publication Services / EuroStockNews: https://www.euronext.com/en/corporate-services/oslo-bors-publication-service
- Local app default: http://127.0.0.1:8765
- Local app alternate/debug: http://127.0.0.1:8768
- Safari launcher: `scripts/open_in_safari.sh`
- SQLite backup script: `scripts/backup_database.sh`
- SQLite restore script: `scripts/restore_database.sh`
- SQLite restore drill script: `scripts/drill_restore_database.sh`
- Hosted/public verification script: `scripts/verify_public_deployment.sh`
- Sharing/deployment notes: `docs/deployment-sharing.md`
- Go-live readiness notes: `docs/go-live-readiness.md`
- Primary report verification notes: `docs/primary-report-verification.md`
- Operator refresh checklist: `docs/operator-refresh-checklist.md`
- Runtime config example: `.env.example`
- Hosted runtime config example: `deploy/oslo-stock.env.example`
- Hosted systemd service template: `deploy/oslo-stock.service`
- Hosted Caddy reverse-proxy template: `deploy/Caddyfile.example`
- Hosted backup cron template: `deploy/oslo-stock-backup.cron.example`

## Main Local Files

- `README.md`
- `AGENTS.md`
- `docs/roadmap.md`
- `docs/project-handoff.md`
- `docs/links-and-resources.md`
- `docs/go-live-readiness.md`
- `docs/operator-refresh-checklist.md`
- `scripts/open_in_safari.sh`
- `scripts/backup_database.sh`
- `scripts/restore_database.sh`
- `scripts/drill_restore_database.sh`
- `scripts/verify_public_deployment.sh`
- `deploy/oslo-stock.env.example`
- `deploy/oslo-stock.service`
- `deploy/Caddyfile.example`
- `deploy/oslo-stock-backup.cron.example`
- `.env.example`
- `.github/workflows/ci.yml`
- `app/server.py`
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`
- `requirements.txt`

## Codex Chats

- Current sprint branch: `codex/sharing-prep-follow-up`
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
- `GET /api/event-monitoring`
- `GET /api/quarterly-statement-reviews`
- `POST /api/quarterly-statement-reviews`
- `GET /api/sources`

## Runtime Configuration

- `OSLO_APP_HOST`: bind host, default `127.0.0.1`.
- `OSLO_APP_PORT`: bind port, default `8765`.
- `OSLO_APP_DB_PATH`: optional SQLite database path.
- `OSLO_APP_BACKUP_DIR`: optional backup directory for SQLite backup/restore scripts.
- `OSLO_APP_BACKUP_MIRROR_DIR`: optional backup mirror directory for backup files and checksums.
- `OSLO_APP_REQUIRE_AUTH`: set to `1` for Basic Auth.
- `OSLO_APP_AUTH_USERNAME` and `OSLO_APP_AUTH_PASSWORD`: Basic Auth credentials.
- `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE`: explicit override for non-local unauthenticated binds.

Non-local bind hosts are refused by default unless Basic Auth credentials are configured or the explicit unauthenticated override is set.

## Sharing / Deployment References

- SQLite online backup API: https://www.sqlite.org/backup.html
- Caddy automatic HTTPS: https://caddyserver.com/docs/automatic-https
- Caddy reverse proxy directive: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- Tailscale Serve: https://tailscale.com/docs/features/tailscale-serve
- Hetzner cloud pricing docs: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Render persistent disks: https://render.com/docs/disks
- Fly.io volumes: https://fly.io/docs/volumes/

Current decision as of 06 May 2026: keep local/private use as default; Tailscale/LAN is suitable only for a small trusted pilot; any external sharing should use one small EU VPS or equivalent single-host target with the app bound to localhost behind HTTPS reverse proxy, a persistent SQLite path, and off-host backups. Repo templates now exist for that single-host path, but no external deployment has been performed because no real domain/subdomain, DNS access, host credential, or mounted off-host backup destination is present in this workspace.

## External Sources In Use

- Yahoo Finance via `yfinance`
- Yahoo/yfinance target and rating-label fields are stored as provider-row consensus/source rows, not verified consensus.
- Yahoo/yfinance 1-year daily closes for sampled compact price charts, with observation count, freshness, confidence, and limitations shown in the app
- Yahoo/yfinance quarterly income statement, balance sheet, and cash-flow tables for true quarterly statement history when dated quarter-end columns are returned; missing statement rows stay missing and current summary fields are not used as proxies
- Manual/source-linked primary company-report review rows for quarterly statement periods, stored separately from yfinance values; reviews do not backfill missing statement data
- Published RSI14/Oslo Screener Dashboard HTML
- Published Oslo Screener `latest.csv` technical indicator output
- Manual/source-linked sector KPI inputs, reviewed locally before values appear in benchmark output
- Manual consensus/source rows for target/rating references when source URL, as-of date, method, and limitations reduce ambiguity from free provider data
- Local `fundamentals_snapshots` for own-multiple trend charts, gated by minimum observation count
- NewsWeb ticker search links, on-demand NewsWeb rows, on-demand 24-hour daily digest rows, and manual/source-reviewed significant-event rows
- TradingView search links

## NewsWeb / Euronext Event Source Notes

- Source path checked on 06 May 2026.
- Euronext Oslo page identifies NewsWeb as the place where listed-company news on Euronext Oslo Børs marketplaces is displayed and says it is updated immediately, 24/7.
- NewsWeb public web app exposes JSON calls used by its JavaScript frontend. Its `urls.json` points to `https://api3.oslo.oslobors.no`, and ticker queries use `/v1/newsreader/customQuery`.
- Euronext Publication Services / EuroStockNews describes issuer publication services and API/web-module capabilities, but that appears to be an issuer/corporate-services path rather than a confirmed public research ingestion API.
- App behavior: News/Events tab and `/api/event-monitoring` fetch NewsWeb rows on demand with a 15-minute cache, merge them with manual/source-reviewed rows, and expose a 24-hour watchlist digest grouped by symbol and event category.
- Digest behavior: duplicate/correction handling uses same client announcement IDs when present plus same-day title fingerprints for repeated issuer messages and same-title announcements. It is heuristic and keeps dedupe counts visible.
- Fetch status behavior: each watchlist symbol carries fresh, stale, old, error, or stale-after-error metadata with timestamps, confidence, limitations, and direct NewsWeb links.
- Event categories in use: earnings, contract/order, financing/private placement, dividend, insider, M&A, guidance/profit warning, corporate action.

## RSI14 Dashboard Refresh Notes

- On 05 May 2026, the published Oslo Screener `latest.csv` was current but the separate dashboard HTML still showed 28 April 2026 data.
- Cause: the `oslo-screener-dashboard` default branch was an older setup branch, and the scheduled workflow path was not updating the `gh-pages` branch served by GitHub Pages.
- Fix applied: regenerated the dashboard from current CSV data, pushed the fixed dashboard branch state, and published the refreshed `gh-pages` site.
- Current public dashboard after the final reliability verification: `Screener data: 05 May 2026`, `Source generated: 05 May 2026 19:59 UTC`, `Generated: 05 May 2026 20:02 UTC`, source labels BUY 1, SELL 4, BUY-watch 8, SELL-watch 11, 111 screened rows.
- Generation source limitations to remember: Yahoo RSS returned rate-limit errors and Oslo Bors news parsing failed for some symbols, but the screener data itself refreshed from the current CSV.

## Oslo Screener Reliability Notes

- `oslo-screener` default branch: `main`.
- `oslo-screener-dashboard` default branch: `main`.
- `oslo-screener-dashboard` published branch: `gh-pages`.
- `oslo-screener` daily workflow verifies `latest.csv` metadata, required columns, and non-empty rows before publishing.
- `oslo-screener-dashboard` daily workflow runs at 09:30 UTC and 12:30 UTC weekdays, verifies generated HTML, and displays `latest.csv` source-generation freshness from `generated_at`.
- Optional cross-repo immediate refresh path: configure `DASHBOARD_WORKFLOW_TOKEN` in `oslo-screener` repo secrets so the daily screener deploy can dispatch `oslo-screener-dashboard` after the CSV publishes.

## External Sources Considered But Not Automated

- TradingView analyst/target-price pages
- MarketScreener consensus pages
- Primary company report parsing for quarterly statement verification
- Scheduled NewsWeb/Euronext announcement automation
The current digest is on-demand. Any scheduled automation should reuse the same conservative source path, keep deduplication/source links/error/freshness reporting visible, and preserve overlapping analyst-count caveats for consensus data.
