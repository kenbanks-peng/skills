# Recovery and cleanup

## Resume

Read Aven context and the saved run directory. Run workspace.py status.
Reconcile pane, worktree, queue, review, and ship identities against native
inventories. Inspect pending journal entries and Git history before retrying
an operation with uncertain output. Reuse matching resources and assignments.

## Cleanup

Save results, dirty work, checkpoints, and logs outside disposable trees.
Stop worker queues and background writers through the supported native controls.
Close starter and helper panes when their purpose ends.
At every run end, including blocked and failed runs, close Aven, Linux workers,
views, and helper panes. Keep dispatch with the final result.
Preserve unrelated windows and useful unresolved work on disk.

```sh
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" cleanup --evidence-saved
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" audit --final
```

The cleanup script captures logs and closes registered idle panes by exact ID.
Inspect cleanup failures, resolve active writers, and rerun with the same
directory. Use workspace.py close for one finished resource during a run.
Record worktree disposition, then use native worktree removal for completed
trees. Container mode removes its temporary container when the command exits.
Use the runtime's lifecycle tools for other owned container resources.

Compare initial and final inventories. Final run-owned inventory contains
dispatch only. Record retained branches, stashes, worktrees, and logs.

## Handoff

Report delivered changes, task references, check results, unresolved work,
and retained resources. Separate delivery results from cleanup still pending.
