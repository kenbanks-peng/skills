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

1. Run [integrate.py](scripts/integrate.py) with the full task reference, reviewed full worker commit, and latest reviewed RESULT note ID, using [merge.md](merge.md). The saved worker record supplies identity, explicit base, and required checks.
2. Require `ok: true`. The operation rebases, checks the exact resulting commit, integrates with hooks enabled and the worktree retained, then independently verifies the pinned base. It saves revisions and check logs automatically. No worker merge prompt or merge-response polling is needed.
3. On failure, keep the task active and worktree intact. Send conflicts or check failures for repair. After an attempted merge, use `--reconcile`; never repeat an uncertain merge blindly.
4. Review `finish_worker.py <full-ref>` and authorize the one plan with `--authorize-finish`, using [the finish procedure](runtime.md#stop-archive-and-clean-up). It reads the saved integration event, verifies exact worker exit, archives only known generated prompts, and attempts strict cleanup. It saves a durable Aven completion report before marking done and clearing the agent. Exclude other Git writers through completion.
5. Unknown exit, mismatched verification, base movement, changed identity, or a failed Aven write blocks completion. Safe retained resources do not: record their exact identity, evidence, owner, and next action as pending cleanup. Inspect with `finish_worker.py <ref> --inspect`; repeat the command without new authorization to resume. Never recreate removed resources.
6. Query ready tasks again using the run's filters. Create or reuse tasks for discovered work; distinguish current-run work from deferred backlog.

## 5. Close the run

1. Confirm all selected tasks are verified, merged, have confirmed worker exit, and have durable completion reports. List retained resources as pending cleanup, not removed. If acceptance requires identifying notes, require a committed manifest and persistent CI check for all exact notes using the [runtime procedure](runtime.md#persistent-identifying-note-checks). Use `verify_base.py` for the run-wide checks against the final base revision, supplying a retained verified worker commit. Passing task checks do not replace these.
2. Parent-directory removal is best-effort housekeeping. Use only `rmdir` on each recorded exact path; leave nonempty or unsafe directories intact. Report failures separately from task delivery and pending cleanup.
3. Attempt to close this run's tasks view using its recorded resource ID and the [runtime cleanup procedure](runtime.md#dispatch-and-tasks-tabs). Closure failure is housekeeping, not a task or delivery gate. Keep its identity and next action in the handoff.
4. Render and append one `SUMMARY` note on the run's epic, or a designated task when there is no epic. State delivered work, pending cleanup, and housekeeping separately. Completion does not imply that all resources are gone.

## Evidence notes

Every dispatch-written note or comment starts with a standard CAPS prefix followed by a colon. Use one lead sentence and at most three short bullets (normally under 80 words); recovery blockers may exceed this when necessary. Write plain, scannable text with one fact per bullet.

Record only the new event. Keep recovery coordinates in DISPATCH and shared settings in one run-context note; refer back to them. Omit the attached task's own ref, unchanged state, routine commands, and lifecycle recaps. Summarize distinct checks by outcome; retain commands, logs, full SHAs, and resource identity in evidence files and link them. Display home paths with `~`.

- `ACTIVITY:` — shared run context, a material decision, review/authorization, or recovery update. State what changed and why; routine polling needs no note.
- `DISPATCH` — worker recovery coordinates and launch revision; reference shared run context.
- `RESULT` — delivered change, commit, acceptance/check results, and exceptions.
- `MERGE` — optional dispatch integration summary; link the saved integration event and exact checked revisions. No worker response is required.
- `VERIFIED` — independently tested base revision, check results, confirmed writer exit, pending cleanup, and housekeeping. The finish operation writes this note directly from saved evidence. Do not claim retained resources are gone.
- `BLOCKED` — blocker first, then recovery evidence, responsible party, and next action.
- `SUMMARY` — delivered outcome, final verified revision, run-wide check results, and follow-up refs; leave lifecycle history in earlier notes.

The finish operation writes its own completion report; it does not use the legacy cleanup-required `MERGE_VERIFIED` renderer. For other notes, use [render_note.py](scripts/render_note.py) and its `--help` to render transition notes from the [templates](templates). Review for relevance and add material decisions or exceptions before appending through `tasks`. Supply all required JSON input fields, including evidence fields omitted from display. The helper kinds `MERGE_PENDING` and `MERGE_VERIFIED` render `MERGE` and `VERIFIED` respectively. Use full Git SHAs for machine evidence and Git-generated unambiguous short SHAs for other prose. Keep failure details sufficient to resume; never replace evidence with a success claim.
