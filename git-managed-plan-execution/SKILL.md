---
name: git-managed-plan-execution
description: Sequentially execute existing multi-phase implementation plans from disk using CRON scheduling, git branches/worktrees, local verification, checkpoint commits, and durable phase status in the plan file.
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

Sequentially execute an existing multi-phase plan from disk through CRON. The plan file is canonical.

Use this workflow when CRON should resume and advance plan phases across runs, with durable status recorded in the plan file.

The workflow is focused on local phase execution: selecting eligible work, making scoped changes, running local verification, updating durable phase status, and committing checkpoints.

## Tools

- File tools: read and patch plan files.
- Terminal: git and local verification.
- `todo`: session tracking only.
- `delegate_task`: optional isolated implementation or review.
- `cronjob`: required.

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

Update the table as each phase is claimed and completed. Before writing, confirm the table has not changed unexpectedly since it was read.

## Git Rules

Preflight:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```

Rules:

- Validate generated branch names with `git check-ref-format --branch`.
- Plan branch: `plan/<slug>`.
- Phase branch: `plan/<slug>-phase-<NN>`.
- Do not remove worktrees with uncommitted changes.

## CRON Bootstrap

If `## CRON Bootstrap` is absent or incomplete:

1. Collect or derive required parameters.
2. Create the CRON job.
3. Record concrete bootstrap state in the plan.
4. Update any CRON bootstrap status row.
5. Commit if appropriate.
6. Report the job id/name/schedule.
7. End the current run.

Required parameters:

- schedule
- repo path and plan path
- branch strategy and worktree pattern
- max phases per run; default is `1`
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

The CRON prompt must include:

- repo path and plan path
- CRON bootstrap state
- verification commands
- commit format
- self-stop identity and action

Each CRON run must re-read the plan, run git preflight, execute at most one eligible `TODO` phase, run local verification, update phase status, commit verified changes, and report the result.

When all phases are complete and verified, pause the CRON job by default; remove it only if configured.

## Execution Workflow

Each CRON tick executes at most one phase.

1. Read the plan from disk.
2. Parse the `## Phase Status` table.
3. Run git preflight.
4. Apply stop conditions to the git preflight result.
5. Ensure CRON bootstrap is complete.
6. Apply stop conditions to the phase status table.
7. Select the first `TODO` phase.
8. Mark the selected phase `IN PROGRESS`.
9. Execute only that phase's scoped work.
10. Run local verification.
11. Inspect diffs.
12. Commit scoped verified changes.
13. Update phase status:
    - `DONE` when verification passes and changes are committed
    - `FAILED` when verification fails
    - `BLOCKED` when required input or authorization is missing
    - `DEFERRED` when the phase should intentionally be postponed
14. Re-check `git status --short`.
15. Run completion verifier.

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

## CRON Shutdown

At the end of every CRON tick, check the `## Phase Status` table.

If every phase is `DONE`:

1. Run configured verification commands.
2. Check `git status --short`.
3. If verification passes and the worktree is clean, apply the configured self-stop action.
4. Record/report the shutdown result.

Default self-stop action is `pause`. Use `remove` only when configured.

## Cleanup

Do not clean worktrees, delete branches, merge branches, or run destructive git commands unless the user explicitly asks.

Before any user-authorized cleanup, report the current branches, worktrees, commits, changed files, and verification status.

## Stop Conditions

Stop and report when:

- required input is missing or ambiguous
- any phase is already `IN PROGRESS`
- the phase status table changed unexpectedly since it was read
- unrelated uncommitted changes are present
- verification fails without an obvious scoped fix
- user authorization is required
- a destructive git action would be needed
- a branch, worktree, merge, or plan-status conflict occurs
