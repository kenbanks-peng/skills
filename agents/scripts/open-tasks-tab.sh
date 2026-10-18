#!/bin/sh
set -eu

project_dir=${1:?Usage: open-tasks-tab.sh ABSOLUTE_PROJECT_DIR}
case "$project_dir" in
  /*) ;;
  *) echo 'Project directory must be absolute' >&2; exit 1 ;;
esac
project_dir=$(cd "$project_dir" && pwd -P)
[ "${HERDR_ENV:-}" = 1 ] || { echo 'HERDR_ENV=1 is required' >&2; exit 1; }
: "${HERDR_WORKSPACE_ID:?Required}"

response=$(herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "$project_dir" --label tasks)
pane_id=$(printf '%s' "$response" | jq -er '.result.root_pane.pane_id')

herdr pane run "$pane_id" "aven"
