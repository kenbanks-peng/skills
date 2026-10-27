#!/usr/bin/env bash
# Launch one retained tuios worker pane, or run its host-side wrapper.
set -euo pipefail
scripts=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

if [[ ${1:-} == --worker ]]; then
  [[ $# == 2 ]] || { echo "Usage: $0 --worker ATTEMPT" >&2; exit 2; }
  attempt=$2
  : "${TUIOS_SESSION:?Missing worker session}"
  : "${TUIOS_PANE_ID:?Missing worker pane}"
  tuios set-agent-state working -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \
    --harness pi -m "pi worker running" || true
  printf 'started\n' > "$attempt/pi.started"
  rc=0
  python3 "$scripts/create_container.py" --attempt "$attempt" --launch || rc=$?
  printf '%s\n' "$rc" > "$attempt/pi.exit.tmp"
  mv "$attempt/pi.exit.tmp" "$attempt/pi.exit"
  if [[ $rc == 0 ]]; then
    state="done"
    message="pi exited; dispatcher review required"
  else
    state=errored
    message="pi execution failed: $rc"
  fi
  tuios set-agent-state "$state" -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \
    --harness pi -m "$message" || true
  exit "$rc"
fi

[[ $# == 5 ]] || {
  echo "Usage: $0 SESSION WORKSPACE NAME WORKTREE ATTEMPT" >&2
  exit 2
}
session=$1 workspace=$2 name=$3 worktree=$4 attempt=$5
[[ $session == "${TUIOS_SESSION:?Run from the original tuios session}" ]] || {
  echo "Session mismatch; reconcile before launch" >&2
  exit 1
}
# Refuse another pane launch if an earlier launch may have taken effect.
(set -o noclobber; tuios list-windows -s "$session" --json > "$attempt/panes-before.json")
worker_id=$(tuios new-window -s "$session" "$name" \
  --workspace "$workspace" --cwd "$worktree" --no-focus --keep-open --print-id -- \
  bash "$scripts/launch_worker.sh" --worker "$attempt")
[[ -n $worker_id ]] || { echo "Missing pane ID; reconcile live inventory" >&2; exit 1; }
printf '%s\n' "$worker_id" > "$attempt/worker-pane-id"
printf '%s\n' "$worker_id"
