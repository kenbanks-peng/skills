# Recovery and cleanup

## Resume

Read Aven context and reconcile the recorded host/session/pane/worktree IDs with
native worktree, agent, queue, review, and ship inventories. Inspect repository
history for commits/merges whose output was lost. Reuse matching resources.
Do not relaunch, requeue, recommit, or remerge solely because output is missing.

Native mail and queue can disappear after a daemon restart. Repository state
and saved results determine what ran. A stale remote link does not mean a worker
stopped. Preserve uncertain work and report the specific unresolved effect.
Preserving work does not require keeping its windows open at run end.
Use native resume-agent where its installed harness supports it.

## Cleanup

Close resources as soon as their purpose ends, not only at final delivery.
At every run end, including blocked and failed runs, leave only the run-owned
dispatch window. Close Aven, Linux worker windows, worker views, and all hidden
auxiliary windows. Do not close unrelated windows that existed before the run.
Record the initial inventory and each owned ID, including implicit windows.

Only dispatch, Aven, and active Linux workers may be visible during the run.
All auxiliary windows in the table must be hidden from creation:

| Resource | End of purpose |
| --- | --- |
| Worktree starter shell | Worker is ready and has replaced it; never visible |
| Check command pane | Exit and full log are saved, pass or fail |
| Reusable checks shell | Checkout's checks are complete |
| Reviewer | Findings are recorded |
| Worker/view | Source worker finishes, session is removed, or run ends |
| Aven window | Run ends; task records are saved |
| Event reader | Wait/monitoring stage ends |
| Task worktree/session | Delivery/disposition and useful evidence are saved |
| Dispatch/dashboard | Keep the single dispatch window with final status |

Use exact owned IDs. Do not close unrelated demo panes as part of another run.

```sh
tuios close-window -s "$SESSION" "$TEMP_PANE"
tuios worktree rm "$SESSION" --json
```

Native worktree rm removes the session/tree and retains the branch.
For useful dirty alternatives, retain the worktree or use native --stash when
preservation in stash fits the recorded disposition. Use fan keep for group
cleanup when all unselected attempts have a disposition. Do not force discard
unresolved work. Save useful checkpoints/logs outside removed trees.
Stop owned container processes with their runtime tool; removing a pane does
not remove a container.

Before closing worker windows, stop their queues and writers through supported
native controls. Save dirty work, checkpoints, logs, and resume identities.
Retain a branch, stash, or worktree on disk when needed, not its window. If a
window cannot close safely, record cleanup blocked; do not claim completion.

Update the same dashboard with removed/retained resources. Compare initial and
final inventories across all owned hosts and sessions, including hidden windows.
The run-owned window inventory must contain dispatch only: no Aven, workers,
views, starter shells, merge, integration, check, review, or monitoring windows.
Verify actual closure, not merely loss of focus or movement to another workspace.

## Handoff

Report delivered changes and task refs, source/target commits, check results,
blockers, and retained resources. Separate delivered work from cleanup pending.
Do not turn the final response into a command transcript or ask a question.
