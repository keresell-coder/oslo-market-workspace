#!/usr/bin/env bash
set -euo pipefail

URL="${1:-${OSLO_PUBLIC_URL:-}}"
USERNAME="${OSLO_PUBLIC_AUTH_USERNAME:-${OSLO_APP_AUTH_USERNAME:-}}"
PASSWORD="${OSLO_PUBLIC_AUTH_PASSWORD:-${OSLO_APP_AUTH_PASSWORD:-}}"

if [[ -z "$URL" ]]; then
  echo "Usage: OSLO_PUBLIC_URL=https://research.example.com scripts/verify_public_deployment.sh" >&2
  echo "Optional auth: OSLO_PUBLIC_AUTH_USERNAME and OSLO_PUBLIC_AUTH_PASSWORD" >&2
  exit 1
fi

URL="${URL%/}"
if [[ "$URL" != https://* && "${OSLO_ALLOW_HTTP_VERIFY:-0}" != "1" ]]; then
  echo "Refusing public verification without HTTPS: $URL" >&2
  echo "Set OSLO_ALLOW_HTTP_VERIFY=1 only for local/private dry runs." >&2
  exit 1
fi

AUTH_ARGS=()
if [[ -n "$USERNAME" || -n "$PASSWORD" ]]; then
  if [[ -z "$USERNAME" || -z "$PASSWORD" ]]; then
    echo "Both username and password are required when auth verification is enabled." >&2
    exit 1
  fi
  AUTH_ARGS=(-u "$USERNAME:$PASSWORD")
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/oslo-public-verify.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Checking health endpoint..."
curl -fsS "${AUTH_ARGS[@]}" "$URL/api/health" | python3 -m json.tool > "$TMP_DIR/health.json"

if [[ "${#AUTH_ARGS[@]}" -gt 0 ]]; then
  echo "Checking unauthenticated access is blocked..."
  status="$(curl -sS -o "$TMP_DIR/unauth.out" -w "%{http_code}" "$URL/" || true)"
  if [[ "$status" != "401" ]]; then
    echo "Expected unauthenticated app access to return 401, got $status" >&2
    exit 1
  fi
fi

check_json() {
  local path="$1"
  local name="$2"
  echo "Checking $name..."
  curl -fsS "${AUTH_ARGS[@]}" "$URL$path" | python3 -m json.tool > "$TMP_DIR/$name.json"
}

check_json "/api/watchlist-overview" "watchlist-overview"
check_json "/api/fundamentals?symbols=MOWI.OL" "fundamentals-mowi"
check_json "/api/technical-indicators?universe=watchlist" "technical-indicators"
check_json "/api/event-monitoring" "event-monitoring"

python3 - "$TMP_DIR/health.json" <<'PY'
import json
import sys
from pathlib import Path

health = json.loads(Path(sys.argv[1]).read_text())
sharing = health.get("sharing") or {}
problems = []
if not health.get("ok"):
    problems.append("health ok flag is missing")
if not sharing.get("authRequired"):
    problems.append("health sharing.authRequired is not true")
if not sharing.get("databasePathConfigured"):
    problems.append("health sharing.databasePathConfigured is not true")
if not sharing.get("localOnly"):
    problems.append("health sharing.localOnly is not true; app may not be bound to localhost")
if problems:
    raise SystemExit("; ".join(problems))
PY

echo "Public deployment verification passed for $URL"
