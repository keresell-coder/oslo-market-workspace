# Deployment And Sharing Prep

This document records the current sharing decision as of 06 May 2026. It is
prep work only; it does not deploy the app externally. The next go-live target
is a controlled public MVP with HTTPS and authentication, not public
unauthenticated access.

The default app run is local-only:

```bash
python3 app/server.py
```

Default URL:

```text
http://127.0.0.1:8765
```

## Runtime Settings

The server reads these environment variables:

- `OSLO_APP_HOST`: bind host. Default `127.0.0.1`.
- `OSLO_APP_PORT`: bind port. Default `8765`.
- `OSLO_APP_DB_PATH`: optional SQLite database path. Relative paths resolve from the project root.
- `OSLO_APP_BACKUP_DIR`: optional local backup directory for SQLite backup/restore scripts.
- `OSLO_APP_BACKUP_MIRROR_DIR`: optional mirror directory for backup files and checksums.
- `OSLO_APP_REQUIRE_AUTH`: set to `1` to require Basic Auth.
- `OSLO_APP_AUTH_USERNAME`: Basic Auth username.
- `OSLO_APP_AUTH_PASSWORD`: Basic Auth password.
- `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE`: set to `1` only when an upstream trusted access layer handles authentication.

## Current Decision

Recommended path before broader sharing:

1. Keep local/private use as the default.
2. For a small trusted pilot, use a private network path such as Tailscale Serve
   or a LAN-only bind with Basic Auth.
3. For external sharing, use one small single-host VPS in Europe with the app
   bound to `127.0.0.1`, a reverse proxy terminating HTTPS, a persistent
   SQLite path, and off-box backups.

Do not use a static host, serverless function, or multi-instance platform for
the current app shape. The app is stateful and SQLite-backed; one writable
database file should have one active app instance.

Practical target comparison:

| Target | Fit | Pros | Tradeoffs / requirements |
| --- | --- | --- | --- |
| Local Mac or LAN with Basic Auth | Best for personal use and very small trusted review | No cloud cost, same local data, fastest to operate | Not suitable for public access; uptime depends on the machine and network |
| Tailscale Serve tailnet-only | Good first private pilot | Avoids public internet exposure; each user must be in the tailnet | Not a public deployment; access is tied to Tailscale account/device management |
| Small EU VPS, for example Hetzner CX23/CPX22-class or equivalent | Recommended first external target | Simple fit for Python + SQLite; stable disk path; straightforward Caddy/Nginx reverse proxy and backup jobs | Requires server patching, SSH hardening, firewalling, monitoring, and explicit backup/restore testing |
| PaaS with persistent disk/volume, such as Render or Fly.io | Possible later | Managed HTTPS and deployment workflow | Persistent disks/volumes are single-service or machine-local concepts; scaling to multiple app instances is not appropriate for this SQLite app |

Provider prices and product limits change. Re-check current vendor docs before
spending money or moving the database.

## Public MVP Readiness

The app is close to a public MVP, but not live-ready today. Before giving users
a public address, complete:

- domain/subdomain decision
- single-host deployment target
- HTTPS reverse proxy
- Basic Auth or stronger access control
- app service bound to localhost
- persistent hosted SQLite path
- real off-host backup mirror path
- hosted backup and restore drill
- hosted README API checks
- cross-device browser verification

The repository now includes deployment support files for the recommended
single-host path:

- `deploy/oslo-stock.env.example`: install as
  `/etc/oslo-stock/oslo-stock.env` and replace placeholders with real secrets
  and host paths.
- `deploy/oslo-stock.service`: systemd service template for one app instance
  running from `/opt/oslo-stock/oslo-market-workspace`.
- `deploy/Caddyfile.example`: Caddy HTTPS reverse-proxy template for a public
  subdomain proxying to `127.0.0.1:8765`.
- `deploy/oslo-stock-backup.cron.example`: daily backup cron template.
- `scripts/verify_public_deployment.sh`: hosted smoke test for HTTPS, Basic
  Auth blocking, `/api/health`, and the README API endpoints.

These files do not create the DNS record, provision the VPS, mount the off-host
backup destination, or verify another-device browser access by themselves.

Recommended sprint count from the current state:

- 2 sprints minimum for a controlled public MVP.
- 3 sprints recommended to include hosted smoke testing and beta operating
  documentation before relying on it.

See `docs/go-live-readiness.md`.

## Sharing Guardrails

- Local-only use does not require authentication.
- Binding to a non-local host, such as `0.0.0.0`, requires Basic Auth credentials by default.
- The server refuses non-local unauthenticated startup unless `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE=1` is set intentionally.
- Basic Auth is a sharing-prep gate, not a full production security model.
- Use HTTPS, backups, access controls, and reviewed deployment settings before external sharing.

Example private-network run:

```bash
OSLO_APP_HOST=0.0.0.0 \
OSLO_APP_PORT=8765 \
OSLO_APP_AUTH_USERNAME='choose-a-user' \
OSLO_APP_AUTH_PASSWORD='choose-a-long-password' \
python3 app/server.py
```

## Data And Backups

Runtime data lives in SQLite. The default database path is:

```text
app/data/oslo_workspace.sqlite3
```

For a hosted setup, put the database outside the git checkout, for example:

```text
/var/lib/oslo-stock/oslo_workspace.sqlite3
```

Then run the app with:

```bash
OSLO_APP_DB_PATH=/var/lib/oslo-stock/oslo_workspace.sqlite3 python3 app/server.py
```

### Backup Workflow

Use the SQLite online backup API rather than copying the live database file.
The repository now includes:

```bash
scripts/backup_database.sh
scripts/restore_database.sh
scripts/drill_restore_database.sh
```

Default backup location:

```text
backups/sqlite/
```

Backups are ignored by git. Each backup writes a timestamped `.sqlite3` file and
a `.sha256` checksum file.

Run a backup:

```bash
scripts/backup_database.sh
```

Use `OSLO_APP_DB_PATH` when backing up a non-default database path:

```bash
OSLO_APP_DB_PATH=/var/lib/oslo-stock/oslo_workspace.sqlite3 scripts/backup_database.sh
```

Off-host backup decision for the next private-sharing step:

- Keep the local backup destination as `backups/sqlite/` for quick restores.
- Set `OSLO_APP_BACKUP_MIRROR_DIR` to a mounted encrypted cloud folder, removable
  disk, or other off-host path before any external sharing.
- Do not commit backups or mirror-path credentials to git.
- Treat VPS/provider snapshots as secondary convenience copies, not the only
  backup.

Example mirror run:

```bash
OSLO_APP_BACKUP_MIRROR_DIR="$HOME/Library/CloudStorage/Encrypted Oslo Backups" \
  scripts/backup_database.sh
```

Minimum backup cadence before broader sharing:

- Before any deployment/runtime change.
- Before any schema-affecting code change.
- After meaningful manual curation of watchlist notes, peer groups, sector KPI
  inputs, consensus/source rows, or significant events.
- Daily while externally shared.

Retention target:

- Keep at least 7 daily backups.
- Keep at least 4 weekly backups.
- Keep one known-good pre-sharing backup.
- Copy backups off the app host, preferably to an encrypted cloud folder,
  object-storage bucket, or another machine. Host snapshots are useful but are
  not the only backup.

### Restore Workflow

Restores are point-in-time replacements, not merges. Any data changed after the
chosen backup is lost unless manually re-entered.

1. Stop the app process and reverse proxy route.
2. Choose the backup file and verify its checksum when available:

   ```bash
   shasum -a 256 -c backups/sqlite/<backup>.sqlite3.sha256
   ```

3. Restore:

   ```bash
   scripts/restore_database.sh backups/sqlite/<backup>.sqlite3
   ```

4. Restart the app.
5. Run `/api/health` and the README verification endpoints.
6. Confirm Watchlist, Fundamentals, Own history, Benchmarks, News/Events,
   Technical indicators, and RSI14 screener still render.

The restore script verifies the selected backup with `PRAGMA integrity_check`
and writes a pre-restore backup of the current database before replacement.

### Restore Drill

Run a restore drill before any external sharing and after backup-script changes:

```bash
scripts/drill_restore_database.sh
```

The drill creates a fresh backup, validates its checksum when present, restores
to a scratch database path, runs `PRAGMA integrity_check`, compares restored
table names against the live database, and deletes the scratch file. It does not
replace the live database.

## HTTPS And Reverse Proxy Expectations

For external sharing, do not expose the Python server directly. Keep the app
bound to localhost and put a reverse proxy in front:

```bash
OSLO_APP_HOST=127.0.0.1 OSLO_APP_PORT=8765 OSLO_APP_REQUIRE_AUTH=1 python3 app/server.py
```

Example Caddy shape:

```caddyfile
research.example.com {
	reverse_proxy 127.0.0.1:8765
}
```

Use `deploy/Caddyfile.example` as the repo-maintained starting point and keep
app-layer Basic Auth enabled through `/etc/oslo-stock/oslo-stock.env` unless a
stronger upstream access layer is configured and tested.

Expectations:

- Use a real domain name and HTTPS.
- Redirect HTTP to HTTPS.
- Bind the app to `127.0.0.1`; expose only the proxy publicly.
- Keep Basic Auth enabled unless a stronger upstream auth layer is already
  configured and tested.
- Do not set `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE=1` for public internet
  access.
- Keep the SQLite database on persistent local disk, not an ephemeral deploy
  filesystem.
- Keep deployment secrets in environment files or service manager settings that
  are not committed to git.

## Production Access-Control Checklist

Before external sharing:

- Domain and HTTPS are working.
- Python app binds only to localhost behind the proxy.
- Basic Auth or stronger upstream access control is enabled.
- Password is long, unique, and shared out-of-band.
- Firewall exposes only SSH, HTTP, and HTTPS as needed.
- SSH uses keys; password SSH login is disabled where practical.
- `OSLO_APP_DB_PATH` points to persistent storage outside the git checkout.
- Backup and restore have been tested on a copy.
- `OSLO_APP_BACKUP_MIRROR_DIR` points to a mounted off-host/encrypted backup destination and a mirror copy exists.
- Source/freshness/confidence/limitation and missing-data language remains
  visible.
- `docs/operator-refresh-checklist.md` has been run against the hosted instance
  before sharing a beta view.
- Quarterly statement history remains screening-grade until primary
  company-report verification is added.
- Sector index/proxy rows remain explicit reviewed peer rows only.
- The NewsWeb daily digest remains on demand; scheduled automation is not part
  of this deployment prep unless separately scoped.
- No recommendation logic or cheap/expensive/fair/neutral standalone multiple
  labels have been added.

## Current Scope

This prep does not add scheduled NewsWeb collection, recommendation logic, or
external publishing. The repo now contains concrete single-host deployment
templates and a public verification script, but an actual production deployment
still requires a real domain/subdomain, DNS access, host credentials, and a
mounted off-host/encrypted backup destination. The app remains a descriptive,
screening-grade research workspace.

## Source References Checked

- SQLite online backup API: https://www.sqlite.org/backup.html
- Caddy automatic HTTPS: https://caddyserver.com/docs/automatic-https
- Caddy reverse proxy directive: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- Tailscale Serve: https://tailscale.com/docs/features/tailscale-serve
- Hetzner cloud pricing docs: https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/
- Render persistent disks: https://render.com/docs/disks
- Fly.io volumes: https://fly.io/docs/volumes/
