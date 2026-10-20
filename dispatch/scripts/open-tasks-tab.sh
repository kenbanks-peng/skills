#!/bin/bash
set -euo pipefail

# One adapter and saved run identity for startup, repeat setup, and resume.
if [ "${1:-}" = --help ]; then
  echo 'Usage: open-tasks-tab.sh TASK_REF [--run-id ID] [--db PATH] [--workspace KEY]'
  echo 'Run from the target repository (subdirectories are supported).'
  echo 'Delegates to dispatch.py startup; returns a saved JSON run record.'
  exit 0
fi
exec python3 "$(dirname "$0")/dispatch.py" startup "$@"
