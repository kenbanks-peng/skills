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
4. Write and append a `DISPATCH` note with the worker handle and saved recovery-record link. For resumed workers, retain the original launch evidence. Use optional `ACTIVITY:` notes on the run epic or designated task for consequential shared decisions; the saved records already retain routine settings and coordinates.

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

1. Confirm all selected tasks are verified, merged, have confirmed worker exit, and have durable completion reports. List retained resources as pending cleanup, not removed. Project-specific checks belong in explicit task acceptance criteria. Use `verify_base.py` for the run-wide checks against the final base revision, supplying a retained verified worker commit. Passing task checks do not replace these.
2. Parent-directory removal is best-effort housekeeping. Use only `rmdir` on each recorded exact path; leave nonempty or unsafe directories intact. Report failures separately from task delivery and pending cleanup.
3. If a tasks view was opened, attempt to close it using its recorded resource ID and the [runtime cleanup procedure](runtime.md#optional-tasks-views). Closure failure is housekeeping, not a task or delivery gate. Keep its identity and next action in the handoff.
4. Write and append one `SUMMARY` note on the run's epic, or a designated task when there is no epic. State delivered work, pending cleanup, and housekeeping separately. Completion does not imply that all resources are gone.

## Evidence notes

Use the `tasks` selective-note policy and write notes directly. Helpers return recovery-record paths, revisions, and check evidence; no note parameters or formatter are required.

Three routine events:
- `DISPATCH:` — worker handle and durable recovery-record link.
- `RESULT:` — delivered change, Git-verified commit, check outcome, and relevant exceptions.
- `VERIFIED:` — integrated revision, independent checks, confirmed worker exit, and remaining cleanup. Finish writes this from saved evidence before marking done.

Use `BLOCKED:` for exceptions and optional `ACTIVITY:` notes for consequential decisions. Write one `SUMMARY:` per run. Preserve failed report text locally and surface Aven write failures; restore required durable reporting before merge or completion. Notes provide evidence, not authority to delete resources.
