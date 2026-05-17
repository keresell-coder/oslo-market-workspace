#!/usr/bin/env bash
set -euo pipefail

URL="${1:-${OSLO_PUBLIC_URL:-}}"
USERNAME="${OSLO_PUBLIC_AUTH_USERNAME:-${OSLO_APP_AUTH_USERNAME:-}}"
PASSWORD="${OSLO_PUBLIC_AUTH_PASSWORD:-${OSLO_APP_AUTH_PASSWORD:-}}"
REFRESH_SYMBOL="${OSLO_VERIFY_REFRESH_SYMBOL:-MOWI.OL}"
VERIFY_REFRESH="${OSLO_VERIFY_REFRESH:-1}"

if [[ -z "$URL" ]]; then
  echo "Usage: OSLO_PUBLIC_URL=https://research.example.com scripts/verify_public_deployment.sh" >&2
  echo "Optional auth: OSLO_PUBLIC_AUTH_USERNAME and OSLO_PUBLIC_AUTH_PASSWORD" >&2
  echo "Optional refresh controls: OSLO_VERIFY_REFRESH=0 to skip refresh smoke checks, OSLO_VERIFY_REFRESH_SYMBOL=MOWI.OL to choose the fundamentals/benchmark symbol" >&2
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

curl_json() {
  local url="$1"
  if [[ "${#AUTH_ARGS[@]}" -gt 0 ]]; then
    curl -fsS "${AUTH_ARGS[@]}" "$url"
  else
    curl -fsS "$url"
  fi
}

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/oslo-public-verify.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Checking health endpoint..."
curl_json "$URL/api/health" | python3 -m json.tool > "$TMP_DIR/health.json"

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
  curl_json "$URL$path" | python3 -m json.tool > "$TMP_DIR/$name.json"
}

check_json "/api/watchlist-overview" "watchlist-overview"
check_json "/api/fundamentals?symbols=MOWI.OL" "fundamentals-mowi"
check_json "/api/technical-indicators?universe=watchlist" "technical-indicators"
check_json "/api/event-monitoring" "event-monitoring"

if [[ "$VERIFY_REFRESH" != "0" ]]; then
  echo "Checking hosted true-refresh paths..."
  check_json "/api/watchlist-overview?refresh=1" "refresh-watchlist-overview"
  check_json "/api/fundamentals?symbols=${REFRESH_SYMBOL}&refresh=1" "refresh-fundamentals"
  check_json "/api/technical-indicators?universe=watchlist&refresh=1" "refresh-technical-indicators"
  check_json "/api/event-monitoring?refresh=1" "refresh-event-monitoring"
  check_json "/api/benchmarks?symbol=${REFRESH_SYMBOL}&refresh=1" "refresh-benchmarks"
fi

python3 - "$TMP_DIR/health.json" "$URL" <<'PY'
import json
import os
import sys
from pathlib import Path

health = json.loads(Path(sys.argv[1]).read_text())
url = sys.argv[2]
sharing = health.get("sharing") or {}
problems = []
if not health.get("ok"):
    problems.append("health ok flag is missing")
hosted_checks_required = not (os.environ.get("OSLO_ALLOW_HTTP_VERIFY") == "1" and url.startswith("http://"))
if hosted_checks_required:
    if not sharing.get("authRequired"):
        problems.append("health sharing.authRequired is not true")
    if not sharing.get("databasePathConfigured"):
        problems.append("health sharing.databasePathConfigured is not true")
    if not sharing.get("localOnly"):
        problems.append("health sharing.localOnly is not true; app may not be bound to localhost")
if problems:
    raise SystemExit("; ".join(problems))
PY

if [[ "$VERIFY_REFRESH" != "0" ]]; then
  python3 - "$TMP_DIR" "$REFRESH_SYMBOL" <<'PY'
import json
import sys
from pathlib import Path

tmp_dir = Path(sys.argv[1])
refresh_symbol = sys.argv[2]


def load(name: str) -> dict:
    return json.loads((tmp_dir / f"{name}.json").read_text())


def as_list(value) -> list:
    return value if isinstance(value, list) else []


def collect_statuses(value, statuses: set[str] | None = None, errors: list[str] | None = None) -> tuple[set[str], list[str]]:
    if statuses is None:
        statuses = set()
    if errors is None:
        errors = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {
                "cacheStatus",
                "sourceStatus",
                "refreshStatus",
                "fetchStatus",
            } and isinstance(item, str):
                statuses.add(item)
            if key in {
                "error",
                "sourceError",
                "sourceRefreshError",
                "technicalError",
                "screenerError",
            } and item:
                errors.append(str(item))
            else:
                collect_statuses(item, statuses, errors)
    elif isinstance(value, list):
        for item in value:
            collect_statuses(item, statuses, errors)
    return statuses, errors


problems: list[str] = []
summaries: list[str] = []

watchlist = load("refresh-watchlist-overview")
if watchlist.get("refreshRequested") is not True:
    problems.append("watchlist refresh endpoint did not mark refreshRequested=true")
watchlist_rows = as_list(watchlist.get("rows"))
if not watchlist_rows:
    problems.append("watchlist refresh returned no rows")
watchlist_statuses, watchlist_errors = collect_statuses(watchlist)
summaries.append(
    f"watchlist refresh rows={len(watchlist_rows)} "
    f"statuses={','.join(sorted(watchlist_statuses)) or 'none'} "
    f"errors={len(watchlist_errors)}"
)

fundamentals = load("refresh-fundamentals")
fundamental_rows = as_list(fundamentals.get("rows"))
if not fundamental_rows:
    problems.append(f"fundamentals refresh returned no rows for {refresh_symbol}")
fundamental_statuses, fundamental_errors = collect_statuses(fundamentals)
summaries.append(
    f"fundamentals refresh rows={len(fundamental_rows)} "
    f"statuses={','.join(sorted(fundamental_statuses)) or 'none'} "
    f"errors={len(fundamental_errors)}"
)

technical = load("refresh-technical-indicators")
technical_rows = as_list(technical.get("rows"))
if not technical_rows:
    problems.append("technical indicators refresh returned no rows")
technical_statuses, technical_errors = collect_statuses(technical)
summaries.append(
    f"technical refresh rows={len(technical_rows)} "
    f"statuses={','.join(sorted(technical_statuses)) or 'none'} "
    f"errors={len(technical_errors)}"
)

events = load("refresh-event-monitoring")
event_rows = as_list(events.get("rows"))
event_errors = as_list(events.get("errors"))
coverage = events.get("coverage") if isinstance(events.get("coverage"), dict) else {}
newsweb_fetch = coverage.get("newswebFetch") if isinstance(coverage.get("newswebFetch"), dict) else {}
event_statuses, event_nested_errors = collect_statuses(events)
if event_errors:
    event_nested_errors.extend(str(error) for error in event_errors)
summaries.append(
    f"event refresh rows={len(event_rows)} "
    f"freshSymbols={newsweb_fetch.get('freshSymbols', 'n/a')} "
    f"staleSymbols={newsweb_fetch.get('staleSymbols', 'n/a')} "
    f"errorSymbols={newsweb_fetch.get('errorSymbols', 'n/a')} "
    f"statuses={','.join(sorted(event_statuses)) or 'none'} "
    f"errors={len(event_nested_errors)}"
)

benchmarks = load("refresh-benchmarks")
if benchmarks.get("symbol") != refresh_symbol:
    problems.append(f"benchmark refresh did not return requested symbol {refresh_symbol}")
benchmark_statuses, benchmark_errors = collect_statuses(benchmarks)
summaries.append(
    f"benchmark refresh symbol={benchmarks.get('symbol', 'missing')} "
    f"statuses={','.join(sorted(benchmark_statuses)) or 'none'} "
    f"errors={len(benchmark_errors)}"
)

if problems:
    raise SystemExit("; ".join(problems))

print("Refresh verification summary:")
for summary in summaries:
    print(f"- {summary}")
print("Visible cached/stale/error source states are allowed here when the endpoint returns usable JSON and keeps the state explicit.")
PY
fi

echo "Public deployment verification passed for $URL"
