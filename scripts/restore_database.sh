#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${OSLO_APP_DB_PATH:-app/data/oslo_workspace.sqlite3}"
BACKUP_DIR="${OSLO_APP_BACKUP_DIR:-$PROJECT_DIR/backups/sqlite}"
PORT="${OSLO_APP_PORT:-8765}"

if [[ "$DB_PATH" != /* ]]; then
  DB_PATH="$PROJECT_DIR/$DB_PATH"
fi

if [[ "$BACKUP_DIR" != /* ]]; then
  BACKUP_DIR="$PROJECT_DIR/$BACKUP_DIR"
fi

if [[ $# -ne 1 ]]; then
  echo "Usage: scripts/restore_database.sh <backup.sqlite3>" >&2
  exit 1
fi

SOURCE="$1"
if [[ "$SOURCE" != /* ]]; then
  SOURCE="$PROJECT_DIR/$SOURCE"
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "Backup not found: $SOURCE" >&2
  exit 1
fi

if [[ "${OSLO_APP_FORCE_RESTORE:-0}" != "1" ]] && command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | grep -q "Python"; then
    echo "A Python server appears to be listening on port $PORT." >&2
    echo "Stop the app before restoring, or set OSLO_APP_FORCE_RESTORE=1 if you have already handled it." >&2
    exit 1
  fi
fi

python3 - "$SOURCE" <<'PY'
import sqlite3
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
with sqlite3.connect(source_path) as con:
    result = con.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"backup integrity_check failed: {result[0] if result else 'no result'}")
PY

mkdir -p "$(dirname "$DB_PATH")" "$BACKUP_DIR"

if [[ -f "$DB_PATH" ]]; then
  STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
  CURRENT_BACKUP="$BACKUP_DIR/pre_restore.$STAMP.sqlite3"
  python3 - "$DB_PATH" "$CURRENT_BACKUP" <<'PY'
import sqlite3
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])
with sqlite3.connect(source_path) as source, sqlite3.connect(target_path) as target:
    source.backup(target)
with sqlite3.connect(target_path) as con:
    result = con.execute("PRAGMA integrity_check").fetchone()
    if not result or result[0] != "ok":
        raise SystemExit(f"pre-restore backup integrity_check failed: {result[0] if result else 'no result'}")
PY
  shasum -a 256 "$CURRENT_BACKUP" > "$CURRENT_BACKUP.sha256"
  echo "Pre-restore backup written: $CURRENT_BACKUP"
fi

TMP="$DB_PATH.restore.$$"
cp "$SOURCE" "$TMP"
mv "$TMP" "$DB_PATH"

echo "Database restored to: $DB_PATH"
