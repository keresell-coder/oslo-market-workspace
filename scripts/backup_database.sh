#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="${OSLO_APP_DB_PATH:-app/data/oslo_workspace.sqlite3}"
BACKUP_DIR="${OSLO_APP_BACKUP_DIR:-$PROJECT_DIR/backups/sqlite}"
MIRROR_DIR="${OSLO_APP_BACKUP_MIRROR_DIR:-}"

if [[ "$DB_PATH" != /* ]]; then
  DB_PATH="$PROJECT_DIR/$DB_PATH"
fi

if [[ "$BACKUP_DIR" != /* ]]; then
  BACKUP_DIR="$PROJECT_DIR/$BACKUP_DIR"
fi

if [[ -n "$MIRROR_DIR" && "$MIRROR_DIR" != /* ]]; then
  MIRROR_DIR="$PROJECT_DIR/$MIRROR_DIR"
fi

if [[ ! -f "$DB_PATH" ]]; then
  echo "Database not found: $DB_PATH" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
DB_NAME="$(basename "$DB_PATH")"
OUT="$BACKUP_DIR/${DB_NAME%.sqlite3}.$STAMP.sqlite3"
TMP="$OUT.tmp"

rm -f "$TMP"

python3 - "$DB_PATH" "$TMP" <<'PY'
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
        raise SystemExit(f"integrity_check failed: {result[0] if result else 'no result'}")
PY

mv "$TMP" "$OUT"
shasum -a 256 "$OUT" > "$OUT.sha256"

echo "Backup written: $OUT"
echo "Checksum written: $OUT.sha256"

if [[ -n "$MIRROR_DIR" ]]; then
  mkdir -p "$MIRROR_DIR"
  cp "$OUT" "$OUT.sha256" "$MIRROR_DIR/"
  echo "Mirror copy written: $MIRROR_DIR/$(basename "$OUT")"
fi
