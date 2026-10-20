# Recovery and handoff

Load for resume, uncertain state, failed lifecycle operations, or pending cleanup.
The [safety contract](SKILL.md#safety-contract) applies throughout.

## Reconcile first

Query `aven list --open` with the run's filters and read relevant context/notes.
Also include completed tasks listed with pending cleanup in the prior SUMMARY or
saved records; an open-task query alone cannot find these.

```sh
python3 <skill-directory>/scripts/dispatch.py inspect APP-1234
python3 <skill-directory>/scripts/dispatch.py inspect APP-1234 --resume
```

Inspection is read-only; `--resume` saves reconciled observations. Repeated launch
also only reconciles the original assignment; neither starts a replacement.
Use the saved record under `<common-git-dir>/dispatch-workers/<full-ref>/worker.json`,
not a reconstructed identity document. Compare Git ancestry, actual worktree state,
the reported commit and current tip, UI/container identity, and saved attempts.
A missing window is not evidence of lost work or writer exit.

After integration, inspect finish state instead:

```sh
python3 <skill-directory>/scripts/finish_worker.py APP-1234 --inspect
```

## Observed state → action

| Observed state | Action |
| --- | --- |
| Worker still running | Resume bounded monitoring; use the original handle. |
| Worker needs input | Answer or report the blocker to the user. |
| Startup unconfirmed or partial launch | Inspect resources and saved errors; use `dispatch.py inspect <ref> --resume`. Never remove the record to force another add. |
| Report missing or invalid | Diagnose worker state and restore a current RESULT in Aven before integration. |
| Reported work not integrated | Review the actual diff and latest RESULT, then use `integrate.py <ref> --reviewed-commit <sha> --result-id <id>`. |
| Conflict/check failure before merge attempt | Send repair to the worker, preserving unfinished Git state. Review its new commit and RESULT; use the same integration command with `--new-attempt`. |
| Merge attempted, failed, or interrupted | With the original reviewed SHA and RESULT ID, use `integrate.py <ref> --reviewed-commit <sha> --result-id <id> --reconcile`. It never merges/rebases; it checks actual ancestry and runs fresh verification. |
| Integrated, not independently verified | Inspect integration evidence and reconcile; repair failed checks without repeating the old merge. |
| Verified, finish not authorized | Review `finish_worker.py <ref>` and authorize its plan once with `--authorize-finish`. |
| Finish interrupted or cleanup pending, including task already done | Inspect finish, then repeat `finish_worker.py <ref>` without new authorization. It rechecks the saved verification, base, exit and surviving resources and attempts remaining actions only. Keep pending identity/evidence/owner/next action visible in the handoff. |
| Resource reappeared after recorded removal, unexpected absence, or changed identity | Preserve it for judgment; old authorization does not cover replacement resources. Never recreate removed resources merely to retry cleanup. |
| Work, exit, or ownership uncertain | Preserve resources, record the discrepancy, and obtain the missing evidence. |

## Locks, repair, and reassignment

On lock errors pause lifecycle mutations. Inspect lock metadata, owning processes,
Git/common directories, and partial resources. Remove only a confirmed stale lock.
For legacy records, `recovery_snapshot.py --help` offers targeted diagnostics;
missing identity needs investigation rather than automatic adoption.

Use a live worker's original session for repair. Reopening a retained worktree with
`--continue` requires the recorded config and original UI context; load
[runtime.md](runtime.md) for adapter details, or [local-worker.md](local-worker.md)
for approved local execution. Before reassignment, confirm the old writer cannot
continue, preserve its changes, determine merge state, and record ownership.
The normal finish operation confirms container exit from exact saved ID/mount
identity; a missing container before a confirmed stop is uncertain. Local writer
exit is not automatically supported. Obtain independent process evidence for
review rather than inferring exit from UI closure.

## Durable handoff

Use `tasks` selective notes for BLOCKED/ACTIVITY and SUMMARY. Record the blocker,
evidence directory, repair owner, and next action. Failed Aven writes retain local
report text and block the corresponding integration/completion gate. Keep unfinished
tasks assigned unless explicitly handing off. Retained prompts, ignored files,
dirty content, and unknown artifacts are pending cleanup, even after task completion.
Known unchanged eligible prompts alone may be archived automatically. Keep the
common Git evidence and container inspection access while cleanup is pending.

UI closure and exact empty-parent `rmdir` failures remain housekeeping. Retain exact
UI ID and original server/session context; use [runtime.md](runtime.md#ui-adapters)
if manual closure is needed. Never target a tab by label or recursively delete a
parent directory.
