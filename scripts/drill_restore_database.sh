#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${OSLO_APP_DB_PATH:-app/data/oslo_workspace.sqlite3}"
BACKUP_DIR="${OSLO_APP_BACKUP_DIR:-$PROJECT_DIR/backups/sqlite}"

if [[ "$DB_PATH" != /* ]]; then
  DB_PATH="$PROJECT_DIR/$DB_PATH"
fi

if [[ "$BACKUP_DIR" != /* ]]; then
  BACKUP_DIR="$PROJECT_DIR/$BACKUP_DIR"
fi

if [[ ! -f "$DB_PATH" ]]; then
  echo "Database not found: $DB_PATH" >&2
  exit 1
fi

before_count="$(find "$BACKUP_DIR" -maxdepth 1 -name '*.sqlite3' 2>/dev/null | wc -l | tr -d ' ')"
backup_output="$("$PROJECT_DIR/scripts/backup_database.sh")"
printf '%s\n' "$backup_output" >/tmp/oslo_restore_drill_backup.log
after_count="$(find "$BACKUP_DIR" -maxdepth 1 -name '*.sqlite3' 2>/dev/null | wc -l | tr -d ' ')"

if [[ "$after_count" -le "$before_count" ]]; then
  cat /tmp/oslo_restore_drill_backup.log >&2
  echo "Backup drill did not create a new backup file." >&2
  exit 1
fi

BACKUP_PATH="$(printf '%s\n' "$backup_output" | sed -n 's/^Backup written: //p' | tail -1)"
if [[ -z "$BACKUP_PATH" || ! -f "$BACKUP_PATH" ]]; then
  cat /tmp/oslo_restore_drill_backup.log >&2
  echo "Could not determine backup path from backup output." >&2
  exit 1
fi
if [[ -f "$BACKUP_PATH.sha256" ]]; then
  shasum -a 256 -c "$BACKUP_PATH.sha256" >/dev/null
fi

SCRATCH="$(mktemp "${TMPDIR:-/tmp}/oslo-restore-drill.XXXXXX.sqlite3")"
rm -f "$SCRATCH"
OSLO_APP_DB_PATH="$SCRATCH" OSLO_APP_PORT="${OSLO_APP_DRILL_PORT:-9876}" "$PROJECT_DIR/scripts/restore_database.sh" "$BACKUP_PATH" >/tmp/oslo_restore_drill_restore.log

python3 - "$DB_PATH" "$SCRATCH" <<'PY'
import sqlite3
import sys
from pathlib import Path

live_path = Path(sys.argv[1])
scratch_path = Path(sys.argv[2])

with sqlite3.connect(scratch_path) as con:
    integrity = con.execute("PRAGMA integrity_check").fetchone()
    if not integrity or integrity[0] != "ok":
        raise SystemExit(f"scratch integrity_check failed: {integrity[0] if integrity else 'no result'}")
    scratch_tables = {
        row[0]
        for row in con.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")
    }

with sqlite3.connect(live_path) as con:
    live_tables = {
        row[0]
        for row in con.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")
    }

missing = sorted(live_tables - scratch_tables)
if missing:
    raise SystemExit(f"scratch restore missing table(s): {', '.join(missing)}")
PY

rm -f "$SCRATCH"

echo "Restore drill passed using backup: $BACKUP_PATH"
