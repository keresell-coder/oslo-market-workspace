# Hosted Public Access Runbook

Use this runbook to complete Hosted Public Access Completion for **Beta v0.1.0**
after the real host details are available.

This repository cannot complete the live rollout by itself. Do not mark the
sprint complete until the operator has provided or created:

- public domain/subdomain
- DNS access for that name
- one single-host deployment target
- SSH/deployment access
- mounted off-host/encrypted backup destination
- Basic Auth credentials or a stronger tested upstream access layer

Keep secrets in host files or password managers, not in git.

## Host Install

Target shape:

- one Python app instance
- app bind: `127.0.0.1:8765`
- reverse proxy: public HTTPS to localhost app
- authentication: Basic Auth in the app or stronger upstream control
- SQLite path: persistent disk outside the git checkout
- backup mirror: mounted off-host/encrypted destination

Suggested host paths from the repo templates:

```text
/opt/oslo-stock/oslo-market-workspace
/etc/oslo-stock/oslo-stock.env
/var/lib/oslo-stock/oslo_workspace.sqlite3
/var/backups/oslo-stock/sqlite
/mnt/oslo-stock-backups/sqlite
```

Install templates:

```bash
id -u oslostock >/dev/null 2>&1 || sudo useradd --system --home /opt/oslo-stock --shell /usr/sbin/nologin oslostock
sudo install -d -o oslostock -g oslostock /opt/oslo-stock
sudo install -d -o oslostock -g oslostock /var/lib/oslo-stock
sudo install -d -o oslostock -g oslostock /var/backups/oslo-stock/sqlite
sudo install -d -m 0750 /etc/oslo-stock
sudo install -m 0600 deploy/oslo-stock.env.example /etc/oslo-stock/oslo-stock.env
sudo install -m 0644 deploy/oslo-stock.service /etc/systemd/system/oslo-stock.service
```

Clone or update the repository under
`/opt/oslo-stock/oslo-market-workspace` before starting the service. If the real
backup mirror mount is not under `/mnt/oslo-stock-backups`, update the service
template `ReadWritePaths` before installing it.

Edit `/etc/oslo-stock/oslo-stock.env` on the host:

```text
OSLO_APP_HOST=127.0.0.1
OSLO_APP_PORT=8765
OSLO_APP_REQUIRE_AUTH=1
OSLO_APP_AUTH_USERNAME=<host-secret>
OSLO_APP_AUTH_PASSWORD=<host-secret>
OSLO_APP_DB_PATH=/var/lib/oslo-stock/oslo_workspace.sqlite3
OSLO_APP_BACKUP_DIR=/var/backups/oslo-stock/sqlite
OSLO_APP_BACKUP_MIRROR_DIR=<mounted-off-host-encrypted-path>
```

Install the reverse proxy from `deploy/Caddyfile.example` or an equivalent
Nginx/Caddy config. Replace `research.example.com` with the real subdomain and
keep the upstream target at `127.0.0.1:8765`.

## Host Verification

Run these on the host after the service and proxy are configured:

```bash
python3 -m py_compile app/server.py
node --check app/static/app.js
sudo systemctl daemon-reload
sudo systemctl enable --now oslo-stock.service
sudo systemctl status oslo-stock.service
curl -s http://127.0.0.1:8765/api/health | python3 -m json.tool
```

Confirm the health payload shows:

- `sharing.localOnly: true`
- `sharing.authRequired: true`
- `sharing.databasePathConfigured: true`

Run hosted backup and restore drill with the hosted database path:

```bash
OSLO_APP_DB_PATH=/var/lib/oslo-stock/oslo_workspace.sqlite3 \
OSLO_APP_BACKUP_DIR=/var/backups/oslo-stock/sqlite \
OSLO_APP_BACKUP_MIRROR_DIR=<mounted-off-host-encrypted-path> \
scripts/backup_database.sh

OSLO_APP_DB_PATH=/var/lib/oslo-stock/oslo_workspace.sqlite3 \
OSLO_APP_BACKUP_DIR=/var/backups/oslo-stock/sqlite \
OSLO_APP_BACKUP_MIRROR_DIR=<mounted-off-host-encrypted-path> \
scripts/drill_restore_database.sh
```

Run README API checks locally against the app service:

```bash
curl -s http://127.0.0.1:8765/api/watchlist-overview | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/fundamentals?symbols=MOWI.OL" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/technical-indicators?universe=watchlist" | python3 -m json.tool
curl -s "http://127.0.0.1:8765/api/event-monitoring" | python3 -m json.tool
```

Run public HTTPS verification from outside the host or from a trusted operator
machine:

```bash
OSLO_PUBLIC_URL=https://<real-subdomain> \
OSLO_PUBLIC_AUTH_USERNAME=<host-secret> \
OSLO_PUBLIC_AUTH_PASSWORD=<host-secret> \
scripts/verify_public_deployment.sh
```

The public verification script checks Basic Auth blocking, `/api/health`, the
README API endpoints, and hosted `refresh=1` paths for Watchlist, Fundamentals,
Technical indicators, News/Events, and Benchmarks. Use
`OSLO_VERIFY_REFRESH=0` only for a targeted access-control/API smoke test; do
not use that skip for beta release evidence.

## Refresh And Browser Pass

Run `docs/operator-refresh-checklist.md` against the hosted URL before sharing a
beta view. Confirm each refresh status strip shows source timestamp/cache/error
details where available.

From another device, verify:

- Watchlist
- Fundamentals
- Own history
- Benchmarks
- News/Events
- Technical indicators
- Sources
- separate RSI14 screener tab

For refresh failures, confirm the visible wording remains explicit:

- `cached`
- `stale`
- `stale-after-error`
- `rate-limited`
- `error`
- `missing`

Do not add recommendation logic, standalone cheap/expensive/fair/neutral labels,
or inferred missing data while completing the hosted rollout.

## Release Evidence To Record

Record the following in the project docs after the hosted run:

- public HTTPS URL, without secrets
- deployment host class/provider, without exposing credentials
- hosted database path
- backup mirror destination type, without exposing secret paths if sensitive
- backup file timestamp and checksum location
- restore drill result
- public verification script result
- true-refresh verification summary
- another-device browser result
- remaining known caveats
