# One live dashboard

Open one read-only TML pane in the dispatcher's workspace before workers launch.
Update it in place. Do not substitute prose, an empty terminal, or a saved TML
file for an open surface. Read the rendered view before and after opening.

The supplied helper only renders snapshots and guarded patches. It does not
launch work, poll agents, or schedule tasks. Aven and native tuios inventories
remain the sources of truth.

## Open

Set skill to this installed directory and run_dir to the run's evidence folder.
Use assets/dashboard-example.json for the schema, not as live status. Start with
the actual run identity and pending tasks; unknown fields say unknown.

```sh
python3 "$skill/scripts/dashboard.py" render "$run_dir/snapshot-1.json" > "$run_dir/dashboard.tml"
tuios tml validate "$run_dir/dashboard.tml"
tuios tml render "$run_dir/dashboard.tml" --width 80 --height 24
tuios tml show "$run_dir/dashboard.tml" --pane -s "$DISPATCH_SESSION" --workspace "$DISPATCH_WORKSPACE" --name "dispatch status" --json
```

Record the returned surface ID and pane ID. Confirm it exists with tml get and
capture-pane. Inspect the actual overview for clipped columns and empty data.
Name the run's workspaces; do not steal focus or switch the user's session.
Worker views belong in a workers workspace, not between tiny check panes.

## Update

After launch, state changes, queue delivery, review, checks, merge, and cleanup,
build the next snapshot and increment revision:

```sh
python3 "$skill/scripts/dashboard.py" patch "$run_dir/snapshot-1.json" "$run_dir/snapshot-2.json" > "$run_dir/dashboard.patch.json"
tuios tml patch "$SURFACE" "$(cat "$run_dir/dashboard.patch.json")"
tuios tml get "$SURFACE"
tuios capture-pane -s "$DISPATCH_SESSION" -w "$DASHBOARD_PANE"
```

The same owner pane must update the surface. Patches test the run/revision to
prevent stale updates. If a patch fails, get the current state before retrying.
If the surface was closed, confirm absence before opening one replacement.

## Snapshot

Top level: run, revision (integer), observed_at, tasks (list). Each task/attempt
has text fields task, task_state, attempt, agent, session, pane, branch, worktree,
environment, queue, review, checks, delivery, blockers, cleanup; dependencies is
a text list. native contains state, source, identity (text), evidence_age_ms,
completion_seq, subagents (nonnegative integers or null). Use unknown/not run
for facts not observed. Do not invent a pass or retain stale done after a link
failure. Use concise summaries; full evidence lives in logs/task notes.

The overview shows task, native state, environment, and blocker. Other tabs show
execution, checks/delivery, and resource details. Host-qualified addresses must
identify Linux workers and their views. Read-only tabs are navigation, not
human-input workflows. Do not add forms, approval buttons, or pane actions.

## Runtime failure

A CLI/daemon mismatch can prevent tml show even when validation passes.
Record the actual error and mark visibility blocked. Continue independent work
only with an explicit degraded status, not a claim that dispatch is working.
Do not open repeated failed surfaces or restart a shared daemon.
A client reached through another machine may show a placeholder for TML; keep
the dashboard on the user's display host and verify there.

Leave one final dashboard with outcomes and retained resources. Close it with
`tuios tml close "$SURFACE" '"dispatch closed"'` only when closure is required.
