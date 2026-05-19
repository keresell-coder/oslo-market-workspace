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
- Public Oslo Screener input/report artifacts used for coverage reconciliation:
  `tickers.txt`, `valid_tickers.txt`, `invalid_tickers.csv`, `raw_tickers.txt`,
  dated `report_*.csv` files, and `summaries/latest.md` in
  https://github.com/keresell-coder/oslo-screener
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
- Hosted public access runbook: `docs/hosted-public-access-runbook.md`
- Static GitHub Pages remake plan: `docs/static-github-pages-remake.md`
- Static data builder: `scripts/build_static_site_data.py`
- Static GitHub Pages workflow: `.github/workflows/static-data.yml`
- Static Pages entrypoint: `docs/index.html`
- Static generated-data manifest: `docs/data/manifest.json`
- Primary report verification notes: `docs/primary-report-verification.md`
- Operator refresh checklist: `docs/operator-refresh-checklist.md`
- Watchlist edit workflow: `docs/watchlist-edit-workflow.md`
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
- `docs/hosted-public-access-runbook.md`
- `docs/static-github-pages-remake.md`
- `docs/operator-refresh-checklist.md`
- `docs/watchlist-edit-workflow.md`
- `scripts/open_in_safari.sh`
- `scripts/backup_database.sh`
- `scripts/restore_database.sh`
- `scripts/drill_restore_database.sh`
- `scripts/verify_public_deployment.sh`
- `scripts/build_static_site_data.py`
- `deploy/oslo-stock.env.example`
- `deploy/oslo-stock.service`
- `deploy/Caddyfile.example`
- `deploy/oslo-stock-backup.cron.example`
- `.env.example`
- `.github/workflows/ci.yml`
- `.github/workflows/static-data.yml`
- `data/watchlist.yml`
- `data/manual_consensus.yml`
- `data/peer_groups.yml`
- `data/sector_kpis.yml`
- `data/manual_events.yml`
- `data/quarterly_statement_reviews.yml`
- `docs/index.html`
- `docs/data/manifest.json`
- `app/server.py`
- `app/static/index.html`
- `app/static/app.js`
- `app/static/styles.css`
- `requirements.txt`

## Codex Chats

- Current sprint branch: `codex/hosted-public-access-completion`
- Related chat requested for this project: Add GitHub account to Codex.
- The related chat exists locally and was created against the same original generated workspace path. No supported Codex project/chat membership tool was exposed in this session, so move it manually in the Codex UI if it is not grouped under Oslo Stock web-app after the folder rename.

## Current API Endpoints

- `GET /api/health`
- `GET /api/tickers`
- `GET /api/watchlist`
- `POST /api/watchlist`
- `DELETE /api/watchlist`
- `GET /api/watchlist-overview`
  - accepts `refresh=1` to refresh the upstream/source paths used by the
    Watchlist synthesis view: yfinance fundamentals, RSI14 dashboard parsing,
    Oslo Screener `latest.csv`, and on-demand NewsWeb rows
- `GET /api/fundamentals`
  - accepts `refresh=1`; when yfinance refresh fails and a cached row exists,
    the row can be shown as `stale-after-error` with `sourceRefreshError`
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
  - accepts `refresh=1`; failed CSV refreshes can return cached
    `stale-after-error` data with source errors when available
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

Current decision as of 16 May 2026: pause the hosted backend path and remake the
project as a static GitHub Pages dashboard generated by scheduled/manual GitHub
Actions. The old single-host templates and runbook remain for reference, but
the preferred public beta path is now `docs/static-github-pages-remake.md`.

Static beta status as of 17 May 2026: the repo contains YAML inputs under
`data/`, generated JSON under `docs/data/`, copied Pages assets under `docs/`,
and `.github/workflows/static-data.yml` for scheduled/manual generation. GitHub
Pages is live at https://keresell-coder.github.io/oslo-market-workspace/. The
first manual static-data workflow run on `main` succeeded and published a
manifest generated at `2026-05-17T07:32:16+00:00` with 13 watchlist rows and no
reported screener/technical/event/watchlist errors. Local release-prep
verification and public Pages browser checks passed; capture an explicit
another-device laptop/tablet check if not already done by the operator.

Watchlist edit workflow status as of 19 May 2026: the public Pages app remains
read-only and token-free. Watchlist changes use `data/watchlist.yml`, a PR,
regenerated `docs/data/*.json`, and public Pages verification. The starter
polish pass adds in-app edit steps, `docs/watchlist-edit-workflow.md`, and
`BRG.OL` / Borregaard ASA to the repo-owned watchlist source.

Fundamental frameworks status as of 19 May 2026: deferred while a separate
`oslo-quant` repository is being developed as a possible external source
artifact, similar to `oslo-screener`. Wait for a status update and stable output
contract before integrating framework tabs or generated framework JSON here.

Watchlist streamlining status as of 16 May 2026: the shared local/static
frontend now renders compact Watchlist synthesis rows, visible source chips, and
expandable per-row source-detail drawers instead of repeating dense caveat text
in every main row cell.

Source-quality sprint status as of 16 May 2026: Fundamental Multiples And
Technical Coverage Verification is complete. Fundamentals rows now include
`multipleSourceMetadata`; source-gated displayed values retain raw provider
fields separately; P/NAV and EV/EBIT stay intentionally unavailable; and
Technical indicators explicitly list watchlist symbols absent from
the current Oslo Screener `latest.csv`/report output as missing coverage rows.

## Static Remake References

- GitHub Pages static-site support and server-side limitation: https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site
- GitHub Actions workflow syntax, `schedule`, and `workflow_dispatch`: https://docs.github.com/actions/learn-github-actions/workflow-syntax-for-github-actions
- GitHub Actions scheduled workflow behavior: https://docs.github.com/actions/reference/events-that-trigger-workflows
- GitHub repository contents API for file updates, relevant only if a safe authenticated write flow is later planned: https://docs.github.com/en/rest/repos/contents

## External Sources In Use

- Yahoo Finance via `yfinance`
- EV/EBITDA source-gate: the app computes displayed EV/EBITDA from yfinance
  enterprise value, yfinance TTM EBITDA, and yfinance FX rates when needed. The
  raw Yahoo/yfinance `enterpriseToEbitda` field is kept separately as
  `providerEnterpriseToEbitda` because it can be inconsistent when quote
  currency and financial statement currency differ.
- Other fundamental multiples now follow the same audit pattern where feasible:
  displayed TTM P/E, forward P/E, P/B, P/S, EV/revenue, and dividend yield are
  source-gated from explicit yfinance inputs when available; raw provider
  fields are retained separately for audit.
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
- Coverage reconciliation on 16 May 2026 found HAFNI.OL, KMAR.OL, LINK.OL,
  PUBLI.OL, and VEND.OL absent from the current published/raw `latest.csv`, the
  latest committed dated report, the summary, and the public ticker input lists.
  The app describes these as current report-output gaps and does not compute or
  merge fallback technical labels.
- Current generated Oslo Stock static data after the 19 May 2026 rebuild shows
  BRG.OL covered by the screener CSV and only KMAR.OL missing/history-gated in
  watchlist technical coverage. HAFNI.OL, LINK.OL, PUBLI.OL, and VEND.OL are
  now covered by the generated screener output.

## External Sources Considered But Not Automated

- TradingView analyst/target-price pages
- MarketScreener consensus pages
- Primary company report parsing for quarterly statement verification
- Scheduled NewsWeb/Euronext announcement automation
The current digest is on-demand. Any scheduled automation should reuse the same conservative source path, keep deduplication/source links/error/freshness reporting visible, and preserve overlapping analyst-count caveats for consensus data.
