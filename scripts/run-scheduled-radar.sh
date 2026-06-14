#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/thor/Sites/wp-core-radar"
LOG_PREFIX="[wp-core-radar]"
PYTHON_BIN="/usr/local/opt/python@3.14/bin/python3.14"

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

cd "$REPO_DIR"

echo "$LOG_PREFIX Starting scheduled radar update at $(date)"

git pull --rebase origin main

"$PYTHON_BIN" scripts/run-radar.py

git add data docs reports

if git diff --cached --quiet; then
  echo "$LOG_PREFIX No changes to commit."
else
  git commit -m "Update radar data"
  git push origin main
  echo "$LOG_PREFIX Pushed radar update."
fi

echo "$LOG_PREFIX Finished scheduled radar update at $(date)"
