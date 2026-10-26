# Container procedure (required)

Use this procedure for every worker and every integration-check container.
Supported runtime: Apple `container` on macOS, selected by the installed `linux`
configuration. Do not substitute Docker, change the image, or invent an adapter.

## Create and identify

Set `skill` to this skill's absolute directory. Set `attempt` to a new directory
under the run record and `worktree` to the checkout to mount. Both must exist.
Run all commands on the host in Bash with `set -euo pipefail`.

```sh
python3 "$skill/scripts/create_container.py" --worktree "$worktree" --attempt "$attempt"
```

The helper calls `linux container -dry-run` with the worktree as cwd and the common
Git directory mounted at the same path. It preserves the configured image,
user, environment, memory, CPUs, and mounts. It adds the attempt mount when needed.
It passes the host Git author/committer identities and sets process-scoped
`safe.directory` to this exact checkout for Apple file-mount ownership. It does
not edit Git configuration or trust a wildcard. It replaces the random name with
a saved ID, removes auto-delete/TTY flags, and calls `container create` with
`sleep infinity`. It does **not** start pi.
The intent is saved before creation; a second create on that directory is refused.
Resolved environment values are not saved.

Load the canonical paths from the receipt. Host symlinks such as `/var` versus
`/private/var` are not interchangeable guest paths:

```sh
cid=$(jq -er '.id' "$attempt/container.json")
owner=$(jq -er '.owner' "$attempt/container.json")
worktree=$(jq -er '.worktree' "$attempt/container.json")
common_git=$(jq -er '.common_git' "$attempt/container.json")
attempt=$(jq -er '.attempt' "$attempt/container.json")

owned_state() {
  container inspect "$cid" | jq -er \
    --arg id "$cid" --arg owner "$owner" \
    --arg worktree "$worktree" --arg common "$common_git" '
      if length == 1
        and .[0].configuration.id == $id
        and .[0].configuration.labels["dispatch.owner"] == $owner
        and .[0].configuration.initProcess.workingDirectory == $worktree
        and any(.[0].configuration.mounts[];
          .source == $worktree and .destination == $worktree)
        and any(.[0].configuration.mounts[];
          .source == $common and .destination == $common)
      then .[0].status.state
      else error("container ownership or mount mismatch")
      end'
}
```

Call `owned_state` before every start, exec, stop, or delete. Any mismatch or
runtime error stops the procedure. Do not save full inspect output: it includes
environment values. The label is an ownership check, not a security boundary.

## Start and preflight

```sh
test "$(owned_state)" = stopped
container start "$cid"
test "$(owned_state)" = running
container exec --workdir "$worktree" "$cid" bash -eu -c '
  test "$(git rev-parse --show-toplevel)" = "$1"
  test -w "$2"
  command -v pi
  pi --version
  git var GIT_AUTHOR_IDENT >/dev/null
  git var GIT_COMMITTER_IDENT >/dev/null
' _ "$worktree" "$attempt" > "$attempt/preflight.log" 2>&1
```

A failed Git identity check is a blocker. Do not invent an identity or alter Git
configuration. Have the person configure it. If credentials or tools are missing,
report the exact failure; do not change the image or mount host secrets.

## Launch pi through tuios

Before this step, the dispatcher must save the rendered `prompt.md`, task
`context.md`, and executable check content in `checks.sh` in the attempt directory.
The check script must start with `set -euo pipefail`. It must contain the agreed
commands, not commands taken from worker reports.

Write a launch-intent note to aven and mark the task and epic active **before**
starting pi. Record the pane inventory before creation. Launch only once:

```sh
test "$(owned_state)" = running
tuios list-windows -s "$session" --json > "$attempt/panes-before.json"
worker_id=$(tuios new-window -s "$session" "$worker_name" \
  --workspace 1 --cwd "$worktree" --no-focus --keep-open --print-id -- \
  bash -c '
    set +e
    tuios set-agent-state working -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \\
      --harness pi -m "pi worker running"
    container exec --workdir "$1" "$2" bash -eu -c '\''
      cd "$1"
      printf "started\\n" > "$2/pi.started"
      exec pi --session "$2/pi.jsonl" --print -- "@$2/prompt.md"
    '\'' _ "$1" "$3"
    rc=$?
    printf "%s\\n" "$rc" > "$3/pi.exit.tmp"
    mv "$3/pi.exit.tmp" "$3/pi.exit"
    if [ "$rc" -eq 0 ]; then
      tuios set-agent-state done -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \\
        --harness pi -m "pi exited; dispatcher review required"
    else
      tuios set-agent-state errored -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \\
        --harness pi -m "pi execution failed: $rc"
    fi
    exit "$rc"
  ' _ "$worktree" "$cid" "$attempt")
printf '%s\n' "$worker_id" > "$attempt/worker-pane-id"
```

The host wrapper reports its own tuios state and writes `pi.exit` only after
`container exec` returns. UI state is not acceptance evidence. No tuios socket
or integration hooks are needed inside the container. The container stays
running so the dispatcher can inspect and check the work.

If pane creation output is lost, compare `panes-before.json` with the live pane
inventory and inspect the recorded container. Do not create a second pane on the
basis of a missing pane-ID file. Stop for reconciliation if identity is uncertain.

## Wait and check

```sh
tuios wait-for window-exit -s "$session" -w "$worker_id" --timeout 600000
test -f "$attempt/pi.started"
test "$(cat "$attempt/pi.exit")" = 0
test -s "$attempt/report.md"
```

A timeout leaves work outstanding. Capture at most 80 lines for diagnosis.
A missing exit file means unknown execution state, not success. Read the report,
then inspect the actual diff. A nonzero exit or BLOCKED report leaves the task
active. For a successful report, run the dispatcher-owned checks:

```sh
test "$(owned_state)" = running
if container exec --workdir "$worktree" "$cid" \
  bash "$attempt/checks.sh" > "$attempt/checks.log" 2>&1; then
  printf '0\n' > "$attempt/checks.exit"
else
  rc=$?
  printf '%s\n' "$rc" > "$attempt/checks.exit"
  exit "$rc"
fi
```

Require checks.exit = 0. Record the reviewed Git HEAD and ensure the source tree
is clean after checks. Then stop the container **before** merging:

```sh
test "$(owned_state)" = running
container stop --time 10 "$cid"
test "$(owned_state)" = stopped
```

A stopped container proves its processes cannot write. Pane exit alone does not.
After stopping, re-read HEAD, diff, and cleanliness on the host; they must match
the reviewed state. Keep the stopped container until delivery is verified.

## Integration checks

After a merge, create a new directory `integration-N` under the run record.
Copy the agreed integration commands into its `checks.sh`. Run integration-container
commands in a Bash subshell `( ... )` so the worker variables are not overwritten.
Use this same create, load, ownership, start, and check procedure with:
- `attempt` = the new integration directory;
- `worktree` = the target checkout (`repo`), **not** the worker checkout.

Do not run pi in an integration container. Save target HEAD before checks, stop
the container after checks, and require the target HEAD to be unchanged and
`git status --porcelain=v1 --untracked-files=all` to be empty. Delete the stopped
integration container with the procedure below. Keep its logs and receipt.

Checks that fail after merge leave the task active. Do not reset the target or
mark it done. Record the delivered SHA and failure, then correct the problem on
a worker branch and repeat review and integration.

## Delete or recover

Delete only a verified, stopped, run-owned container:

```sh
test "$(owned_state)" = stopped
container delete "$cid"
container list --all --format json | jq -e --arg id "$cid" \
  'all(.[]; .id != $id)' >/dev/null
```

For a timeout or an interrupted run, load the saved receipt and call
`owned_state`. If running, leave it alone while inspecting outstanding work.
To cancel the worker or stop an abandoned execution, first record the cancellation
or blocker in aven, then run `container stop --time 10 "$cid"` and confirm stopped.
Do not restart pi automatically. Save a fresh attempt for any retry.

If inspect fails, run the exact list command above. A successful list that
excludes the ID proves absence; a connection failure does not. If create intent
exists but no container exists, retain that attempt as failed and use a new
attempt. Never repeat create, infer identity by a name prefix, or stop/delete
another container. Never use `--all` on stop/delete, or use `--force`, `clean`,
or `prune`.
