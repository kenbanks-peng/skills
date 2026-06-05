---
name: git-managed-plan-execution
description: Use when executing existing multi-phase implementation plans from disk through scheduled Hermes cron runs, with git branches/worktrees, local verification, checkpoint commits, and durable phase status in the plan file.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [git, implementation, execution, branches, worktrees, cron]
    related_skills: [writing-plans, subagent-driven-development, github-repo-management]
---

# Git-Managed Plan Execution

## Overview

Sequentially execute an existing multi-phase plan from disk through CRON. The plan file is canonical.

Use this workflow when CRON should resume and advance plan phases across runs, with durable status recorded in the plan file.

The workflow is focused on local phase execution: selecting eligible work, making scoped changes, running local verification, updating durable phase status, and committing checkpoints.

## When to Use

Use this skill when:

- The user has an existing implementation plan on disk.
- The plan has multiple phases that should be executed sequentially.
- CRON should resume and advance plan phases across runs.
- Progress must survive across sessions and agent runs.
- Git commits should checkpoint each completed phase.
- The plan file should remain the canonical status source.

Do not use this skill when:

- The user only wants a one-off plan review.
- The task has no durable plan file.
- The user wants immediate interactive execution only, with no scheduled continuation.
- Destructive git cleanup, branch deletion, merging, or worktree removal is required without explicit authorization.

## Tools

- File tools: read and patch plan files.
- Terminal: git and local verification.
- `todo`: session tracking only.
- `delegate_task`: optional isolated implementation or review.
- `cronjob`: required.

## Plan File Contract

The plan file must contain:

- A durable `## Phase Status` table.
- A stable phase number and title for each executable phase.
- Enough phase detail elsewhere in the plan to identify scoped work.
- Optional `## CRON Bootstrap` state once scheduled execution is enabled.

Phase selection is based on the `## Phase Status` table. Phase implementation scope is based on the matching numbered/title phase content in the plan.

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

CRON bootstrap is an initiating handoff, not an execution tick.

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

After creating or starting the CRON job, recording `## CRON Bootstrap`, updating any bootstrap status row, and reporting the job id/name/schedule, the initiating agent is done. Do not execute an implementation phase in the same run unless the user explicitly requested bootstrap plus immediate execution.

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

## Common Pitfalls

1. Treating the session todo list as durable state.
   The plan file is canonical. `todo` is only for the current run.

2. Running more than one phase per CRON tick.
   Default to one eligible `TODO` phase per run unless the bootstrap state explicitly says otherwise.

3. Forgetting to end after CRON bootstrap.
   The initiating run should create/start the CRON job, record bootstrap state, commit if appropriate, report the job, and stop.

4. Updating phase status without re-reading the table.
   Before patching the plan, confirm the `## Phase Status` table has not changed unexpectedly.

5. Committing unrelated changes.
   Inspect `git status --short` and diffs before every commit. Stop if unrelated changes are present.

6. Pausing or removing the wrong CRON job.
   Use the recorded job id/name from `## CRON Bootstrap`; list jobs when identity is uncertain.

7. Performing cleanup too early.
   Do not delete branches, remove worktrees, merge, reset, or clean unless explicitly authorized.

## Verification Checklist

- [ ] Plan file was re-read from disk.
- [ ] `## Phase Status` table parsed successfully.
- [ ] Git preflight completed.
- [ ] No unrelated uncommitted changes were present.
- [ ] CRON bootstrap state is complete.
- [ ] At most one eligible `TODO` phase was selected.
- [ ] Selected phase was marked `IN PROGRESS` before work began.
- [ ] Local verification commands were run.
- [ ] Diffs were inspected before commit.
- [ ] Scoped verified changes were committed.
- [ ] Phase status was updated to `DONE`, `FAILED`, `BLOCKED`, `DEFERRED`, or `SKIPPED`.
- [ ] Final `git status --short` was checked.
- [ ] Completion/shutdown conditions were evaluated.
- [ ] CRON job pause/remove action was applied only when configured and safe.
