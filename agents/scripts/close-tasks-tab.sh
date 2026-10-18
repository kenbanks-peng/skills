#!/bin/sh
set -eu

if [ "${HERDR_ENV:-}" != 1 ]; then
  if [ -n "${TMUX:-}" ]; then
    session_id=$(tmux display-message -p '#{session_id}')
    windows=$(tmux list-windows -t "$session_id" -F '#{window_id} #{window_name}')
    window_id=$(printf '%s\n' "$windows" | awk '$2 == "tasks" { print $1; exit }')
    [ -n "$window_id" ] || exit 0
    tmux kill-window -t "$window_id"
    exit 0
  fi
  echo 'An active Herdr or tmux session is required' >&2
  exit 1
fi
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
