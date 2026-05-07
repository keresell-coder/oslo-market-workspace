# Go-Live Readiness

## Current Answer

The app is targeted for **Beta v0.1.0**. Two beta-release sprints remain before
it should be released for real private beta use:

1. Hosted Public Access Completion.
2. Beta Release Hardening.

After those two sprints, pause broad feature work and start using the app to
gain real experience.

The realistic target is a private beta public URL: a real domain over HTTPS,
Basic Auth or stronger access control, one app instance, one persistent SQLite
database, tested backups, and clear screening-grade/source-quality labels. This
fits the current architecture.

The app should not be presented as a fully validated research platform. With
free/open data, "accurate, reliable, credible, and validated" must mean:

- latest available source fetches are interactive and freshness-visible
- source, timestamp, confidence, limitations, and missing data are visible
- provider data is clearly separated from reviewed/manual/source-linked rows
- primary/report-level review is available for important fields
- missing data stays missing
- no recommendation or standalone valuation verdict logic is added

## Public Access Direction

Recommended first public setup:

- one small single-host VPS in Europe or equivalent
- app bound to `127.0.0.1`, not directly exposed
- Caddy or Nginx reverse proxy terminating HTTPS
- real domain name, for example `research.<domain>`
- Basic Auth enabled at the app or reverse-proxy layer
- SQLite database stored outside the git checkout on persistent disk
- daily SQLite online backups
- mirrored backup copy to an off-host/encrypted destination
- restore drill before launch

Avoid for the first MVP:

- static hosting, because the app is dynamic and SQLite-backed
- serverless functions, because the app is stateful
- multiple app instances, because the current SQLite database should have one
  active writer
- public unauthenticated access

## Interactive Data Expectations

The application already has interactive/on-demand pieces:

- fundamentals refresh through `/api/fundamentals?refresh=1`
- Watchlist overview refresh
- NewsWeb/event monitoring refresh through `/api/event-monitoring?refresh=1`
- Technical indicators through `/api/technical-indicators`
- manual/source-linked consensus rows
- manual/source-linked event rows
- reviewed/source-linked sector KPI inputs
- quarterly statement primary-report review tracking

Before public MVP, the refresh behavior should be made more operator-friendly:

- make each tab's refresh state and last successful refresh more obvious
- show source errors and stale states consistently after refresh
- keep conservative rate limits for NewsWeb/yfinance calls
- add a short operator checklist for refreshing and reviewing data before
  sharing with users
- avoid scheduled NewsWeb automation unless explicitly scoped

Repo/UI foundation completed for this step:

- Start tab includes an operator refresh checklist.
- Watchlist, Fundamentals, Own history, Benchmarks, News/Events, Technical
  indicators, and Sources have refresh status strips with last successful app
  refresh, source timestamp where available, source/cache details, and warnings
  or errors.
- Watchlist refresh now calls the upstream/source refresh paths it summarizes:
  yfinance fundamentals, RSI14 dashboard parsing, Oslo Screener `latest.csv`,
  and on-demand NewsWeb rows. yfinance, RSI14 dashboard, and technical CSV
  refresh failures can surface as `stale-after-error` when cached fallback rows
  remain available.
- `docs/operator-refresh-checklist.md` records the pre-sharing refresh order and
  source-quality checks.
- `docs/hosted-public-access-runbook.md` records the host-side install,
  backup/restore, hosted verification, refresh verification, and another-device
  browser pass sequence.
- NewsWeb daily digest remains on demand.

## Data Quality Boundary

The MVP can be credible, but not authoritative.

Free/open data remains screening-grade. The app should keep using source
quality, timestamps, confidence, limitations, and missing-data gates as the
trust model.

Critical fields that need stronger trust should move through source-linked or
manual review paths:

- quarterly statement periods: primary company-report review rows
- consensus/targets: provider-row versus manual/source-linked source rows
- peer groups: draft/reviewed/trusted curation
- sector KPIs: reviewed/trusted source-linked inputs
- events: NewsWeb source rows plus manual/source-reviewed significant events

Do not infer peer groups, sector KPIs, sector index/proxy rows, NAV/fleet,
EBIT/kg, backlog, ROE/CET1, LTV/WAULT, or statement history from generic sector
labels.

## Beta v0.1.0 End State

Beta v0.1.0 is release-ready when:

- the app headline clearly shows `Beta v0.1.0`
- public HTTPS URL works from another device
- unauthenticated access is blocked
- the Python app binds only to localhost behind the reverse proxy
- persistent hosted `OSLO_APP_DB_PATH` is outside the git checkout
- real hosted `OSLO_APP_BACKUP_MIRROR_DIR` points to an off-host/encrypted
  backup destination
- hosted backup, mirror copy, and restore drill pass
- all refresh buttons have been verified and fixed so refresh paths perform true
  upstream/source refreshes where supported, and clearly report cached, stale,
  rate-limited, error, or missing states
- README API checks and `scripts/verify_public_deployment.sh` pass against the
  hosted URL
- Watchlist, Fundamentals, Own history, Benchmarks, News/Events, Technical
  indicators, Sources, and the separate RSI14 screener work from another device
- `docs/operator-refresh-checklist.md` has been run against the hosted instance
- no recommendation logic or standalone valuation verdict labels have been added

## Sprint Count

Remaining beta-release path: 2 sprints.

### Sprint 1: Hosted Public Access Completion

Goal: make the app reachable at a public HTTPS address with controlled access.

Repo foundation completed:

- deployment templates now exist for hosted environment, systemd service, Caddy
  reverse proxy, and daily backup cron
- `scripts/verify_public_deployment.sh` now checks HTTPS/API/auth basics against
  a public URL
- `scripts/verify_public_deployment.sh` also supports a local HTTP dry run for
  endpoint/script validation without weakening the hosted HTTPS checks
- `scripts/verify_public_deployment.sh` now includes hosted true-refresh checks
  for Watchlist, Fundamentals, Technical indicators, News/Events, and
  Benchmarks, with explicit cached/stale/error states allowed when the API keeps
  those states visible
- `docs/hosted-public-access-runbook.md` now provides the host-side execution
  sequence and release-evidence checklist
- true-refresh behavior has been fixed and locally verified for the app refresh
  buttons where the backend supports upstream/source refreshes
- actual public deployment remains pending because no real domain/subdomain,
  DNS access, host credential, or mounted off-host backup destination is present
  in the local repo

Tasks:

- provide or create the real domain/subdomain and hosting target
- create VPS or equivalent single-host runtime
- configure Python app service bound to localhost
- configure HTTPS reverse proxy
- configure Basic Auth or stronger upstream access control
- set persistent `OSLO_APP_DB_PATH`
- set real `OSLO_APP_BACKUP_MIRROR_DIR`
- run backup, mirror copy, and restore drill on the host
- run README API checks on the hosted instance
- rerun true-refresh checks on the hosted instance and confirm stale/error
  wording survives real hosted source failures or rate limits
- verify all tabs from another device

Exit criteria:

- public URL works from another device
- unauthenticated access is blocked
- HTTPS is valid
- local-only app bind is preserved behind proxy
- backups and restore drill pass
- refresh buttons have evidence-backed true-refresh behavior or explicit stale/
  cached/error wording where a source cannot refresh
- no source-quality/no-advice guardrails regress

### Completed Repo/UI Foundation: Data Refresh And Source-Quality Readiness

Goal: make the data update workflow clear enough to use before and during beta.

Repo/UI foundation completed:

- visible refresh status strips added to the refreshable tabs
- Start-tab and document-based operator refresh checklist added
- scheduled NewsWeb automation remains out of scope

### Sprint 2: Beta Release Hardening

Goal: reduce avoidable operational risk before you use the MVP for a while.

Tasks:

- run a complete hosted smoke test from another device
- check mobile/tablet usability for tables and detail panels
- document a simple beta operating routine
- document rollback/restore steps using the hosted backup path
- create a known-good pre-beta database backup
- decide whether to pause further feature work while you use the MVP

Exit criteria:

- external device review passes
- restore/rollback steps are documented and tested
- known-good backup exists off host
- beta caveats are documented
- MVP is ready for real use and feedback collection

## Not In Go-Live Scope Unless Explicitly Added

- buy/sell/hold recommendation logic
- cheap/expensive/fair/neutral valuation labels
- public unauthenticated access
- automated broker-estimate scraping
- automated primary-report value extraction
- scheduled NewsWeb digest automation
- multi-user permission model beyond a shared access gate
- portfolio execution or transaction features

## Suggested Next Sprint

Start Sprint 1: Hosted Public Access Completion. Include the refresh-button
true-refresh verification/fix in this sprint.

Do not broaden data automation or valuation logic until the app is reachable,
backed up, access-controlled, and verified from another device.
