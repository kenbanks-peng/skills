#!/bin/bash
set -euo pipefail

if [ "${1:-}" = --help ]; then
  echo 'Usage: close-tasks-tab.sh <run-task> [--run-id <id>] --authorize-close'
  echo 'Close the saved run-owned Aven tab only after all work and final reporting finish.'
  exit 0
fi
if [ "$#" -eq 0 ] || [[ "$1" == *:* ]]; then
  echo 'Aven tabs are run-owned; supply the run task and --authorize-close, not a label or pane ID.' >&2
  exit 1
fi
exec python3 "$(dirname "$0")/dispatch.py" close-run "$@"
