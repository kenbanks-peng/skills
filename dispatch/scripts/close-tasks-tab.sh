#!/bin/bash
set -euo pipefail

if [ "${1:-}" = --help ]; then
  echo 'Usage: close-tasks-tab.sh herdr:PANE_ID|tmux:WINDOW_ID'
  echo 'Closes only the recorded resource from open-tasks-tab.sh in the original multiplexer.'
  exit 0
fi

resource=${1:?Usage: close-tasks-tab.sh herdr:PANE_ID|tmux:WINDOW_ID}
case "$resource" in
  herdr:*)
    [ "${HERDR_ENV:-}" = 1 ] || { echo 'Original Herdr environment required' >&2; exit 1; }
    pane_id=${resource#herdr:}
    case "$pane_id" in
      ''|-*) echo 'Invalid Herdr pane ID' >&2; exit 1 ;;
    esac
    herdr pane close "$pane_id"
    ;;
  tmux:*)
    [ "${HERDR_ENV:-}" != 1 ] && [ -n "${TMUX:-}" ] || { echo 'Original tmux environment required' >&2; exit 1; }
    window_id=${resource#tmux:}
    if [[ ! "$window_id" =~ ^@[0-9]+$ ]]; then
      echo 'Expected an exact tmux window ID (@number)' >&2
      exit 1
    fi
    tmux kill-window -t "$window_id"
    ;;
  *) echo 'Expected a recorded herdr:PANE_ID or tmux:WINDOW_ID' >&2; exit 1 ;;
esac
