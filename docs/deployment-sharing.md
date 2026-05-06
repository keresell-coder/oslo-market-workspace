# Deployment And Sharing Prep

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
- `OSLO_APP_REQUIRE_AUTH`: set to `1` to require Basic Auth.
- `OSLO_APP_AUTH_USERNAME`: Basic Auth username.
- `OSLO_APP_AUTH_PASSWORD`: Basic Auth password.
- `OSLO_APP_ALLOW_UNAUTHENTICATED_REMOTE`: set to `1` only when an upstream trusted access layer handles authentication.

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

Before sharing or moving the app, decide where the database should live and how it will be backed up. A custom path can be set with `OSLO_APP_DB_PATH`.

## Current Scope

This prep does not add scheduled NewsWeb collection, recommendation logic, external publishing, or a production deployment target. The app remains a descriptive, screening-grade research workspace.
