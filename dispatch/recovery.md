# Recovery and handoff

Read before replacing workers, retrying uncertain operations, or resuming an interrupted run.

## Reconcile first

1. Query `aven list --open` using the run's project/scope filters and inspect task context and full notes. Include any completed tasks explicitly recorded as having pending cleanup.
2. Use the saved worker record, not a new recovery JSON document. After integration, run `python3 <skill-directory>/scripts/finish_worker.py <full-ref> --inspect`. Compare current resources with the saved identity, action journal, stop evidence, archives, and pending cleanup. A closed UI does not prove exit. Before integration, use `dispatch.py inspect <full-ref>`. Use `recovery_snapshot.py` only for targeted diagnostics of legacy records; never guess missing identity.
3. Establish what actually happened from Git ancestry and working-tree state. A missing worker window does not prove lost work; a completion note does not prove a merge. Inspect both the reported worker commit and current branch tip when they differ.

## Choose the next action

| Observed state                       | Action                                                                                                                                                                                                                                                                                                     |
| ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Worker still running                 | Resume monitoring; avoid duplicate dispatch.                                                                                                                                                                                                                                                               |
| Worker needs input                   | Resolve the question or report the blocker to the user.                                                                                                                                                                                                                                                    |
| Startup unconfirmed                  | Inspect status and capture output; reconcile partial resources before retrying. A worker may have finished before `working` was observed.                                                                                                                                                                  |
| Report missing                       | Inspect worker state and restore Aven reporting before merge.                                                                                                                                                                                                                                              |
| Reported work not merged             | Review it, then authorize a merge only when ready.                                                                                                                                                                                                                                                         |
| Work already merged                  | Verify the actual base revision; repair failed checks without repeating the old merge.                                                                                                                                                                                                                     |
| Verification passed, cleanup pending | Run `finish_worker.py <full-ref> --inspect`, then repeat `finish_worker.py <full-ref>` to resume the saved authorization. It rechecks verification, base, exit, and surviving resources. Never recreate resources merely to rerun cleanup. Retained resources stay pending with owner and next action. |
| Work or ownership uncertain          | Preserve resources, record the discrepancy, and seek the missing evidence.                                                                                                                                                                                                                                 |

## Locks and reassignment

- On a lock error, pause repository lifecycle mutations. Inspect lock metadata, owning processes, Git/common directories, and partial Workmux resources. Remove a lock only when it is confirmed stale; retain potentially live locks.
- Before reassignment, stop the old worker and confirm it cannot continue writing using [the verified stop procedure](runtime.md#stop-archive-and-clean-up). Preserve its changes, determine merge state, and record the handoff before assigning a replacement.
- Reuse the original session when available: send a follow-up to a live worker or reopen the retained worktree with `--continue`. Read [runtime.md](runtime.md) for environment and serialization rules. If the worktree was removed, reconcile the prior merge before recreating it from the recorded base.

## Leave a durable handoff

Write `BLOCKED:` directly using the `tasks` selective-note policy, referencing retained recovery and verification evidence. Retain the text locally and surface any Aven write failure; restore required durable reporting before merge or completion. Keep unfinished tasks active and assigned unless explicitly handing ownership off. Use optional `ACTIVITY:` notes for consequential recovery decisions. Tell the user what needs attention. If an optional tasks view remains open, retain its exact ID for best-effort housekeeping; UI never gates completion.
