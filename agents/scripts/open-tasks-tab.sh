#!/bin/sh
set -eu

# Run from the project root.
[ "${HERDR_ENV:-}" = 1 ] || { echo 'HERDR_ENV=1 is required' >&2; exit 1; }
: "${HERDR_WORKSPACE_ID:?Required}"

state="${TMPDIR:-/tmp}/herdr-tasks-${HERDR_WORKSPACE_ID}.pane-id"
if [ -e "$state" ]; then
  echo "Tasks pane state already exists: $state; reuse or close it before opening another pane" >&2
  exit 1
fi
response=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --label tasks)
pane_id=$(printf '%s' "$response" | jq -er '.result.root_pane.pane_id')
printf '%s\n' "$pane_id" > "$state"

herdr pane run "$pane_id" "aven --db .aven/tasks.db"
