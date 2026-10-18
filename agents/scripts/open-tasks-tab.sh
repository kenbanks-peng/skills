#!/bin/sh
set -eu

project_dir=${1:?Usage: open-tasks-tab.sh ABSOLUTE_PROJECT_DIR}
case "$project_dir" in
  /*) ;;
  *) echo 'Project directory must be absolute' >&2; exit 1 ;;
esac
project_dir=$(cd "$project_dir" && pwd -P)
if [ "${HERDR_ENV:-}" = 1 ]; then
  : "${HERDR_WORKSPACE_ID:?Required}"
  response=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$project_dir" --label tasks)
  pane_id=$(printf '%s' "$response" | jq -er '.result.root_pane.pane_id')
  herdr pane run "$pane_id" "aven"
elif [ -n "${TMUX:-}" ]; then
  session_id=$(tmux display-message -p '#{session_id}')
  tmux new-window -d -t "$session_id:" -n tasks -c "$project_dir" aven
else
  echo 'An active Herdr or tmux session is required' >&2
  exit 1
fi
