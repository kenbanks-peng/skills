#!/bin/bash
set -euo pipefail

if [ "${1:-}" = --help ]; then
  echo 'Startup Aven tabs are run-owned and survive worker cleanup.'
  echo 'Review the dispatch-ui run record and close the verified tab manually in the original UI.'
  exit 0
fi
echo 'Refusing legacy label/ID-only closure: Aven tabs are run-owned, not worker resources.' >&2
echo 'Review the saved dispatch-ui JSON identity in the original UI before manual closure.' >&2
exit 1
