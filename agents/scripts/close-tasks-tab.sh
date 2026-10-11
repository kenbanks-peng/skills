#!/bin/sh
set -eu

[ "${HERDR_ENV:-}" = 1 ] || { echo 'HERDR_ENV=1 is required' >&2; exit 1; }
: "${HERDR_WORKSPACE_ID:?Required}"

state="${TMPDIR:-/tmp}/herdr-tasks-${HERDR_WORKSPACE_ID}.pane-id"
pane_id=$(cat "$state")
herdr pane close "$pane_id"
rm "$state"
