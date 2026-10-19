---
name: dispatch
description: Use when the user explicitly requests dispatch to run coding tasks with Workmux workers and Aven tracking, or to resume a dispatch run.
---

# Dispatch

Coordinate workers; own the run through verified completion or a durable handoff. Read enough project context to define scope and acceptance criteria; delegate implementation.

This is an independently maintained workflow. Use the `tasks` skill for Aven operations and installed CLI help for syntax. Its supporting documents are procedures, not generated Workmux skills.

## Contract

- Dispatch alone changes task status and assignment. Workers write evidence and reports.
- Aven is the durable run record; Git and executed checks establish completion. Workmux `done` means a worker ended its turn, not that a task is complete.
- Serialize worker creation/opening and merges per repository. Implementation may run in parallel within disjoint write scopes.
- Workers merge only after authorization. Keep worktrees until merged-base verification passes; failed or uncertain work remains recoverable.
- Run checks and the actions they gate in fail-fast Bash blocks beginning with `set -euo pipefail`. Record failures separately; success notes, cleanup, and completion require passing evidence.

## 1. Prepare

1. Load `tasks`. Establish the repository, Aven project, explicit local base branch, selected task set, and required task/run checks. Reuse existing project mappings; ask before initializing a missing Git repository.
2. Read [runtime.md](runtime.md) before launching or reconnecting workers. Confirm the execution configuration and multiplexer are usable.
3. Reuse existing tasks; create missing tasks with acceptance criteria and write scopes. Select current-run work as `todo`, express ordering through dependencies, and leave deferred work in `backlog`.
4. If any selected work is already active or has dispatch notes, reconcile it using [recovery.md](recovery.md) before starting replacements.

## 2. Dispatch ready work

1. Query `aven list --ready` with the run's project/scope filters; read each selected task with `aven context <task-ref>`.
2. Reuse a related worker session when practical. Give each worker the task ref, project routing, base branch, write scope, acceptance checks, and the full [worker.md](worker.md) contract. Include context unavailable from the task and preserve attachment paths. Use repository-relative source paths.
3. Mark the task `active` with its agent type before launch. Write the prompt file, then create/open the worker using the runtime procedure. Confirm startup before treating it as dispatched.
4. Append a `DISPATCH` note: handle, branch, worktree path, pre-launch base SHA captured by the runtime procedure, base branch, agent type, config, and execution mode. For resumed workers, retain the original launch evidence. The handle identifies the individual worker; the Aven agent field identifies its type.

## 3. Monitor and review

1. Track all unresolved handles. Use bounded `workmux wait`, with `--any` for multiple workers; inspect status after each wait. Handle finished or waiting workers before waiting again.
2. Retrieve reports with `aven show <task-ref> --full`. Use terminal capture only to diagnose missing reports, failed startup, or unexpected state.
3. Compare the report with the actual diff, commits, acceptance criteria, and check evidence. Return incomplete work to the worker; a report remains provisional until base verification.
4. After an interruption or additional user request, reconcile the full tracked set and resume monitoring unless the user stops the run or input is required. Use [recovery.md](recovery.md) for uncertain state.

## 4. Merge, verify, complete

1. Authorize one worker at a time by sending the full [merge.md](merge.md) procedure plus the task ref, recorded base, and required checks. Use ordinary instructions, not a generated `/merge` invocation.
2. Wait for a new merge result or failure note for that authorization. An old Workmux `done` status is not acknowledgment. On failure, follow recovery before retrying.
3. Verify the worker's post-rebase commit is an ancestor of `refs/heads/<base>`. Run the required checks on that exact base revision in a clean checkout; record the revision tested. Recheck the base before closure if it may have moved.
4. If verification fails or cannot run, keep the task active and its worktree intact. Send the failure back for repair, then repeat review, merge, and base verification.
5. After verification, remove only the task's clean, verified worktree and branch. Record `MERGE: <verified base SHA>; <checks>; Verified and done. Cleanup complete.` Then mark the task `done` and clear its agent. A cleanup failure remains pending, not complete.
6. Query ready tasks again using the run's filters. Create or reuse tasks for discovered work; distinguish current-run work from deferred backlog.

## 5. Close the run

1. Confirm all selected tasks are verified, merged, and cleaned up. Run the run-wide checks against the final base revision; passing task checks do not replace these.
2. Close only progress UI created by this run, using its recorded ID. If any condition is unmet, retain the UI and write a recovery handoff instead of claiming completion.
3. Write one `SUMMARY` note on the run's epic, or a designated task when there is no epic: delivered outcome, final verified SHA, checks, and follow-up refs. Give the user a concise outcome and validation report.

## Evidence notes

Use `DISPATCH`, `RESULT`, `MERGE`, `BLOCKED`, and `SUMMARY` for transitions; add progress notes only for material decisions or changes. Record facts once and refer back to unchanged metadata. Use Git-generated unambiguous short SHAs, not branch names alone. Keep failure details sufficient to resume; never replace evidence with a success claim.
