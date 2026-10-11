#!/bin/sh
set -eu

[ "${HERDR_ENV:-}" = 1 ] || { echo 'HERDR_ENV=1 is required' >&2; exit 1; }
: "${HERDR_WORKSPACE_ID:?Required}"

tabs=$(herdr tab list --workspace "$HERDR_WORKSPACE_ID")
panes=$(herdr pane list --workspace "$HERDR_WORKSPACE_ID")
# Pane names come from their tab labels. Close only the first matching pane.
pane_id=$(printf '%s' "$panes" | jq -r --argjson tabs "$tabs" '
  [$tabs.result.tabs[] | select(.label == "tasks") | .tab_id] as $task_tabs
  | [.result.panes[] | select(.tab_id as $id | $task_tabs | index($id)) | .pane_id]
  | first // empty
')
[ -n "$pane_id" ] || exit 0
herdr pane close "$pane_id"
