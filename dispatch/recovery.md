# Recovery and handoff

Read before replacing workers, retrying uncertain operations, or resuming an interrupted run.

## Reconcile first

1. Query `aven list --open` using the run's project/scope filters and inspect task context and full notes. Include any completed tasks explicitly recorded as having pending cleanup.
2. Reconstruct each task's handle, branch, worktree, base, config, last reported commit, and next action. Compare with `workmux list`, `workmux status`, and `git worktree list`.
3. Establish what actually happened from Git ancestry and working-tree state. A missing worker window does not prove lost work; a completion note does not prove a merge. Inspect both the reported worker commit and current branch tip when they differ.

## Choose the next action

| Observed state | Action |
| --- | --- |
| Worker still running | Resume monitoring; avoid duplicate dispatch. |
| Worker needs input | Resolve the question or report the blocker to the user. |
| Startup unconfirmed | Inspect status and capture output; reconcile partial resources before retrying. A worker may have finished before `working` was observed. |
| Report missing | Inspect worker state and restore Aven reporting before merge. |
| Reported work not merged | Review it, then authorize a merge only when ready. |
| Work already merged | Verify the actual base revision; repair failed checks without repeating the old merge. |
| Verification passed, cleanup pending | Reconfirm ancestry and clean state, then finish cleanup and closure. |
| Work or ownership uncertain | Preserve resources, record the discrepancy, and seek the missing evidence. |

## Locks and reassignment

- On a lock error, pause repository lifecycle mutations. Inspect lock metadata, owning processes, Git/common directories, and partial Workmux resources. Remove a lock only when it is confirmed stale; retain potentially live locks.
- Before reassignment, stop the old worker and confirm it cannot continue writing. Preserve its changes, determine merge state, and record the handoff before assigning a replacement.
- Reuse the original session when available: send a follow-up to a live worker or reopen the retained worktree with `--continue`. Read [runtime.md](runtime.md) for environment and serialization rules. If the worktree was removed, reconcile the prior merge before recreating it from the recorded base.

## Leave a durable handoff

Append `BLOCKED` with observed progress, commits/checks, retained resources, blocker, responsible party, and next action. Keep unfinished tasks active and assigned unless explicitly handing ownership off. Record changed handles/configurations rather than repeating the original dispatch entry. Tell the user what needs attention and retain run-owned progress UI while the run is incomplete.
