# Recovery and cleanup

## Resume

Read Aven context and reconcile the recorded host/session/pane/worktree IDs with
native worktree, agent, queue, review, and ship inventories. Inspect repository
history for commits/merges whose output was lost. Reuse matching resources.
Do not relaunch, requeue, recommit, or remerge solely because output is missing.

Native mail and queue can disappear after a daemon restart. Repository state
and saved results determine what ran. A stale remote link does not mean a worker
stopped. Keep uncertain work and report the specific unresolved effect.
Use native resume-agent where its installed harness supports it.

## Cleanup

Close resources as soon as their purpose ends, not only at final delivery:

| Resource | End of purpose |
| --- | --- |
| Worktree starter shell | Worker is ready and has replaced it |
| Check command pane | Exit and full log are saved, pass or fail |
| Reusable checks shell | Checkout's checks are complete |
| Reviewer | Findings are recorded |
| Worker view | Source worker finishes or its session is removed |
| Event reader | Wait/monitoring stage ends |
| Task worktree/session | Delivery/disposition and useful evidence are saved |
| Dashboard | Keep one final surface unless closure was requested |

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

Update the same dashboard with removed/retained resources. Confirm the final
inventory has no abandoned starter shells, checks, reviewers, or worker views.

## Handoff

Report delivered changes and task refs, source/target commits, check results,
blockers, and retained resources. Separate delivered work from cleanup pending.
Do not turn the final response into a command transcript or ask a question.
