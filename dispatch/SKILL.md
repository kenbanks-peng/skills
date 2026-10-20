---
name: dispatch
description: Use when the user explicitly requests dispatch to run coding tasks with Workmux workers and Aven tracking, or to resume a dispatch run.
---

# Dispatch

Coordinate implementation through verified completion or a durable handoff. Use the
`tasks` skill for Aven mechanics and selective notes. Run commands from the target
repository; replace `<skill-directory>` below with this skill's absolute path.
Helpers require Python 3.10+, Git, and POSIX; arrange acceptance-check dependencies
on the dispatcher as well as the worker.

## Safety contract

- Dispatch owns status, assignment, review, integration, and closure; workers own
  implementation and RESULT/BLOCKED reports. Workmux `done` only ends a turn.
- Parallel implementation needs disjoint write scopes. Serialize repository
  lifecycle mutations; helpers share a common-Git-directory lock. Exclude other
  Git writers through integration and finish.
- Review the actual diff and commits against acceptance criteria. Require
  independent checks of the integrated base, exact confirmed worker exit before
  destructive cleanup or completion, and durable reporting before closure.
- Preserve resources on uncertainty. Task completion and resource removal are
  distinct outcomes: retained resources need identity, evidence, owner, and next
  action. Tabs and empty-parent removal are best-effort housekeeping.

## 1. Select and launch

Reuse tasks with acceptance criteria and write scopes; express ordering with
Aven dependencies. Ask before initializing a missing Git repository.

```sh
aven list --ready
aven context APP-1234
python3 <skill-directory>/scripts/dispatch.py launch APP-1234 \
  --base main --scope src/ --scope tests/ \
  --check '["python3", "-m", "unittest"]'
```

Repeat `--scope` and `--check` for the assignment. The default uses
`~/.config/workmux/agents.linux.yaml` with sandboxing, Apple `container` on macOS
and Docker on Linux, and Herdr when `HERDR_ENV=1`, otherwise the active tmux
session. Missing setup is a blocker, not permission to run locally.

Require `ok: true`, then mark active with the returned `agent_type` and append a
`DISPATCH:` note linking the returned handle and recovery record (use `tasks`
for the Aven commands). The launch command loads task context, pins the explicit local base, creates the prompt, and saves
identity and evidence under `<common-git-dir>/dispatch-workers/APP-1234/worker.json`.
The worker receives its actual guest path; caller-managed identity files are not
needed. Keep this evidence outside worker worktrees for recovery.

## 2. Monitor and review

```sh
workmux wait <returned-handle> --any --timeout 120
workmux status --json
python3 <skill-directory>/scripts/dispatch_cli.py report --task APP-1234
```

Track every unresolved handle. Give the enclosing tool more than 120 seconds;
a timeout calls for inspection. Handle waiting/finished workers before waiting
again. Review the selected RESULT, current commits, actual diff, acceptance
criteria, and check evidence. Missing or invalid reports block integration;
return incomplete work to the worker. The report supplies `worker_commit` and
`note.id` for the next step. Capture terminal output only for diagnosis.

## 3. Integrate

```sh
python3 <skill-directory>/scripts/integrate.py APP-1234 \
  --reviewed-commit <reviewed-worker-SHA> --result-id <reviewed-RESULT-note-ID>
```

Require `ok: true`. This operation validates the reviewed report and saved
identity, rebases, checks the resulting commit, integrates with hooks enabled
and the worker retained, and independently checks the pinned integrated base.
Revisions and check logs are saved automatically. On failure or interruption,
load [recovery.md](recovery.md) before another mutation.

## 4. Finish

```sh
python3 <skill-directory>/scripts/finish_worker.py APP-1234
python3 <skill-directory>/scripts/finish_worker.py APP-1234 --authorize-finish
```

Review the first command's plan; authorize once. Finish rechecks integration and
verification, confirms exact worker exit, archives eligible generated prompts,
attempts strict resource cleanup, saves a VERIFIED report in Aven, then marks done
and clears the agent. Inspect the separate `delivered`, `task_complete`,
`pending_cleanup`, and `housekeeping` outcomes. Integrated, independently verified
work with confirmed exit and durable reporting permits completion even when safe
resources remain. Unknown exit, stale verification, or failed reporting blocks it.

## 5. Close or hand off

Query ready work again with the run's filters. Create or reuse follow-ups and
separate current-run work from deferred backlog. Task checks need not be repeated
as an extra run-wide gate; run any explicitly required final-run checks against
the final pinned base (use `verify_base.py --help` if a separate check is needed).

Append one `SUMMARY:` on the epic or designated task: delivered work and checked
revision; unresolved work and owner/next action; pending resource cleanup; and
housekeeping separately. Include saved record/evidence links so another dispatcher
can resume, including cleanup for completed tasks. On a blocker, retain a BLOCKED
report locally if Aven fails and restore durable reporting before integration or
completion. Use the `tasks` policy rather than rendering note templates. For a
file-backed handoff:

```sh
aven note <run-epic-or-designated-task> --file <handoff-file>
```

## Load only when triggered

- **Resume or uncertain state:** [recovery.md](recovery.md), including completed
  tasks with pending cleanup. Reconcile the full tracked set after interruption.
- **Explicitly approved unsandboxed execution:** [local-worker.md](local-worker.md).
- **Nondefault runtime or UI:** [runtime.md](runtime.md) for the relevant adapter;
  optional tasks views live there too.
- **Diagnosed Aven routing failure:** [troubleshooting.md#routing](troubleshooting.md#routing).
- **Unsupported CLI behavior or tool change:** [troubleshooting.md#capabilities](troubleshooting.md#capabilities).
