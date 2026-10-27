# Status in the existing dispatch pane

Use the existing dispatch pane for the
run's status. Refresh after launch, native events, queue delivery, review,
checks, merge, and cleanup. A saved TML file is not a live native surface.

## Refresh and display

Maintain one task snapshot using assets/dashboard-example.json as its schema,
not as live status. Aven stores task requirements and durable outcomes.
The agent supplies task decisions, checks, review, delivery, and blockers.
The script supplies observed native state and the next revision:

```sh
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" status
python3 "$skill/scripts/dashboard.py" observe "$run_dir/snapshot-1.json" --inventory "$run_dir/inventory.json" > "$run_dir/snapshot-2.json"
python3 "$skill/scripts/dashboard.py" report "$run_dir/snapshot-2.json"
```

Use the successful new snapshot for the next refresh. Retry status
after a failed inventory command. observe rejects failed inventory and data
older than 60 seconds; run status again instead of using an old file. Native
events trigger refresh.
Missing workers become unknown, not done. Report does not create a window.
Its overview fits 80 columns. Full results stay in task notes and script logs.

## Snapshot

Top level: run, revision (integer), observed_at, tasks (list). Each task/attempt
has text fields task, task_state, attempt, agent, session, pane, branch, worktree,
environment, queue, review, checks, delivery, blockers, cleanup; dependencies is
a text list. native contains state, source, identity (text), evidence_age_ms,
completion_seq, subagents (nonnegative integers or null).
Use full window UUIDs and host-qualified session addresses. Use unknown/not run
for facts not observed. Replace stale results with fresh observations.
observe replaces native fields only; it does not accept a task or infer delivery.

## Existing TML surfaces

If the run already has an authorized TML surface, render/patch can still update
it without opening another pane. Use the same owner pane and saved surface ID:

```sh
python3 "$skill/scripts/dashboard.py" patch "$run_dir/snapshot-1.json" "$run_dir/snapshot-2.json" > "$run_dir/dashboard.patch.json"
tuios tml patch "$SURFACE" "$(cat "$run_dir/dashboard.patch.json")"
tuios tml get "$SURFACE"
```

Patches check run/revision before replacement. If a patch fails, read current
state before retrying, keeping the same surface.
For offline inspection, render SNAPSHOT writes a read-only TML document to
stdout. No script opens TML windows or asks for input.

At run end, close all other run-owned windows, including Aven and Linux workers.
Leave final status in dispatch. An extra status window is not an exception.
