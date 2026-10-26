# Recovery and handoff

Load for resume, uncertain state, failed lifecycle operations, or pending cleanup. The [coordination rules](SKILL.md#coordination) applies throughout.

## Reconcile first

On resume and before final handoff, enumerate every tracked task from the prior SUMMARY and saved worker records. Query `aven list --open` with the run's filters. Read each tracked task's current context and only the reports needed for its next action; do not print full note histories or worker records. Include completed tasks with pending cleanup; an open-task query alone cannot find these. Reconcile launch confirmation, reviewed integration, independent checks, exact worker exit, durable reports, live Aven status, and cleanup separately. Terminal appearance or elapsed time establishes none of these gates.

```sh
python3 <skill-directory>/scripts/dispatch.py inspect APP-1234
python3 <skill-directory>/scripts/dispatch.py resume APP-1234
```

Inspection is read-only. For a live worker, `resume` verifies the saved open run, saves observations, and reconciles active status with Aven readback. Use plain inspection for completed workers. Repeated launch also only reconciles the original assignment; neither starts a replacement. Use the saved record under `<common-git-dir>/dispatch-workers/<full-ref>/worker.json`, not a reconstructed identity document. Compare Git ancestry, actual worktree state, the reported commit and current tip, UI/container identity, and saved attempts. A missing window is not evidence of lost work or writer exit.

After integration, inspect finish state instead:

```sh
python3 <skill-directory>/scripts/dispatch.py finish APP-1234 --inspect
```

## Observed state → action

| Observed state                                                                      | Action                                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Worker still running                                                                | Resume bounded monitoring; use the original handle.                                                                                                                                                                                                                                                |
| Confirmed launch but active write failed/interrupted                                | Use `dispatch.py resume <ref>` to reconcile active status for the confirmed original launch. It reads before writing and confirms active afterward; it never adds a replacement worker.                                                                                                                                                       |
| Worker RESULT or Workmux done                                                       | Review the turn's report; keep active until every delivery gate passes.                                                                                                                                                                                                                            |
| Worker needs input                                                                  | Answer or report the blocker to the user.                                                                                                                                                                                                                                                          |
| Startup unconfirmed or partial launch                                               | Inspect resources and saved errors; use `dispatch.py resume <ref>`. Never remove the record to force another add.                                                                                                                                                                        |
| Report missing or invalid                                                           | Diagnose worker state and restore a current RESULT in Aven before integration.                                                                                                                                                                                                                     |
| Reported work not integrated                                                        | Review the actual diff and latest RESULT, then use `dispatch.py integrate <ref> --reviewed-commit <sha> --result-id <id>`.                                                                                                                                                                                  |
| Conflict/check failure before merge attempt                                         | Send repair to the worker, preserving unfinished Git state. Review its new commit and RESULT; use the same integration command with `--new-attempt`.                                                                                                                                               |
| Merge attempted, failed, or interrupted                                             | With the original reviewed SHA and RESULT ID, use `dispatch.py integrate <ref> --reviewed-commit <sha> --result-id <id> --reconcile`. It never merges/rebases; it checks actual ancestry and runs fresh verification.                                                                                       |
| Integrated, not independently verified                                              | Inspect integration evidence and reconcile; repair failed checks without repeating the old merge.                                                                                                                                                                                                  |
| Accepted and integrated, finish not started                                         | Run `dispatch.py finish <ref>`.                                                                                                                                                                                                             |
| Finish interrupted or cleanup pending, including task already done                  | Inspect finish, then repeat `dispatch.py finish <ref>` directly. It checks writer exit and surviving resource identities and attempts remaining actions only. Keep pending identity/evidence/owner/next action visible in the handoff.                               |
| VERIFIED report saved, done write failed/interrupted or live task still active      | Inspect `completion.md`, `finish-blocked.md`, and saved actions. Repair Aven access, restore any locally retained report, then repeat finish. It reads live status, retries an incomplete transition, and requires readback of done. A saved task-action receipt alone is insufficient. |
| Failed checks, unknown exit, or missing durable report                              | Retain the current supported status and resources. Record BLOCKED with evidence, owner, and next action; repair the failed gate before completion.                                                                                                                                                 |
| Resource reappeared after recorded removal, unexpected absence, or changed identity | Preserve it for judgment; saved resource identity does not cover replacements. Never recreate removed resources merely to retry cleanup.                                                                                                                                                        |
| Work, exit, or ownership uncertain                                                  | Preserve resources, record the discrepancy, and obtain the missing evidence.                                                                                                                                                                                                                       |

## Cleanup retry after the base advances

A later base change does not reopen accepted work. Inspect and repeat `dispatch.py finish <ref>` directly. Do not rerun A's acceptance checks against B's changes just to finish A. Finish does not read verification files or maintain a history of base reverification.

Changed resource identity, unknown writer exit, and worktree/branch/archived-prompt reappearance still block destructive cleanup. Preserve these resources for dispatcher review. Dirty, ignored, unknown, or changed prompt content remains pending cleanup. A cleanup-only blocker preserves previously confirmed delivery and task completion. Keep pending cleanup in the handoff even when the task is already done.

## Locks, repair, and reassignment

On lock errors pause lifecycle mutations. Inspect lock metadata, owning processes, Git/common directories, and partial resources. Remove only a confirmed stale lock. For legacy records, `dispatch.py recover snapshot --help` offers targeted diagnostics; missing identity needs investigation rather than automatic adoption.

Use a live worker's original session for repair. Reopening a retained worktree with `--continue` requires the recorded config and original UI context; load [runtime.md](runtime.md) for adapter details (including local execution). Before reassignment, confirm the old writer cannot continue, preserve its changes, determine merge state, and record ownership. The normal finish operation confirms container exit from exact saved ID/mount identity; a missing container before a confirmed stop is uncertain. Local writer exit is not automatically supported. Obtain independent process evidence for review rather than inferring exit from UI closure.

## Exceptional command help

Use normal finish first. These commands are for a diagnosed recovery need:

```sh
python3 <skill-directory>/scripts/dispatch.py recover snapshot --help
python3 <skill-directory>/scripts/dispatch.py recover preflight --help
python3 <skill-directory>/scripts/dispatch.py recover verify --help
python3 <skill-directory>/scripts/dispatch.py recover stop --help
python3 <skill-directory>/scripts/dispatch.py recover archive --help
python3 <skill-directory>/scripts/dispatch.py recover cleanup --help
python3 <skill-directory>/scripts/dispatch.py doctor --help
```

Stop, archive, and cleanup need exact saved identity/evidence inputs. Dry-run output is not authorization to execute. Keep explicit execute/cleanup authorization flags and all validation gates. Never use recovery to replace an uncertain worker, infer a stopped writer from a missing UI, or delete unknown content.

Default output is compact. Read the named evidence or use `--verbose` on a read-only query for details. Do not rerun a mutation only to print its evidence. Verification and oversized recovery logs remain outside worker/check checkouts; complete log paths survive cleanup.

## Durable handoff

Use `tasks` selective notes for BLOCKED/ACTIVITY and SUMMARY. Record the blocker, evidence directory, repair owner, and next action. Failed Aven writes retain local report text and block the corresponding integration/completion gate. Keep unfinished tasks assigned unless explicitly handing off. `BLOCKED:` is a report, not a supported task status. On an authorized transition out of active, clear an agent field only if the installed CLI supports it; current Aven has neither that field nor a clear-agent flag. Keep session identities in the saved worker record. Retained prompts, ignored files, dirty content, and unknown artifacts are pending cleanup, even after task completion. Known unchanged eligible prompts alone may be archived automatically. Keep the common Git evidence and container inspection access while cleanup is pending.

Before final handoff, list every remaining active task with its blocker, owner, and next action (or explicitly state none), and list done tasks' pending cleanup separately. Confirm status writes individually from evidence rather than bulk-closing active tasks. If Aven is unavailable, keep the handoff locally, surface that failure, and restore the durable note before claiming success.

UI closure and exact empty-parent `rmdir` failures remain housekeeping. Retain exact UI ID and original server/session context; use [runtime.md](runtime.md#ui-adapters) if manual closure is needed. Never target a tab by label or recursively delete a parent directory.
