#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/keresell-coder/oslo-market-workspace.git"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"

if [ ! -d .git ] || [ ! -f .git/HEAD ]; then
  git init -b main
fi

git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
git push -u origin main

