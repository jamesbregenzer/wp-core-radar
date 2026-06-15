#!/bin/bash
set -euo pipefail

REPO_DIR="/Users/thor/Sites/wp-core-radar"
LOG_PREFIX="[wp-core-radar]"
PYTHON_BIN="/usr/local/opt/python@3.14/bin/python3.14"

# LaunchAgents run with a minimal PATH. Put the Homebrew Python 3.14 bin
# directory first so child scripts that call `python3` use the same runtime
# as this wrapper instead of macOS' system Python.
export PATH="/usr/local/opt/python@3.14/bin:/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHON_BIN

cd "$REPO_DIR"

echo "$LOG_PREFIX Starting scheduled radar update at $(date)"
echo "$LOG_PREFIX Using Python: $("$PYTHON_BIN" --version 2>&1)"
echo "$LOG_PREFIX PATH: $PATH"

git pull --rebase origin main

"$PYTHON_BIN" scripts/run-radar.py

git add data docs reports

if git diff --cached --quiet; then
  echo "$LOG_PREFIX No changes to commit."
else
  git commit -m "Update radar data"

  # Review-only dashboard refreshes may be committed by GitHub Actions while
  # this longer collection job is running. Rebase immediately before pushing so
  # the scheduled collector publishes cleanly instead of failing on a non-fast-forward.
  git pull --rebase origin main
  git push origin main
  echo "$LOG_PREFIX Pushed radar update."
fi

echo "$LOG_PREFIX Finished scheduled radar update at $(date)"
