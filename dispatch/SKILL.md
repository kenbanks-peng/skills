---
name: dispatch
description: Use when the user explicitly requests dispatch to run coding tasks with Workmux workers and Aven tracking, or to resume a dispatch run.
---

# Dispatch

Coordinate workers; own the run through verified completion or a durable handoff. Read enough project context to define scope and acceptance criteria; delegate implementation.

This is an independently maintained workflow. Use the `tasks` skill for Aven operations and installed CLI help for syntax.

## Contract

- Dispatch alone changes task status and assignment. Workers write evidence and reports.
- Aven is the durable run record; Git and executed checks establish completion. Workmux `done` means a worker ended its turn, not that a task is complete.
- Serialize worker creation/opening and merges per repository. Implementation may run in parallel within disjoint write scopes.
- Workers merge only after authorization. Keep worktrees until merged-base verification passes; failed or uncertain work remains recoverable.
- Use the fail-fast helpers for mechanical gates. For shell sequences, run checks and gated actions in Bash blocks beginning with `set -euo pipefail`. Record failures separately; success notes, cleanup, and completion require passing evidence.

## 1. Prepare

1. Load `tasks`. Establish the repository, Aven project, explicit local base branch, selected task set, and required task/run checks. Reuse existing project mappings; ask before initializing a missing Git repository.
2. Read [runtime.md](runtime.md) before launching or reconnecting workers. Confirm the execution configuration and multiplexer are usable; set up the dispatch and tasks tabs as described there.
3. Reuse existing tasks; create missing tasks with acceptance criteria and write scopes. Select current-run work as `todo`, express ordering through dependencies, and leave deferred work in `backlog`.
4. If any selected work is already active or has dispatch notes, reconcile it using [recovery.md](recovery.md) before starting replacements.

## 2. Dispatch ready work

1. Query `aven list --ready` with the run's project/scope filters; read each selected task with `aven context <task-ref>`.
2. Generate each initial worker prompt with [scripts/worker_prompt.py](scripts/worker_prompt.py) using its `--help` and the [runtime procedure](runtime.md).
3. Mark the task `active` with its agent type before launch. Write the prompt file, then create/open the worker using the runtime procedure. Confirm startup before treating it as dispatched.
4. Render and append a `DISPATCH` note using the evidence-note procedure below. For resumed workers, retain the original launch evidence. The handle identifies the individual worker; the Aven agent field identifies its type.

## 3. Monitor and review

1. Track all unresolved handles. Use bounded `workmux wait`, with `--any` for multiple workers; inspect status after each wait. Handle finished or waiting workers before waiting again.
2. Retrieve reports with `aven show <task-ref> --full`. Use terminal capture only to diagnose missing reports, failed startup, or unexpected state.
3. Compare the report with the actual diff, commits, acceptance criteria, and check evidence. Return incomplete work to the worker; a report remains provisional until base verification.
4. After an interruption or additional user request, reconcile the full tracked set and resume monitoring unless the user stops the run or input is required. Use [recovery.md](recovery.md) for uncertain state.

## 4. Merge, verify, complete

1. Run [git_preflight.py](scripts/git_preflight.py) for the reviewed worker. On success, generate a single-attempt authorization with [merge_prompt.py](scripts/merge_prompt.py), then send it to one worker at a time. The generator inlines [merge.md](merge.md); use its authorization ID to correlate the response.
2. Wait for a new merge result or failure note for that authorization. An old Workmux `done` status is not acknowledgment. On failure, follow recovery before retrying.
3. Run [verify_base.py](scripts/verify_base.py) with the checked post-rebase worker commit and required checks. Retain its JSON evidence. Recheck the base before closure if it may have moved.
4. If verification fails or cannot run, keep the task active and its worktree intact. Send the failure back for repair, then repeat review, merge, and base verification.
5. After verification, stop worker writers and reconcile their Workmux sessions. Review [cleanup_worker.py](scripts/cleanup_worker.py)'s dry run, then explicitly authorize cleanup using the verified revisions. Retain its JSON evidence and render the `MERGE_VERIFIED` note. Append it before marking the task `done` and clearing its agent. Any cleanup failure remains pending, not complete.
6. Query ready tasks again using the run's filters. Create or reuse tasks for discovered work; distinguish current-run work from deferred backlog.

## 5. Close the run

1. Confirm all selected tasks are verified, merged, and cleaned up. Use `verify_base.py` for the run-wide checks against the final base revision, supplying a retained verified worker commit. Passing task checks do not replace these.
2. After all worktrees are cleaned up, remove their recorded parent directories only if empty, using `rmdir` on each exact path; leave nonempty directories intact. A cleanup failure other than a nonempty directory remains pending.
3. On successful completion, close this run's tasks view using its recorded resource ID and the [runtime cleanup procedure](runtime.md#dispatch-and-tasks-tabs). If any condition is unmet, retain it and write a recovery handoff instead of claiming completion.
4. Render and append one `SUMMARY` note on the run's epic, or a designated task when there is no epic. Give the user a concise outcome and validation report.

## Evidence notes

Use [render_note.py](scripts/render_note.py) and its `--help` to render transition notes from the [templates](templates). Review the result, then append through `tasks`; rendering never posts or changes status. Worker reports remain governed by their inlined contracts when dispatcher-local helpers are inaccessible. Record facts once and refer back to unchanged metadata; add progress notes only for material decisions. Use full Git SHAs for machine evidence and Git-generated unambiguous short SHAs for other prose. Keep failure details sufficient to resume; never replace evidence with a success claim.
