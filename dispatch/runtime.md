# Container procedure (required)

Use this procedure for every worker and check container. Use Apple container
through the installed `linux` command, not Docker. Run `linux skill` and read
its instructions before container operations. Except for `launch`, `config`,
and `skill`, linux passes arguments through to Apple `container`.
Keep the configured image,
resources, user, and mounts unless the user authorizes a change.
The worker command is `linux launch --name <NAME> -it -- pi`, with the
mount, Git identity, and pi session options described below. Do not create a
sleep container and then exec pi into it.

## Create and identify

Set `skill` to this skill's absolute directory. Set `attempt` to a new directory
under the run record and `worktree` to the checkout. Both must exist.
Run host commands in Bash with `set -euo pipefail`.

```sh
python3 "$skill/scripts/create_container.py" --worktree "$worktree" --attempt "$attempt"
cid=$(jq -er '.id' "$attempt/container.json")
worktree=$(jq -er '.worktree' "$attempt/container.json")
common_git=$(jq -er '.common_git' "$attempt/container.json")
attempt=$(jq -er '.attempt' "$attempt/container.json")
linux config validate
linux list --all --format json | jq -e --arg id "$cid" \
  'all(.[]; .id != $id)' >/dev/null
```

The helper now only prepares a receipt. It does not create or start a container.
It saves a unique name and canonical paths with mode 0600. A second preparation
in that directory is refused. Save this name in run.json before launch.
Host symlinks such as `/var` and `/private/var` are not interchangeable guest paths.

With `--launch`, the helper runs `linux launch --name "$cid" -it -- pi ...`
from the worktree. It adds writable mounts for the common Git directory and,
when needed, the attempt directory. Linux mounts the current checkout and
selects its working directory. The helper passes the host Git author/committer
identities and process-scoped `safe.directory` for this exact checkout.
It does not edit shared Git configuration, trust a wildcard, use `--rm`, or save
environment values. It saves launch intent before calling linux and refuses
another launch after that point, including after failure.

Define the ownership check on the host:

```sh
owned_state() {
  linux inspect "$cid" | jq -er \
    --arg id "$cid" --arg worktree "$worktree" --arg common "$common_git" '
      if length == 1
        and .[0].configuration.id == $id
        and .[0].configuration.initProcess.workingDirectory == $worktree
        and any(.[0].configuration.mounts[];
          .source == $worktree and .destination == $worktree)
        and any(.[0].configuration.mounts[];
          .source == $common and .destination == $common)
      then .[0].status.state
      else error("container identity or mount mismatch")
      end'
}
```

Require the saved launch intent as well as matching live identity and mounts.
Call `owned_state` before exec, stop, or delete. A mismatch blocks operations.
Do not save full inspect output, which can contain secrets. Never infer
ownership from a name prefix. An uncertain identity blocks destructive cleanup.

## Launch pi through tuios

Before launch, save rendered `prompt.md`, task `context.md`, and dispatcher-owned
`checks.sh` in the attempt directory. The check script must start with
`set -euo pipefail` and contain the commands selected before launch.

Write a launch-intent note to aven and mark the task and epic active first.
Use the saved orchestrator session and allocated workspace. Verify both in live
inventory. Do not create a separate session. Name the window exactly
`workspace_name`. Before a retry, confirm the previous container is stopped,
then close only its owned worker pane. Record the pane inventory before creation.
Launch only once:

```sh
tuios list-windows -s "$session" --json > "$attempt/panes-before.json"
worker_id=$(tuios new-window -s "$session" "$workspace_name" \
  --workspace "$workspace" --cwd "$worktree" --no-focus --keep-open --print-id -- \
  bash -c '
    set +e
    tuios set-agent-state working -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \
      --harness pi -m "pi worker running"
    printf "started\n" > "$3/pi.started"
    python3 "$4/scripts/create_container.py" --attempt "$3" --launch
    rc=$?
    printf "%s\n" "$rc" > "$3/pi.exit.tmp"
    mv "$3/pi.exit.tmp" "$3/pi.exit"
    if [ "$rc" -eq 0 ]; then
      tuios set-agent-state done -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \
        --harness pi -m "pi exited; dispatcher review required"
    else
      tuios set-agent-state errored -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" \
        --harness pi -m "pi execution failed: $rc"
    fi
    exit "$rc"
  ' _ "$worktree" "$cid" "$attempt" "$skill")
printf '%s\n' "$worker_id" > "$attempt/worker-pane-id"
```

The host wrapper writes `pi.exit` only after linux returns. The `pi.started`
file records the launch attempt, not proof that pi ran. Confirm the live
container with `owned_state` and inspect the pane before reporting a running
worker. While running, use `linux exec "$cid" ...` for read-only preflight:
confirm the checkout path, writable attempt path, pi version, and Git identities.
Repair missing tools or configuration within authorization. Do not invent a Git
identity or mount secrets without permission.

Pi uses its regular interactive TUI. A completed turn does not exit pi.
UI state is not acceptance evidence. No tuios socket is needed in the container.
If pane creation output is lost, compare saved and live inventories and inspect
the saved container. Do not create another pane because its ID file is missing.

## Wait and check

1. Check for a final, nonempty `attempt/report.md`. Temporary files or terminal
   text are not report-ready signals.
2. If absent, use bounded tuios waits, then check again. On timeout, visit other
   workers. Do not sleep and capture in a loop. Do not wait for window exit
   while pi is open.
3. Read the report and verify task and attempt IDs. Inspect the owned pane to
   confirm the final response has ended and pi is idle, with no tool running
   or approval request. A report alone does not prove the turn ended.
4. Verify pane identity, then send Ctrl+D to the idle pi TUI. Never send exit
   keys or answer a prompt while a worker is active.

```sh
tuios wait-for window-exit -s "$session" -w "$worker_id" --timeout 600000
test -f "$attempt/pi.started"
test "$(cat "$attempt/pi.exit")" = 0
test -s "$attempt/report.md"
test "$(owned_state)" = stopped
```

Pi is the container's main process. Its exit stops the container; it does not
leave a sleep process for later exec. Confirm stopped state before review or
checks. If still running, diagnose it, then stop the exact owned container when
safe with `linux stop --time 10 "$cid"` and confirm stopped.
A timeout or missing exit file means unknown state, not success. Capture at most
80 lines for diagnosis. Nonzero exit or a BLOCKED report leaves the task active.

Record the reviewed Git HEAD and inspect the diff. Run dispatcher-owned checks
in a new check container with the procedure below, using the worker checkout.
Require a zero exit, unchanged reviewed HEAD, and a clean tree under the Aven-file
exception in SKILL.md. Keep the stopped worker until delivery is verified.
Do not restart it: that would start pi again.

## Check containers

Use a new directory under the run record for each review or integration check.
Copy the selected commands into its `checks.sh`. Run in a Bash subshell so the
worker variables stay unchanged. Set `attempt` to the new directory and
`worktree` to the worker checkout for review or `repo` for integration.
Use the preparation and identity procedure above, then:

```sh
if python3 "$skill/scripts/create_container.py" --attempt "$attempt" --launch -- \
  bash "$attempt/checks.sh" > "$attempt/checks.log" 2>&1; then
  printf '0\n' > "$attempt/checks.exit"
else
  rc=$?
  printf '%s\n' "$rc" > "$attempt/checks.exit"
fi
test "$(owned_state)" = stopped
test "$(cat "$attempt/checks.exit")" = 0
```

This uses `linux launch --name <NAME> -it -- bash ...`, not pi.
Retain logs and receipt even on failure. Confirm stopped state on all paths
before cleanup. Require checks.exit = 0 before acceptance.

## Integration checks

After merging, run a fresh check container against the target checkout.
Save target HEAD first and require it unchanged after checks. Require Git status
to be clean under the Aven-file exception. Delete the stopped check container
with the procedure below, including after failed checks when safe.

A failure after merge leaves the task active. Record the delivered SHA and
failure. Repair on a worker branch, then repeat review and integration.
Do not reset the target or mark the task done.

## Delete or recover

Delete only a stopped container whose receipt and live identity match:

```sh
test "$(owned_state)" = stopped
linux delete "$cid"
linux list --all --format json | jq -e --arg id "$cid" \
  'all(.[]; .id != $id)' >/dev/null
```

After interruption, load the receipt and inspect the exact container. Leave a
running worker alone while checking outstanding work. To cancel or stop an
abandoned execution, record the cancellation or blocker in aven, then use
`linux stop --time 10 "$cid"` and confirm stopped.

If inspect fails, use the exact list command above. Only a successful list
excluding the ID proves absence. A connection failure does not.
A prepared receipt with no launch intent has not launched. A launch intent with
an absent container is a failed attempt: retain it and allocate a fresh attempt.
Never repeat an uncertain launch, restart a worker, or stop/delete another
container. Never use `--all` on stop/delete, `--force`, `clean`, or `prune`.
