---
name: dispatch
description: Use when the user explicitly requests dispatch to run coding tasks with Workmux workers and Aven tracking, or to resume a dispatch run.
---

# Dispatch

Coordinate implementation through verified completion or a durable handoff. Use the `tasks` skill for Aven mechanics. Run commands from the target repository; replace `<skill-directory>` below with this skill's absolute path.

## Coordination

- Own status, assignment, review, integration, and closure. Assign implementation and RESULT/BLOCKED reporting to workers. Keep tasks active after a worker RESULT or Workmux `done` until completion requirements are met.
- Give parallel workers disjoint write scopes. Serialize repository lifecycle mutations through the helpers' common-Git-directory lock. Exclude other Git writers through integration and finish.

## 1. Select and launch

Add tasks with clear requirements and acceptance criteria; express ordering with Aven dependencies. Group tasks with epics rather than labels. Ask before initializing a missing Git repository.

Run startup only after dispatch is requested, in the original host terminal, never during intake:

```sh
aven list --ready
aven context APP-1234
python3 <skill-directory>/scripts/dispatch.py startup APP-1234
python3 <skill-directory>/scripts/dispatch.py launch APP-1234 \
  --base main \
  --check '["python3", "-m", "unittest"]'
```

Startup and launch must use the same run ID. It defaults to the command's task ref; for multiple worker tasks, pass `--run-id <stable-id>` to startup and every launch. Launch verifies successful startup and the saved open Aven tab. Resume uses the worker's saved run ID. Reuse exact tab identity rather than matching by label. Preserve the returned `record_path`. For interrupted startup, load [runtime.md](runtime.md#dispatch-startup-and-aven-tab).

Repeat `--check` for required checks. Put task requirements in Aven rather than separate prompt fields. Pass `--platform darwin` when macOS workers are requested; otherwise launch defaults to `linux`. Let the script manage configuration, runtime selection, and UI routing. Treat script failures as blockers.

Require launch `ok: true`: the script confirms worker identity, sets active when needed, and reads Aven context to confirm the status. It saves the worker in the run index. If activation fails, use `dispatch.py inspect <task-ref> --resume`; it reads live status before any retry and never creates a replacement. Append a `DISPATCH:` note linking the returned handle and recovery record; use `tasks` for selective notes.

Keep session identity and the observed `agent_type` in saved recovery evidence. Use the `tasks` policy and supported Aven metadata options for assignment metadata. On Aven versions exposing an agent field, clear it with supported CLI options when leaving active. Preserve the launch-generated evidence at `<common-git-dir>/dispatch-workers/APP-1234/worker.json`, outside worker worktrees. Use the generated worker prompt and guest path rather than caller-managed identity files.

## 2. Monitor and review

```sh
workmux wait <returned-handle> --any --timeout 120
workmux status --json
python3 <skill-directory>/scripts/dispatch_cli.py report --task APP-1234
```

Track every unresolved handle. Give the enclosing tool more than 120 seconds; inspect workers after a timeout. Handle waiting/finished workers before waiting again. Review the selected RESULT, current commits, actual diff, acceptance criteria, and check evidence. Block integration for missing or invalid reports; return incomplete work to the worker. Save the report's `worker_commit` and `note.id` for integration. Capture terminal output only for diagnosis.

## 3. Integrate

```sh
python3 <skill-directory>/scripts/integrate.py APP-1234 \
  --reviewed-commit <reviewed-worker-SHA> --result-id <reviewed-RESULT-note-ID>
```

Require `ok: true`. Preserve saved revisions and check logs. On failure or interruption, load [recovery.md](recovery.md) before another mutation.

## 4. Finish

```sh
python3 <skill-directory>/scripts/finish_worker.py APP-1234
python3 <skill-directory>/scripts/finish_worker.py APP-1234 --authorize-finish
```

Review the first command's plan; authorize once. Inspect the separate `delivered`, `task_complete`, `pending_cleanup`, and `housekeeping` outcomes. Require reviewed integration, independent acceptance verification, exact worker exit, a durable VERIFIED report, and confirmed Aven done status before claiming completion. Permit completion with pending safe resource cleanup only when all completion requirements are met. For blocked finish, inspect the saved error, dispatcher owner, recovery action, and local `finish-blocked.md`. Restore failed Aven reporting before claiming closure.

### Enforce status transitions

- **Ready → active:** Launch/resume enforces confirmed launch, status write when needed, and readback.
- **Active → active during review, integration, or a blocker:** Record the blocker, owner, and next action. Record `BLOCKED:` as a report, not an Aven status.
- **Active → done:** Enforce the finish requirements above.
- **Done with pending cleanup → done:** Retry safe cleanup separately; retain resource identity, evidence, owner, and next action. Include automatic cleanup in normal finish.
- **Explicit handoff/cancellation:** Record delivery state, blocker, owner, and next action. Use only supported Aven statuses and confirm any authorized write.

On retries, reconcile live status against saved evidence. Confirm current status rather than relying on a saved successful action. Skip an interrupted status write if live status already confirms done.

## 5. Close or hand off

Query ready work again with the run's filters. Create or reuse follow-ups and separate current-run work from deferred backlog. Run explicitly required final-run checks against the final pinned base; use `verify_base.py --help` if a separate check is needed. Do not repeat task checks as an extra run-wide gate.

Before final handoff, reconcile every tracked task against saved records and Aven context, including done tasks with pending cleanup; see [recovery.md](recovery.md). Never bulk-mark active tasks done. Append one `SUMMARY:` on the epic or designated task containing:

- Delivered work and checked revision.
- Unresolved work and owner/next action.
- Every remaining active task with its blocker, owner, and next action, or explicitly none.
- Pending resource cleanup.
- Housekeeping, separately.
- Saved record/evidence links for resuming work and cleanup of completed tasks.

On a blocker, retain a BLOCKED report locally if Aven fails and restore durable reporting before integration or completion. Use the `tasks` policy rather than rendering note templates. For a file-backed handoff:

```sh
aven note <run-epic-or-designated-task> --file <handoff-file>
```

When all run work, resource cleanup, and final SUMMARY reporting are finished, close the saved Aven tab before the final response:

```sh
python3 <skill-directory>/scripts/dispatch.py close-run <run-epic-or-designated-task> --authorize-close
```

Use the same `--run-id <stable-id>` as startup, if set. Closure checks the run index and saved workers, live done status, retained delivery ancestry, absent worker resources, completed cleanup/housekeeping, and a SUMMARY note added since startup. Missing evidence blocks closure. Final SUMMARY content and work outside the saved run remain dispatcher review decisions. Require `ok: true` and `aven_closed: true`; otherwise report pending UI housekeeping. Leave the dispatcher tab open. Keep Aven open during worker cleanup, resume, or a blocked/partial handoff. See [runtime.md](runtime.md#dispatch-startup-and-aven-tab) for safe closure and retry rules.

## Load only when triggered

- **Resume or uncertain state:** [recovery.md](recovery.md), including completed tasks with pending cleanup. Reconcile the full tracked set after interruption.
- **Nondefault runtime/UI or interrupted startup:** [runtime.md](runtime.md) for the relevant adapter and saved run-owned Aven tab.
- **Diagnosed Aven routing failure:** [troubleshooting.md#routing](troubleshooting.md#routing).
- **Unsupported CLI behavior or tool change:** [troubleshooting.md#capabilities](troubleshooting.md#capabilities).
