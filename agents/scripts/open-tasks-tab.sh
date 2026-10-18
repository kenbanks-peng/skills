#!/bin/sh
set -eu

# Run from the project root.
[ "${HERDR_ENV:-}" = 1 ] || { echo 'HERDR_ENV=1 is required' >&2; exit 1; }
: "${HERDR_WORKSPACE_ID:?Required}"

response=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --label tasks)
pane_id=$(printf '%s' "$response" | jq -er '.result.root_pane.pane_id')

herdr pane run "$pane_id" "aven"
