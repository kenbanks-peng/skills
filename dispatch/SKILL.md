---
name: dispatch
description: Use when the user explicitly requests dispatch to run coding tasks with Workmux workers and Aven tracking, or to resume a dispatch run.
---

# Dispatch

Coordinate implementation through verified completion or a durable handoff. Use the `tasks` skill for Aven mechanics and selective notes. Run commands from the target repository; replace `<skill-directory>` below with this skill's absolute path. Helpers require Python 3.10+, Git, and POSIX; arrange acceptance-check dependencies on the dispatcher as well as the worker.

## Safety contract

- Dispatch owns status, assignment, review, integration, and closure; workers own implementation and RESULT/BLOCKED reports. A worker RESULT or Workmux `done` ends a turn, not the Aven task.
- Parallel implementation needs disjoint write scopes. Serialize repository lifecycle mutations; helpers share a common-Git-directory lock. Exclude other Git writers through integration and finish.
- Review the actual diff and commits against acceptance criteria. Require independent checks of the integrated base, exact confirmed worker exit before destructive cleanup or completion, and durable reporting before closure.
- Preserve resources on uncertainty. Task completion and resource removal are distinct outcomes: retained resources need identity, evidence, owner, and next action. Tabs and empty-parent removal are best-effort housekeeping.

## 1. Select and launch

Reuse tasks with clear requirements and acceptance criteria; express ordering with Aven dependencies. Ask before initializing a missing Git repository.

```sh
aven list --ready
aven context APP-1234
# Once dispatch is requested, in the original host terminal (never during intake):
python3 <skill-directory>/scripts/dispatch.py startup APP-1234
python3 <skill-directory>/scripts/dispatch.py launch APP-1234 \
  --base main \
  --check '["python3", "-m", "unittest"]'
```

Require startup `ok: true` before launching workers. Startup names the dispatcher and opens one run-owned Aven tab at the target repository's Git top-level, using the dispatcher's original database, workspace, and project. Use a designated run task (or `--run-id <stable-id>`) consistently on resume; repeat startup reuses the saved exact UI identity, not a matching label. Supply the same diagnosed `--db`/`--workspace` overrides as other dispatch commands. Preserve the returned `record_path`; interrupted startup requires [runtime.md](runtime.md#dispatch-startup-and-aven-tab).

Repeat `--check` for required checks. The worker prompt contains work location, Aven context, and the worker contract with required checks. Task requirements belong in Aven, not separate prompt fields. The default uses `~/.config/workmux/agents.linux.yaml` with sandboxing, Apple `container` on macOS and Docker on Linux, and Herdr when `HERDR_ENV=1`, otherwise the active tmux session. Missing setup is a blocker, not permission to run locally.

Require `ok: true` (confirmed launch), then mark active using `aven edit <task-ref> --status active`; read `aven context <task-ref> --json` with the same routing to confirm the write. Append a `DISPATCH:` note linking the returned handle and recovery record (use `tasks` for selective notes). A failed status write is a blocker to reconcile, not permission to relaunch. The observed `agent_type` is saved in the worker record, not an Aven agent field. Current Aven has no agent field or clear-agent option; on versions exposing one, clear it with supported CLI options when leaving active. Session identity belongs only in saved recovery evidence. If assignment metadata is needed, follow the `tasks` policy and use supported Aven metadata options. The launch command loads task context, pins the explicit local base, creates the prompt, and saves identity and evidence under `<common-git-dir>/dispatch-workers/APP-1234/worker.json`. The worker receives its actual guest path; caller-managed identity files are not needed. Keep this evidence outside worker worktrees for recovery.

## 2. Monitor and review

```sh
workmux wait <returned-handle> --any --timeout 120
workmux status --json
python3 <skill-directory>/scripts/dispatch_cli.py report --task APP-1234
```

Track every unresolved handle. Give the enclosing tool more than 120 seconds; a timeout calls for inspection. Handle waiting/finished workers before waiting again. Review the selected RESULT, current commits, actual diff, acceptance criteria, and check evidence. Missing or invalid reports block integration; return incomplete work to the worker. The report supplies `worker_commit` and `note.id` for the next step. Capture terminal output only for diagnosis.

## 3. Integrate

```sh
python3 <skill-directory>/scripts/integrate.py APP-1234 \
  --reviewed-commit <reviewed-worker-SHA> --result-id <reviewed-RESULT-note-ID>
```

Require `ok: true`. This operation validates the reviewed report and saved identity, rebases, checks the resulting commit, integrates with hooks enabled and the worker retained, and independently checks the pinned integrated base. Revisions and check logs are saved automatically. On failure or interruption, load [recovery.md](recovery.md) before another mutation.

## 4. Finish

```sh
python3 <skill-directory>/scripts/finish_worker.py APP-1234
python3 <skill-directory>/scripts/finish_worker.py APP-1234 --authorize-finish
```

Review the first command's plan; authorize once. Finish rechecks integration and verification, confirms exact worker exit, archives eligible generated prompts, attempts strict resource cleanup, saves a VERIFIED report in Aven, then marks done with `aven edit <task-ref> --status done` and confirms live status through Aven context. The saved worker record retains the observed `agent_type` for recovery. Inspect the separate `delivered`, `task_complete`, `pending_cleanup`, and `housekeeping` outcomes. Integrated, independently verified work with confirmed exit and durable reporting permits completion even when safe resources remain. Unknown exit, stale verification, failed reporting, or unconfirmed Aven status blocks it. Finish saves the error, dispatcher owner, recovery action, and local `finish-blocked.md`; restore failed Aven reporting before claiming closure.

### Status transitions (dispatcher-owned)

| Transition | Required evidence |
| --- | --- |
| Ready task → active | Confirmed successful launch, then successful status write and readback. |
| Active → active during review/integration or a blocker | RESULT/Workmux turn completion alone is insufficient. Record blocker, owner, and next action; `BLOCKED:` is a report, not an Aven status. |
| Active → done | Reviewed integration, independent acceptance verification, exact worker exit, durable VERIFIED report, successful status write and readback. |
| Done with pending cleanup → done | Retry safe cleanup separately; retain resource identity, evidence, owner, and next action. Automatic cleanup remains part of normal finish. |
| Explicit handoff/cancellation | Record delivery state, blocker, owner, and next action; use only supported Aven statuses and confirm any authorized write. |

Retries reconcile live status against saved evidence. A saved successful action alone cannot prove current status; an interrupted write already observed done need not be repeated.

## 5. Close or hand off

Query ready work again with the run's filters. Create or reuse follow-ups and separate current-run work from deferred backlog. Task checks need not be repeated as an extra run-wide gate; run any explicitly required final-run checks against the final pinned base (use `verify_base.py --help` if a separate check is needed).

Before final handoff, reconcile every tracked task against saved records and Aven context, including done tasks with pending cleanup; see [recovery.md](recovery.md). Never bulk-mark active tasks done. Append one `SUMMARY:` on the epic or designated task: delivered work and checked revision; unresolved work and owner/next action; every remaining active task with its blocker, owner, and next action (or explicitly none); pending resource cleanup; and housekeeping separately. Include saved record/evidence links so another dispatcher can resume, including cleanup for completed tasks. On a blocker, retain a BLOCKED report locally if Aven fails and restore durable reporting before integration or completion. Use the `tasks` policy rather than rendering note templates. For a file-backed handoff:

```sh
aven note <run-epic-or-designated-task> --file <handoff-file>
```

When all run work, resource cleanup, and final SUMMARY reporting are finished, close the saved Aven tab before the final response:

```sh
python3 <skill-directory>/scripts/dispatch.py close-run <run-epic-or-designated-task> --authorize-close
```

Use the same `--run-id <stable-id>` as startup, if set. Require `ok: true` and `aven_closed: true`; otherwise report pending UI housekeeping. The dispatcher tab stays open. Keep Aven open during worker cleanup, resume, or a blocked/partial handoff. See [runtime.md](runtime.md#dispatch-startup-and-aven-tab) for safe closure and retry rules.

## Load only when triggered

- **Resume or uncertain state:** [recovery.md](recovery.md), including completed tasks with pending cleanup. Reconcile the full tracked set after interruption.
- **Explicitly approved unsandboxed execution:** [local-worker.md](local-worker.md).
- **Nondefault runtime/UI or interrupted startup:** [runtime.md](runtime.md) for the relevant adapter and saved run-owned Aven tab.
- **Diagnosed Aven routing failure:** [troubleshooting.md#routing](troubleshooting.md#routing).
- **Unsupported CLI behavior or tool change:** [troubleshooting.md#capabilities](troubleshooting.md#capabilities).
