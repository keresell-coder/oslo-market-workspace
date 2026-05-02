#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="127.0.0.1"
PORT="8765"
URL="http://${HOST}:${PORT}"

if ! lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  RUNNER="${TMPDIR:-/tmp}/oslo-stock-web-app.command"
  {
    printf '#!/usr/bin/env bash\n'
    printf 'cd %q\n' "$PROJECT_DIR"
    printf 'python3 app/server.py\n'
  } > "$RUNNER"
  chmod +x "$RUNNER"
  open -a Terminal "$RUNNER"

  for _ in {1..20}; do
    if curl -fsS "${URL}/api/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

curl -fsS "${URL}/api/health" >/dev/null
open -a Safari "$URL"
printf 'Oslo Stock web-app is available in Safari at %s\n' "$URL"
