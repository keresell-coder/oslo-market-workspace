# Oslo Stock web-app

Local-first Oslo Bors research workspace for a personal watchlist, later shareable with friends/investment-club style users. The Watchlist is the synthesis view; deeper tabs hold source detail, peer context, fundamentals, own-history context, technical indicators, and event/consensus context.

The app is intentionally conservative. It must not produce buy/sell investment advice, and it must not label stocks cheap, expensive, fair, or neutral from standalone multiples. Valuation context must be relative to peers, sector, own history, source quality, and missing data.

## Run

```bash
python3 app/server.py
```

Open:

```text
http://127.0.0.1:8765
```

If the port is busy, stop the stale Python process or use a temporary local port. During development `8768` has often been used.

To open the app for normal Safari review after a sprint or update:

```bash
scripts/open_in_safari.sh
```

The script starts the local server in Terminal if needed, verifies `http://127.0.0.1:8765/api/health`, and opens Safari at `http://127.0.0.1:8765`.

## Sharing Prep

The default run is local-only and unauthenticated. Runtime settings can be configured with environment variables:

- `OSLO_APP_HOST`: bind host, default `127.0.0.1`.
- `OSLO_APP_PORT`: bind port, default `8765`.
- `OSLO_APP_DB_PATH`: optional SQLite database path.
- `OSLO_APP_BACKUP_DIR`: optional backup destination for database backup/restore scripts.
- `OSLO_APP_BACKUP_MIRROR_DIR`: optional mirror destination for backup files and checksums.
- `OSLO_APP_REQUIRE_AUTH`: set to `1` to require Basic Auth.
- `OSLO_APP_AUTH_USERNAME` and `OSLO_APP_AUTH_PASSWORD`: Basic Auth credentials.

If `OSLO_APP_HOST` is set to a non-local bind host such as `0.0.0.0`, the server refuses to start unless Basic Auth credentials are configured or `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE=1` is set intentionally. See `docs/deployment-sharing.md` and `.env.example`.

SQLite backup/restore utilities:

```bash
scripts/backup_database.sh
scripts/drill_restore_database.sh
scripts/restore_database.sh backups/sqlite/<backup>.sqlite3
```

The backup script uses SQLite's online backup path, writes timestamped backups under `backups/sqlite/` by default, and writes a `.sha256` checksum. The restore script verifies the selected backup, creates a pre-restore backup of the current database, and replaces the configured database path. Stop the app before restoring.

Hosted deployment support files:

- `deploy/oslo-stock.env.example`: hosted environment file shape for localhost binding, Basic Auth, persistent SQLite, and backup mirror paths.
- `deploy/oslo-stock.service`: systemd service template for one Python app instance.
- `deploy/Caddyfile.example`: HTTPS reverse-proxy template.
- `deploy/oslo-stock-backup.cron.example`: daily hosted backup job template.
- `scripts/verify_public_deployment.sh`: hosted HTTPS/API/auth smoke test.

Beta/operator routine:

- `docs/operator-refresh-checklist.md`: refresh order and source-quality checks
  before sharing a beta view.

Current go-live assessment: the app can go live soon as a controlled,
authenticated MVP, but not as a public unauthenticated site and not as a fully
validated research platform. See `docs/go-live-readiness.md`.

Repository: `keresell-coder/oslo-market-workspace`

Local folder:

```text
/Users/ke/Documents/Oslo Stock web-app
```

## Current App

- **Start**: concise intent, source/metric summary, operator refresh checklist, limitations, and not-investment-advice disclaimer.
- **Watchlist**: main scan table with collapsed note editing, add/remove symbols, price, RSI14 dashboard alert, technical indicators, multiples, own history entry point, peer context status/counts, provider target/rating source rows, updates, and actions.
- **Fundamentals**: cached Yahoo/yfinance fields in grouped columns, metric guide/data-validation panel below the primary table, and expanded consensus/source row editor.
- **Own history**: dedicated tab for descriptive price-history context, compact price charts, local snapshot trend charts/rows, yfinance dated quarterly statement rows where available, primary-report review tracking, source/freshness/confidence metadata, and missing-data gates.
- **Technical indicators**: `/api/technical-indicators` parses Oslo Screener `latest.csv` for RSI14, RSI6, MACD histogram, SMA50 distance, ADX14, MFI14, source signal, risk, stop-loss, and position sizing fields; the indicator guide sits behind a collapsed details control.
- **Benchmarks**: editable peer groups with curation status, role labels, peer notes, sector benchmark components, minimum-data checks, and reviewed manual/source-linked sector KPI input slots; peer metric tables are shown before supporting checklist and sector details.
- **News/Events**: watchlist-first NewsWeb announcements plus manual/source-reviewed event rows, on-demand 24-hour daily digest grouped by symbol/category, duplicate/correction grouping, per-symbol fetch status, source links, freshness, confidence, and missing-data caveats.
- **RSI14 screener**: separate embedded/parsing tab for the published Oslo Screener dashboard. The dashboard was refreshed to the 05 May 2026 screener data after its Pages branch lagged the current `latest.csv`. Do not edit the Oslo Screener repository unless explicitly requested.
- **Sources**: source quality and limitations.
- **Sharing prep**: environment-based host/port/database configuration, SQLite backup/restore/drill scripts, optional backup mirroring, an optional Basic Auth gate, deployment target notes, HTTPS/reverse-proxy expectations, hosted service/reverse-proxy templates, a hosted verification script, operator refresh checklist, a production access-control checklist, and a CI syntax-check workflow.

## Rules And Guardrails

- Free data is screening-grade only: delayed, incomplete, rate-limited, and sometimes wrong.
- Show source, timestamp/freshness, confidence, limitations, and missing data clearly.
- Missing data stays missing. Do not infer NAV/fleet values, P/NAV, EBIT/kg, backlog, ROE/CET1, LTV/WAULT, or sector KPIs from generic sector labels.
- Yahoo/yfinance target and rating-label data is one provider row by default, not verified consensus. Reported analyst refs may overlap across providers and are not deduplicated.
- Consensus/source rows may be `provider-row`, `manual-source`, or `manual-override`; manual rows carry review status, source URL, as-of date, currency, method note, and limitation note when known.
- Peer statuses are local curation markers only: `missing`, `draft`, `reviewed`, `trusted`. They do not create valuation verdicts.
- Backend-assisted peer groups stay `draft` until reviewed. Do not auto-assign a company to an unrelated existing peer group based only on sector labels.
- Sector benchmark components are explicit: Oslo peer group, international peer group, and optional sector index/proxy. Sector index/proxy rows are never inferred automatically.
- Minimum-data checks are visible before any derived valuation score/status marker is considered. Valuation scores remain disabled.
- Technical BUY/SELL/BUY-watch/SELL-watch labels are source signal names from the screener CSV/dashboard, not app investment advice.
- Preserve the **Technical indicators** tab and `/api/technical-indicators`; the RSI14 screener dashboard remains a separate tab.

## Current Data State

- Price history uses Yahoo/yfinance 1-year daily closes with observation count, range, percentile, sampled chart points, source, freshness, confidence, and limitations.
- Quarterly statement history uses yfinance quarterly income statement, balance sheet, and cash-flow tables only when they return dated quarter-end columns; values are not inferred from current summary fields, missing rows stay missing, and each period stays not-primary-verified until a source-linked company-report review row is stored.
- Own-history uses local `fundamentals_snapshots`; Watchlist signals and compact snapshot charts require minimum observations.
- Fundamentals table default columns are grouped: company, price/size, valuation multiples, earnings/yield, consensus/source refs, source, and links.
- Fundamentals metric guide and validation panel explain fields, coverage, source quality, and missing-data caveats behind progressive disclosure below the main scan table.
- Peer groups can be edited in Benchmarks. Existing researched groups cover NOD, MOWI, FRO, HAFNI, DOFG, ODL, KOG, and LINK; local database status may be `reviewed` or `trusted`.
- Tankers and offshore energy are split into tighter groups: crude tankers for FRO, product tankers for HAFNI, subsea/offshore services for DOFG, and offshore drilling rigs for ODL.
- Sector KPI input slots exist for shipping NAV/fleet/P/NAV, seafood EBIT/kg and harvest volume, offshore/defence backlog, bank ROE/CET1, and real-estate LTV/WAULT. Values remain missing in benchmark output until reviewed/trusted manual or source-linked inputs have source context.
- Remaining major gaps: primary-source value entry/import for quarterly statements, optional sector index/proxy curation, optional scheduled NewsWeb digest automation, selecting the real mounted off-host backup destination, and any actual external deployment.
- Public MVP gap: the repo now has hosted service/reverse-proxy templates and a
  hosted verification script, but the app still needs a real domain/subdomain,
  a provisioned single host, DNS/HTTPS setup, a real off-host backup mirror,
  hosted restore drill, and cross-device smoke testing before release.

## Verification

Before finishing code changes, run:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/event-monitoring" | python3 -m json.tool
```

Use the in-app browser for visual checks when UI changes. Specifically verify Watchlist, Fundamentals, Own history, Benchmarks, News/Events, Technical indicators, and the separate RSI14 screener tab.

After every sprint or user-visible update, also run:

```bash
scripts/open_in_safari.sh
```

Leave the app available in Safari at `http://127.0.0.1:8765` unless the user asks to stop the local server.

## Documentation Discipline

After each completed task, update the relevant docs so they reflect what changed, what was verified, and what remains planned. Default continuation context is this `README.md` plus `docs/roadmap.md`; use more detailed docs only when needed.

## Recently Completed

**Data Refresh And Source-Quality Readiness**

- Added a Start-tab operator refresh checklist for the beta refresh/review
  routine.
- Added refresh status strips to Watchlist, Fundamentals, Own history,
  Benchmarks, News/Events, Technical indicators, and Sources.
- Refresh status strips show refresh state, last successful app refresh, source
  timestamp when available, source/cache details, warnings/errors, and the
  relevant source-quality check before sharing.
- Added `docs/operator-refresh-checklist.md`.
- Kept the NewsWeb daily digest on demand, added no recommendation logic, added
  no standalone multiple verdict labels, and did not edit Oslo Screener repos.
- Verified backend/frontend/script syntax, README API checks, restore drill,
  temporary backup-mirror copy, in-app browser refresh-status pass with no
  console errors, and Safari launch.

**Public Access Foundation Repo Prep**

- Added hosted deployment templates for a single Python app instance bound to
  localhost behind Caddy HTTPS.
- Added a hosted environment template with `OSLO_APP_DB_PATH` outside the git
  checkout and `OSLO_APP_BACKUP_MIRROR_DIR` pointing to an off-host/encrypted
  mounted backup location.
- Added a daily backup cron example and `scripts/verify_public_deployment.sh`
  for HTTPS/API/auth checks against a public URL.
- Confirmed no real public URL, DNS record, host credential, or mounted
  off-host mirror path is present in this local repo, so actual external
  deployment and another-device verification remain blocked pending those
  operator details.
- Verified backend/frontend/script syntax, README API checks, restore drill,
  temporary backup-mirror copy, local dry run of the hosted verification script,
  in-app browser tabs, and Safari launch.

**Go-Live Readiness Reframe**

- Clarified that the next goal is a controlled public MVP at a public HTTPS URL, not broader feature work first.
- Added `docs/go-live-readiness.md` with the public-access direction, data-quality boundary, interactive refresh expectations, and a 2-sprint minimum / 3-sprint recommended path.
- Defined the next sprint as Public Access Foundation: hosting target, HTTPS reverse proxy, access control, persistent SQLite path, off-host backups, restore drill, hosted API checks, and verification from another device.

**Primary Verification And Sharing Readiness**

- Added manual/source-linked primary company-report review tracking for quarterly statement periods through `/api/quarterly-statement-reviews`.
- Own history now shows primary-review counts, per-period primary-review status, and a source-review form inside quarterly statement detail.
- Kept yfinance quarterly statement rows screening-grade by default; unreviewed periods stay not-primary-verified, missing rows stay missing, and primary reviews do not backfill values or create recommendation logic.
- Added `docs/primary-report-verification.md` with review statuses, API examples, source requirements, and no-verdict guardrails.
- Added `scripts/drill_restore_database.sh` and optional `OSLO_APP_BACKUP_MIRROR_DIR` backup mirroring so restore drills and off-host backup copies are repeatable before sharing.
- Verified backend/frontend/script syntax, README API checks, `/api/quarterly-statement-reviews?symbol=MOWI.OL`, non-mutating POST validation, restore drill, temporary backup-mirror copy, in-app browser navigation including Own history primary-review UI, browser console errors, and Safari launch.

**Sharing And Deployment Follow-Up**

- Decided the next practical sharing path: keep local/private use as default; use Tailscale/LAN only for a small trusted pilot; use a single EU VPS with the app bound to localhost, HTTPS reverse proxy, persistent SQLite path, and off-host backups for any later external sharing.
- Added `scripts/backup_database.sh` and `scripts/restore_database.sh` using SQLite online backup plus `PRAGMA integrity_check`, timestamped backup files, and SHA-256 checksum files.
- Documented backup cadence, retention target, restore workflow, hosted database path expectations, deployment target comparison, HTTPS/reverse-proxy expectations, and a production access-control checklist in `docs/deployment-sharing.md`.
- Preserved quarterly statement history as screening-grade only, kept optional sector index/proxy curation explicit/reviewed, kept the NewsWeb daily digest on demand, preserved `/api/technical-indicators` and the separate RSI14 screener tab, and added no recommendation logic.
- Verified script syntax, backend/frontend syntax, README API checks, backup creation/checksum validation, restore to a temporary database path, and Safari launch.

**Sharing Prep Follow-Up**

- Added environment-based runtime settings for host, port, SQLite path, and optional Basic Auth.
- Kept the default run local-only at `127.0.0.1:8765` with no auth prompt.
- Added a startup guard that refuses non-local unauthenticated binds unless an explicit override is set.
- Added `docs/deployment-sharing.md`, `.env.example`, and a GitHub Actions CI workflow for backend/frontend syntax checks.
- Kept quarterly statement history screening-grade, sector index/proxy rows explicit, the on-demand NewsWeb digest unchanged, and recommendation logic absent.
- Verified syntax, README API checks, optional Basic Auth behavior on a temporary local port, non-local unauthenticated startup refusal, in-app browser navigation across the main tabs, and Safari launch.

**Quarterly History And Sharing Prep**

- Confirmed a reliable screening-grade source path for true quarterly statement history through yfinance quarterly income statement, balance sheet, and cash-flow tables with dated quarter-end columns.
- Added strict quarterly statement parsing for explicit yfinance row labels such as revenue, EBIT/EBITDA, net income, equity, debt, cash, operating cash flow, capex, and free cash flow.
- Kept quarterly statement values missing when yfinance omits a period or row; no statement history is inferred from current summary fields.
- Added a Quarterly statement history section to Own history row details with period count, source path, statement currency when yfinance supplies `financialCurrency`, row coverage, confidence, timestamp, and limitations.
- Preserved optional sector index/proxy curation as explicit peer rows only, kept the on-demand NewsWeb daily digest unchanged, and added no recommendation logic.
- Verified syntax, README API checks, focused MOWI quarterly payload with 6 dated periods ending 2025-12-31, in-app browser navigation across Watchlist/Fundamentals/Own history/Benchmarks/News/Events/Technical indicators/RSI14 screener, and browser console errors.
- Opened the app in Safari at `http://127.0.0.1:8765`.

**NewsWeb Daily Digest**

- Added an on-demand 24-hour watchlist digest to `/api/event-monitoring`, built from the existing NewsWeb ticker fetch path with local cache reuse and conservative per-symbol calls.
- Grouped digest rows by watchlist symbol and existing event taxonomy.
- Added heuristic duplicate/correction grouping using same client announcement IDs where present plus same-day title fingerprints for repeated issuer messages and same-title rows.
- Added per-symbol NewsWeb fetch states for fresh, stale, old, error, and stale-after-error cases; fetch errors remain visible in the digest and detailed News/Events table.
- Kept source links, timestamps, freshness, confidence, limitations, missing-data wording, and no-advice language visible.
- Preserved Watchlist, Fundamentals, Own history, Benchmarks, News/Events, Technical indicators, `/api/technical-indicators`, and the separate RSI14 screener tab.
- Verified syntax, README API checks, `/api/event-monitoring?refresh=1` returning a daily digest with 8 rows across 5 watchlist symbols during the live check, in-app browser navigation across the main tabs, and Safari launch.

**Own History Tab Streamlining**

- Moved the dense own-history surface out of the Fundamentals matrix and Benchmark page into a dedicated **Own history** tab between Fundamentals and Technical indicators.
- Kept the Watchlist Own history column as the entry point and changed it to open the matching row in the Own history tab.
- Split the Own history table into separate Company, Context signal, Price history, Local snapshots, Source/gate, and Detail columns.
- Fundamentals now focuses on current source fields, consensus refs, source metadata, and links.
- Benchmarks now focuses on peer/sector context; minimum-data checks still show own-history coverage requirements, but the detailed own-history component lives in the dedicated tab.
- Reused the existing `/api/fundamentals` payload and historical-context renderer, avoiding a new backend endpoint.

**Compact Charts And Trends**

- Added observation-gated compact price sparklines from sampled Yahoo/yfinance 1-year daily closes.
- Added compact own-multiple sparklines from local `fundamentals_snapshots`; charts stay gated until the existing local-snapshot minimum is met.
- Watchlist keeps its scan-first table and uses the Own history column as an entry point to the dedicated tab.
- Own history shows compact price trend context and keeps denser price/snapshot chart detail in row details.
- Benchmarks no longer repeats the own-history chart block; minimum-data gates still reference own-history coverage.
- Chart cards include source, freshness/timestamp, confidence, observation count/gates, and limitations through visible metadata or tooltip copy; no valuation verdict or recommendation language was added.
- Preserved peer status labels, explicit sector index/proxy curation, Technical indicators, `/api/technical-indicators`, and the separate RSI14 screener tab.
- Verified syntax, README API checks, Watchlist/Fundamentals/Benchmarks/Technical indicators/RSI14 navigation in the in-app browser, and Safari launch.

**Consensus Quality**

- Added explicit consensus/source row metadata for row type, review status, target currency, as-of date, source URL, method note, and limitation note.
- Kept Yahoo/yfinance target and rating fields labeled as provider-row data, not verified consensus.
- Changed Watchlist and Fundamentals wording from consensus conclusions toward provider/source rows and raw rating labels.
- Changed rating summaries so the app counts raw B/H/S provider rows but does not produce a majority or analyst-weighted BUY/HOLD/SELL recommendation.
- Expanded the Fundamentals consensus editor into grouped source, value, and quality sections, with a source-row table for reviewing stored rows.
- Preserved overlapping-analyst caveats, missing-data behavior, peer status labels, Technical indicators, `/api/technical-indicators`, Own history, and the separate RSI14 screener tab.
- Verified syntax, README API checks, in-app browser navigation for Watchlist/Fundamentals/Own history/Benchmarks/Technical indicators/RSI14 screener, and Safari launch.

**NewsWeb And Event Monitoring**

- Renamed the tab to **News/Events** and added watchlist-first NewsWeb on-demand rows, source-quality status, category summary, source links, and a manual significant-event editor.
- Added event categories: earnings, contract/order, financing/private placement, dividend, insider, M&A, guidance/profit warning, and corporate action.
- Extended significant-event rows with source type, review status, confidence, and limitation-note metadata.
- Added on-demand NewsWeb pulls from the same `api3.oslo.oslobors.no` endpoint discovered by the official NewsWeb frontend; Watchlist Updates now uses NewsWeb rows plus manual rows.
- Confirmed the official Euronext Oslo page identifies NewsWeb as the listed-company news site updated immediately 24/7. Scheduled digest automation remains separate and should use conservative rate limits.
- Preserved Watchlist, Fundamentals, Own history, Benchmarks, Technical indicators, `/api/technical-indicators`, and the separate RSI14 screener tab.
- Verified syntax, README API checks, `/api/event-monitoring` returning 60 NewsWeb rows across 12 watchlist symbols, in-app browser navigation for Watchlist/Fundamentals/Own history/Benchmarks/News/Events/Technical indicators/RSI14 screener, and Safari launch.

**RSI14 Screener Dashboard Refresh**

- Confirmed the published Oslo Screener `latest.csv` was current while the separate dashboard HTML was still showing 28 April 2026 data.
- Root cause: the `oslo-screener-dashboard` repository default branch was an older setup branch, so scheduled runs used stale workflow code and did not update the `gh-pages` branch served by GitHub Pages.
- Refreshed the dashboard to **Screener data: 05 May 2026**, pushed the fixed dashboard branch state, and published the refreshed `gh-pages` site.
- Final verified public dashboard after the reliability run shows `Source generated: 05 May 2026 19:59 UTC`, `Generated: 05 May 2026 20:02 UTC`, and source screener labels only: BUY 1, SELL 4, BUY-watch 8, SELL-watch 11, across 111 screened rows.
- Yahoo RSS and Oslo Bors news subfetches had rate-limit/source parse failures during generation; those limitations are visible in the dashboard source notes and do not change the screener data freshness.
- Verified the public dashboard URL, GitHub Pages deployment success, README API checks, and Safari launch.

**Oslo Screener Reliability Pass**

- Set `oslo-screener-dashboard` default branch to `main` so scheduled workflows run from the intended branch.
- Hardened `oslo-screener` daily/weekly workflows with concurrency, timeouts, `latest.csv` metadata/row verification, safer `git pull --rebase` before bot pushes, and optional dashboard workflow triggering when `DASHBOARD_WORKFLOW_TOKEN` is configured.
- Removed tracked `.DS_Store` from `oslo-screener` and ignored it going forward.
- Hardened `oslo-screener-dashboard` with later 09:30 UTC and backup 12:30 UTC weekday schedules, concurrency, output verification, `Pillow` in requirements, and dashboard source freshness rendering from the `latest.csv` `generated_at` metadata.
- Published the regenerated dashboard to `gh-pages`; the RSI14 tab should now show both the screener data date and source-generation freshness.
- Verified screener compile/tests, dashboard compile/generation, workflow YAML parsing, GitHub default branches, public dashboard output, web-app API checks, and Safari launch.

**Reviewed Sector KPI Inputs And Benchmark Polish**

- Added `/api/sector-kpi-inputs` for saving sector KPI input rows with value, unit/currency, period, source name, source URL, note, input type, and review status.
- Benchmark sector KPI rows now carry source-path guidance for shipping NAV/fleet/P/NAV, seafood harvest volume and EBIT/kg, offshore/defence backlog and utilisation, bank ROE/CET1, and real-estate LTV/WAULT.
- Unreviewed or unsourced KPI values stay missing in benchmark output; reviewed/trusted values appear only when source context is present.
- Benchmarks now include a collapsed sector KPI input editor while preserving peer status labels, explicit sector index/proxy rows, disabled valuation scores, and descriptive no-verdict language.
- Verified syntax, Watchlist, Fundamentals, Benchmarks, Technical indicators, the separate RSI14 screener tab, and the README API checks.
- Added a Safari launcher script and sprint closeout rule so the app is opened in Safari after future iterations.

**UI Simplification And Progressive Disclosure**

- Watchlist scan now appears first; note editing and add-symbol controls are collapsed behind details controls.
- Fundamentals and Technical indicators show the primary scan table before metric/indicator guides.
- Benchmarks show peer metric context before checklist and sector support blocks.
- Supporting explanations, policies, validation coverage, indicator thresholds, sector KPI placeholders, and editors remain available without dominating the first view.
- Frontend tab loading now avoids repeat fetches after a tab is already loaded, and dynamic Watchlist/Benchmark controls use delegated handlers instead of rebinding after every render.
- Two unused frontend helpers were removed. Future continuation should keep `README.md` and `docs/roadmap.md` as the default context and open deeper docs only for a specific implementation need.

## Next Sprint

**Public Access Foundation**

- Provide or create the real domain/subdomain, DNS access, single-host target,
  SSH/deployment access, and mounted off-host/encrypted backup destination.
- Install the `deploy/` templates on the host with the Python app bound to
  `127.0.0.1` behind HTTPS and Basic Auth.
- Set the live `OSLO_APP_DB_PATH` and `OSLO_APP_BACKUP_MIRROR_DIR`, run hosted
  backup/mirror/restore drill, then run README API checks plus
  `scripts/verify_public_deployment.sh` against the public URL.
- Verify Watchlist, Fundamentals, Own history, Benchmarks, News/Events,
  Technical indicators, and RSI14 screener from another device.
- Run the operator refresh checklist against the hosted instance before sharing
  a beta view.
- Keep optional sector index/proxy curation explicit and reviewed.
- Continue without adding recommendation logic.

See `docs/roadmap.md` for the broader sprint plan.
