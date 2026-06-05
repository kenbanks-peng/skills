---
name: git-managed-plan-execution
description: Execute existing multi-phase implementation plans from disk using mandatory CRON scheduling, git branches/worktrees, local verification, checkpoint commits, and durable phase status in the plan file.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [git, implementation, execution, branches, worktrees, cron]
    related_skills: [subagent-driven-development, github-repo-management]
---

# Git-Managed Plan Execution

## Purpose

Execute an existing multi-phase plan from disk through CRON. The plan file is canonical.

Do not create PRs, poll CI, merge branches, clean worktrees, or run destructive git commands unless the user explicitly asks.

## Use When

Use only when an existing multi-phase plan file exists and CRON execution is required or already configured.

## Tools

- File tools: read and patch plan files.
- Terminal: git and local verification.
- `todo`: session tracking only.
- `delegate_task`: optional isolated implementation or review.
- `cronjob`: required.

## Plan Requirements

The plan must include:

- Repository path or repo-relative paths.
- Plan slug.
- Base branch, or permission to discover it.
- Sequential or parallel mode.
- Branch strategy.
- Worktree strategy for parallel mode.
- Phase list with scope, files, steps, verification, and commit keyword.
- Dependencies or file ownership for parallel mode.
- Stop conditions.
- Local verification commands.
- `## CRON Bootstrap` with schedule, job identity, run limits, delivery target, and self-stop action.
- Bottom `## Phase Status` table.

If CRON state is missing or incomplete, bootstrap CRON first and stop. There is no non-CRON path.

## Phase Status

Every plan ends with:

```markdown
## Phase Status

| Number | Title | Status |
| -----: | ----- | ------ |
|      1 | Example phase | TODO |
```

Valid statuses: `TODO`, `IN PROGRESS`, `DONE`, `DEFERRED`, `FAILED`, `BLOCKED`, `SKIPPED`.

Allowed transitions:

- `TODO -> IN PROGRESS -> DONE`
- `TODO/IN PROGRESS -> DEFERRED`
- `IN PROGRESS -> FAILED`
- `TODO/IN PROGRESS -> BLOCKED`
- `TODO -> SKIPPED`

Sequential mode may update the table directly. In parallel mode, only the orchestrator updates the canonical table on the plan branch. Stop on table conflicts.

## Git Rules

Preflight:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```

Rules:

- Stop on unrelated uncommitted changes.
- Validate generated branch names with `git check-ref-format --branch`.
- Plan branch: `plan/<slug>`.
- Phase branch: `plan/<slug>-phase-<NN>`.
- Sequential mode uses the plan branch unless overridden.
- Parallel mode uses one phase branch and one worktree per phase.
- Never run two workers in one worktree.
- Never assign overlapping file scopes unless the plan allows it.
- Do not remove worktrees with uncommitted changes.

## CRON Bootstrap

If `## CRON Bootstrap` is absent or incomplete:

1. Collect or derive required parameters.
2. Create the CRON job.
3. Record concrete bootstrap state in the plan.
4. Update any CRON bootstrap status row.
5. Commit if appropriate.
6. Report the job id/name/schedule.
7. Stop.

Required parameters:

- schedule
- repo path and plan path
- execution mode
- branch strategy and worktree pattern
- max phases per run; sequential default is `1`
- verification commands
- delivery target
- self-stop identity
- self-stop action: default `pause`; use `remove` only if requested

Required section:

```markdown
## CRON Bootstrap

Status: enabled
Job name: run-<plan-slug>
Job id: <id-or-unknown>
Schedule: <schedule>
Max phases per run: 1
Self-stop action: pause
Delivery target: <target>
```

## CRON Prompt

The CRON prompt must include repo path, plan path, mode, branch/worktree strategy, max phases per run, verification commands, commit format, valid statuses, terminal statuses, self-stop identity/action, and these rules:

1. Do not ask questions. Stop and report missing or ambiguous input.
2. Re-read the plan before selecting work.
3. Run git preflight.
4. Stop on unrelated uncommitted changes.
5. Require complete CRON bootstrap state.
6. Sequential mode executes at most one `TODO` phase per tick.
7. Parallel mode uses only independent phases, distinct branches, and distinct worktrees.
8. Use local verification only.
9. Do not create PRs, poll CI, merge, clean worktrees, or run destructive commands unless authorized.
10. Do not auto-resolve branch, worktree, merge, or status-table conflicts.
11. On complete verified plans, pause this CRON job by default; remove it only if configured.

End-of-run report: phase attempted, result, verification, commit, completion result, CRON action, next action.

Add `delegation` to CRON `enabled_toolsets` only when subagents may be used. Include `cronjob`.

## Execution Workflow

1. Read the plan from disk.
2. Parse `## Phase Status` and dependency/file metadata.
3. Run git preflight.
4. Stop on unrelated uncommitted changes.
5. Ensure CRON bootstrap is complete.
6. Select the next eligible phase:
   - sequential: first `TODO`; stop if any phase is `IN PROGRESS`
   - parallel: a `TODO` phase marked independent
7. Create or switch to the required branch/worktree.
8. Mark `IN PROGRESS` only when claiming work.
9. Execute only scoped phase work.
10. Run verification.
11. Mark `DONE`, `FAILED`, `BLOCKED`, or `DEFERRED` with a short note.
12. Inspect diffs.
13. Commit scoped verified changes.
14. Re-check `git status --short`.
15. Run completion verifier.

## Delegation

Parent orchestrator owns verification, commits, and status updates.

Subagents receive repo/worktree path, branch, phase scope, expected files, forbidden files, dependencies, verification commands, commit format, and the ban on PRs, CI polling, merge automation, destructive git commands, and cleanup.

Parallel subagents must use distinct worktrees and non-overlapping scopes. They must not update the canonical status table.

## Commit Protocol

Commit at least once per completed phase.

Format:

```text
plan:<plan-slug> phase:<N> <keyword>
```

Rules:

- Keep messages terse.
- Include plan slug and phase number.
- Commit only scoped verified changes.
- Inspect status/diffs before commit and status after commit.

## Completion Verifier

Run at checkpoints and every CRON tick. It is read-only except CRON self-stop.

Steps:

1. Re-read the plan.
2. Parse the bottom `## Phase Status` table.
3. Determine terminal statuses. Default: every phase must be `DONE`.
4. Run configured verification commands.
5. Check `git status --short`.
6. Decide complete, incomplete, or ambiguous.

Do not implement work, start phases, review broadly, rewrite code, reconcile branches, create CRON jobs, or make speculative fixes.

## Reconciliation and Cleanup

Do not reconcile branches or clean worktrees automatically.

Before user-authorized reconciliation, report branches, worktrees, commits, verification results, files changed, and likely conflicts.

Stop on status-table conflicts. Do not remove dirty worktrees.

## Stop Conditions

Stop on failed verification without an obvious scoped fix, missing input, user authorization required, unrelated uncommitted changes, destructive git action, unauthorized merge/reconciliation, ambiguous parallel ownership, or unresolved conflict.
