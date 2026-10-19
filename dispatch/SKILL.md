---
name: dispatch
description: Use when the user explicitly requests dispatch to run coding tasks with Workmux workers and Aven tracking, or to resume a dispatch run.
---

# Dispatch

Coordinate workers; own the run through verified completion or a durable handoff. Read enough project context to define scope and acceptance criteria; delegate implementation.

Use the `tasks` skill for Aven operations and `aven` CLI help for syntax.

## Contract

- Dispatch alone changes task status and assignment. Workers write evidence and reports.
- Aven is the durable run record. Workmux `done` means a worker ended its turn, not that a task is complete.
- Serialize worker creation/opening and merges per repository. Implementation may run in parallel within disjoint write scopes.

## 1. Prepare

1. Load `tasks`.
2. Ask before initializing a missing Git repository.
3. Read [runtime.md](runtime.md) before launching or reconnecting workers.
4. Reuse existing tasks; create missing tasks with acceptance criteria and write scopes. Express ordering through dependencies.
5. If any selected work is already active or has dispatch notes, reconcile it using [recovery.md](recovery.md) before starting replacements.

## 2. Dispatch ready work

1. Query `aven list --ready` with the run's project/scope filters; read each selected task with `aven context <task-ref>`.
2. Run [scripts/dispatch.py](scripts/dispatch.py) `launch <full-task-ref>` with the explicit local base, write scopes, and required argv checks, using the [runtime procedure](runtime.md). It loads Aven context, creates the prompt, and saves one worker record. No caller-managed prompt JSON or launch receipt is needed.
3. Require a confirmed launch in the saved record, then mark the task `active` with the observed agent type. Repeated launch and `inspect --resume` only reconcile existing resources; they never start a replacement.
4. Render and append a `DISPATCH` note using the evidence-note procedure below. For resumed workers, retain the original launch evidence. Record shared config, execution mode, UI resource IDs, and run-wide checks in one ACTIVITY: run-context note on the run epic or designated task; refer to that record from task notes and record task-specific overrides.

## 3. Monitor and review

1. Track all unresolved handles. Use bounded `workmux wait`, with `--any` for multiple workers; inspect status after each wait. Handle finished or waiting workers before waiting again.
2. Retrieve the latest relevant note with [dispatch_cli.py](scripts/dispatch_cli.py) `report`, as described in [runtime.md](runtime.md#compact-reports). Retain full JSON once when several notes are needed; reserve full history for recovery. Use terminal capture only to diagnose missing reports, failed startup, or unexpected state.
3. Compare the report with the actual diff, commits, acceptance criteria, and check evidence. Return incomplete work to the worker; a report remains provisional until base verification.
4. After an interruption or additional user request, reconcile the full tracked set and resume monitoring unless the user stops the run or input is required. Use [recovery.md](recovery.md) for uncertain state.

## 4. Merge, verify, complete

1. Run [git_preflight.py](scripts/git_preflight.py) for the reviewed worker. On success, generate a single-attempt authorization with [merge_prompt.py](scripts/merge_prompt.py), then send it to one worker at a time. The generator inlines [merge.md](merge.md); use its authorization ID to correlate the response.
2. Wait for a new merge result or failure note for that authorization. An old Workmux `done` status is not acknowledgment. On failure, follow recovery before retrying.
3. Run [verify_base.py](scripts/verify_base.py) with the checked post-rebase worker commit and required checks. Retain its JSON evidence. Recheck the base before closure if it may have moved.
4. If verification fails or cannot run, keep the task active and its worktree intact. Send the failure back for repair, then repeat review, merge, and base verification.
5. After verification, follow [stop, archive, and cleanup](runtime.md#stop-archive-and-clean-up): verify worker exit, reconcile its UI, and archive generated prompts before cleanup checks. Review [cleanup_worker.py](scripts/cleanup_worker.py)'s dry run, then explicitly authorize cleanup using the verified revisions and container stop evidence. Retain all JSON evidence and render the `MERGE_VERIFIED` note. Append it before marking the task `done` and clearing its agent. Any cleanup failure remains pending, not complete.
6. Query ready tasks again using the run's filters. Create or reuse tasks for discovered work; distinguish current-run work from deferred backlog.

## 5. Close the run

1. Confirm all selected tasks are verified, merged, and cleaned up. If acceptance requires identifying notes, require a committed manifest and persistent CI check for all exact notes using the [runtime procedure](runtime.md#persistent-identifying-note-checks). Use `verify_base.py` for the run-wide checks against the final base revision, supplying a retained verified worker commit. Passing task checks do not replace these.
2. After all worktrees are cleaned up, remove their recorded parent directories only if empty, using `rmdir` on each exact path; leave nonempty directories intact. A cleanup failure other than a nonempty directory remains pending.
3. On successful completion, close this run's tasks view using its recorded resource ID and the [runtime cleanup procedure](runtime.md#dispatch-and-tasks-tabs). If any condition is unmet, retain it and write a recovery handoff instead of claiming completion.
4. Render and append one `SUMMARY` note on the run's epic, or a designated task when there is no epic. Give the user a concise outcome and validation report.

## Evidence notes

Every dispatch-written note or comment starts with a standard CAPS prefix followed by a colon. Use one lead sentence and at most three short bullets (normally under 80 words); recovery blockers may exceed this when necessary. Write plain, scannable text with one fact per bullet.

Record only the new event. Keep recovery coordinates in DISPATCH and shared settings in one run-context note; refer back to them. Omit the attached task's own ref, unchanged state, routine commands, and lifecycle recaps. Summarize distinct checks by outcome; retain commands, logs, full SHAs, and resource identity in evidence files and link them. Display home paths with `~`.

- `ACTIVITY:` — shared run context, a material decision, review/authorization, or recovery update. State what changed and why; routine polling needs no note.
- `DISPATCH` — worker recovery coordinates and launch revision; reference shared run context.
- `RESULT` — delivered change, commit, acceptance/check results, and exceptions.
- `MERGE` — worker integration result, checked post-rebase commit, resulting base revision, post-rebase check results, and consequential conflict decisions. Explicitly awaiting dispatch verification.
- `VERIFIED` — dispatch's independently tested base revision, check results, and completed cleanup. Add verification evidence rather than repeating the worker's merge report.
- `BLOCKED` — blocker first, then recovery evidence, responsible party, and next action.
- `SUMMARY` — delivered outcome, final verified revision, run-wide check results, and follow-up refs; leave lifecycle history in earlier notes.

Use [render_note.py](scripts/render_note.py) and its `--help` to render transition notes from the [templates](templates). Review for relevance and add material decisions or exceptions before appending through `tasks`. Supply all required JSON input fields, including evidence fields omitted from display. The helper kinds `MERGE_PENDING` and `MERGE_VERIFIED` render `MERGE` and `VERIFIED` respectively. Use full Git SHAs for machine evidence and Git-generated unambiguous short SHAs for other prose. Keep failure details sufficient to resume; never replace evidence with a success claim.
