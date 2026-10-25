# Resume and handoff

Read this before replacing a worker, repeating an uncertain launch or merge, or resuming an interrupted run.

## Reconstruct

1. Read the run's Aven `SUMMARY:` and each assigned task's `DISPATCH:`, `RESULT:`, `BLOCKED:`, and `VERIFIED:` notes. Include done tasks with pending cleanup.
2. Reconnect to the recorded daemon/server. List worktrees and pi panes, then match the saved session, pane ID, canonical repository/worktree, branch, group, and launch SHA.
3. Inspect Git state and current Aven status. Saved notes describe prior observations, not live state. A restored pane may be a new shell, not the old agent.
4. Reconcile every assignment before launching more work. Claim dispatcher ownership in Aven and confirm that the prior dispatcher is no longer acting.

Use `tuios --skill state` for restart and native `resume-agent` support. Check its dry run before resuming. If native resume is unavailable, use the exact pi session file/ID from saved evidence; never use `pi --continue` to guess a conversation.

## Choose the next action

| Observed state | Action |
| --- | --- |
| Launch pending, resources present | Match the existing worker and prompt status; finish recording and activation. |
| Launch pending, resources uncertain | Inspect the daemon, Git worktrees, and processes. Preserve partial resources; do not create a duplicate. |
| No worker or partial resource remains, no implementation started | Record the failed attempt, then authorize a fresh unique group for the same task. |
| Worker working | Resume bounded state waits. |
| Worker needs input | Tell the person what decision is needed; do not inject text. |
| Worker done, no matching report | Inspect the pane and retained report files; request a report from that worker if safe. |
| Result SHA differs from branch tip | Review the current commit and obtain a matching report. |
| Merge outcome uncertain | Check whether the reviewed SHA is already in the intended base before any merge retry. |
| Reviewed SHA already integrated | Verify the actual integrated revision and required checks; finish reporting without merging again. |
| Base changed after failed verification | Inspect the intervening work. Verify the current revision and record which revision passed; do not reset it. |
| Verified delivery, task still active | Restore VERIFIED evidence, confirm live status, and complete only this task. |
| Task done, resources retained | Retry safe cleanup only; retain delivery evidence and the branch. |

Before a fresh launch after loss, preserve uncommitted work and confirm no old writer remains. A closed UI or missing state report is not proof of process exit.

## Partial handoff

Keep unfinished tasks active unless the user chooses another supported status. Record delivery state, blocker, owner, next action, and exact retained resource identities. For canceled work, preserve commits and material files before cleanup.

If Aven is unavailable, keep reports outside worker worktrees under the common Git directory, grouped by run. Tell the user the paths. Do not claim durable Aven reporting or task completion until the write and status readback succeed.

End with a SUMMARY that accounts for the full run. Record cleanup separately from implementation. Leave unresolved worktrees intact.
