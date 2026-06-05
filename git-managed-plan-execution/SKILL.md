---
name: git-managed-plan-execution
description: Use to execute existing multi-phase implementation plans in a git environment using a CRON job.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags:
      [git, implementation, execution, branches, worktrees, cron, delegation]
    related_skills: [subagent-driven-development, github-repo-management]
---

# Git-Managed Plan Execution

## Purpose

Execute existing multi-phase implementation plans through a mandatory CRON schedule that future runs can resume from disk. The plan file is the durable control surface; local git repo provides coordination through branches, worktrees when needed, checkpoint commits, and local verification.

This skill is local-only. It does not create PRs, watch CI, merge branches, clean worktrees, or run destructive git operations unless the user explicitly asks.

## Use When

- A user has an existing implementation plan that should be executed or resumed from disk by scheduled CRON runs.
- Work should proceed through named phases, branches, and checkpoint commits.
- Independent phases need isolated worktrees for subagents or CRON runs.

Do not use unless an existing multi-phase plan file is available and CRON scheduling will be configured or is already configured in that plan.

## Tool Use

- File tools: read, patch, and search existing plan/skill files.
- Terminal: git state, tests, lint, validation, and local smoke checks.
- `todo`: session-local tracking only; durable phase status stays in the plan.
- `delegate_task`: isolated implementation or review when helpful.
- `cronjob`: required for CRON bootstrap, job inspection, and self-stop.

## Operating Model

1. The plan is self-contained. Future executors need the repository and plan file, not chat history.
2. Discover state before acting; do not assume the base branch is `main`.
3. Follow branch, worktree, phase, verification, and stop rules already recorded in the plan.
4. Keep the bottom `## Phase Status` table as the canonical status surface.
5. Run only from a self-contained CRON prompt after the interactive bootstrap has recorded concrete schedule state.
6. Commit only scoped, verified work. Prefer one commit per completed phase.
7. Stop before ambiguity, unrelated changes, destructive actions, unauthorized merges, or failed verification without an obvious in-scope fix.

## Existing Plan Requirements

Before executing, confirm the existing plan includes enough information to run safely:

- Goal and scope, including out-of-scope work.
- Repository path or explicit repo-relative paths.
- Plan slug.
- Base branch from `git branch --show-current`, unless overridden.
- Execution mode.
- Branch strategy:
  - plan branch: `plan/<slug>`
  - phase branch: `plan/<slug>-phase-<NN>`
  - any user branch override
- Worktree strategy; required for parallel execution.
- Phase list with files/scope, steps, verification, and commit keyword.
- Dependency or file-ownership metadata when phases may run in parallel.
- Local verification commands.
- Concrete `## CRON Bootstrap` state, including schedule, job identity, run limits, delivery target, and self-stop action.
- Stop conditions.
- Explicit exclusions: no PR, CI polling, merge automation, destructive cleanup, or worktree cleanup unless separately authorized.
- Bottom `## Phase Status` table.

CRON scheduling is mandatory. Require concrete `## CRON Bootstrap` state before phase execution. If the section is absent or incomplete, bootstrap CRON first; there is no non-CRON execution path. Do not infer missing CRON details.

### Optional Parallel Metadata

```markdown
## Phase Dependencies

| Phase | Depends On | Parallel Safe With | Primary Files                 |
| ----: | ---------- | ------------------ | ----------------------------- |
|     1 | -          | 2, 3               | `src/a.py`, `tests/test_a.py` |
|     2 | -          | 1, 3               | `src/b.py`, `tests/test_b.py` |
```

## Inputs to Confirm

- Repository/workdir path and plan path.
- Plan slug from the existing plan.
- Base branch override, if any.
- Sequential vs parallel mode from the existing plan.
- Phase scopes, expected files, dependencies, and file ownership from the existing plan.
- Verification commands from the existing plan.
- Branch naming mode: plan branch or phase branch from the existing plan.
- Worktree mode and path pattern for parallel phases from the existing plan.
- CRON schedule, job identity, run limit, delivery target, and self-stop action from `## CRON Bootstrap` or an explicit CRON bootstrap status row.
- Accepted terminal statuses besides `DONE`, if any.

## Branch and Worktree Rules

Preflight before branch/worktree changes:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```

Rules:

- Stop on unrelated uncommitted changes; ask before touching or moving them.
- Validate generated branch names:

  ```bash
  git check-ref-format --branch plan/<slug>
  git check-ref-format --branch plan/<slug>-phase-03
  ```

- Sequential mode normally uses `plan/<slug>` in the current worktree.
- Parallel mode uses `plan/<slug>-phase-<NN>` plus exactly one worktree per phase branch.
- Never run two workers in one worktree.
- Never assign overlapping file scopes unless the plan says they are independent.
- Pass the exact worktree path to every subagent and CRON prompt.
- Worktree removal is cleanup. Do not remove worktrees with uncommitted changes.

Switch/create a plan branch only after preflight:

```bash
branch=plan/<slug>
git check-ref-format --branch "$branch"
if git show-ref --verify --quiet "refs/heads/$branch"; then
  git switch "$branch"
else
  git switch -c "$branch"
fi
```

Suggested parallel worktree path and creation command:

```bash
../<repo>-plan-<slug>-phase-<NN>
git worktree add ../<repo>-plan-<slug>-phase-<NN> -b plan/<slug>-phase-<NN>
```

## Phase Status

Every plan ends with:

```markdown
## Phase Status

| Number | Title                             | Status |
| -----: | --------------------------------- | ------ |
|      1 | Draft the skill skeleton          | TODO   |
|      2 | Encode branch and status protocol | TODO   |
```

Valid statuses: `TODO`, `IN PROGRESS`, `DONE`, `DEFERRED`, `FAILED`, `BLOCKED`, `SKIPPED`.

Allowed transitions:

- `TODO -> IN PROGRESS -> DONE`
- `TODO/IN PROGRESS -> DEFERRED`
- `IN PROGRESS -> FAILED`
- `TODO/IN PROGRESS -> BLOCKED`
- `TODO -> SKIPPED`

Sequential execution may update the canonical table directly. Parallel execution must not let multiple branches race on the table; the orchestrator owns canonical updates on the plan branch, or updates must be serialized before reconciliation. Stop on status-table conflicts; do not auto-resolve them.

## Execution Workflow

1. Read the plan from disk; ignore chat-memory assumptions.
2. Parse `## Phase Status` and dependency/file-ownership metadata.
3. Run git preflight.
4. Stop on unrelated uncommitted changes.
5. Run the mandatory CRON bootstrap gate before selecting implementation work.
6. Select the next eligible phase:
   - sequential: first `TODO`; stop if any phase is already `IN PROGRESS`.
   - parallel: only a `TODO` phase confirmed independent by dependencies or file ownership.
7. Create/switch to the required branch/worktree.
8. Mark `IN PROGRESS` only when a visible claim is needed. A claim commit is optional.
9. Execute only the scoped phase work.
10. Run phase verification.
11. Mark `DONE`, `FAILED`, `BLOCKED`, or `DEFERRED` with a short note.
12. Inspect status and relevant diffs:

    ```bash
    git status --short
    git diff --stat
    git diff -- <relevant-paths>
    ```

13. Commit only if the diff is scoped and verification passed.
14. Re-check `git status --short`.
15. Run the completion/signoff verifier.

## Delegation

Use `delegate_task` for isolated implementation or review. The parent orchestrator remains responsible for final verification and commits.

Give implementer subagents:

- repo root or exact worktree path
- branch name
- phase number/title/objective/scope
- expected and forbidden files
- dependencies and file-ownership constraints
- verification commands
- commit format and keyword
- explicit ban on PRs, CI polling, merge automation, destructive git operations, and cleanup

Parallel subagents must each receive one distinct worktree and non-overlapping scope. They must not update the canonical status table independently. Reviewer subagents may inspect files and run safe local commands, but must not create PRs, watch CI, merge, or clean worktrees.

## Commit Protocol

Checkpoint at least once per phase. Additional commits are allowed when each sub-step is useful, verified, and scoped.

Format:

```text
plan:<plan-slug> phase:<N> <keyword>
```

Examples:

```text
plan:skill-git-exec phase:1 scaffold
plan:skill-git-exec phase:2 branch-rules
plan:parser-cleanup phase:2 tests
```

Rules:

- Keep messages terse; no long bodies unless requested.
- Include plan slug and phase number.
- Prefer committing implementation and final phase status together after verification.
- A separate `IN PROGRESS` claim commit is optional.
- Inspect status/diffs before commit and status after commit.

Suggested sequence:

```bash
git status --short
git diff --stat
git diff -- <phase-files>
git add <phase-files> <plan-file>
git commit -m "plan:<plan-slug> phase:<N> <keyword>"
git status --short
```

## CRON Scheduling

CRON scheduling is mandatory. This skill only supports scheduled/autonomous execution through a CRON job. CRON runs must be self-contained and able to proceed without questions.

### Bootstrap

Before implementation selection:

- If `## CRON Bootstrap` is absent or incomplete, collect/derive parameters, create the CRON job, record concrete state in `## CRON Bootstrap`, update any explicit CRON bootstrap status row to `DONE`, checkpoint if appropriate, report the job, and stop.
- If CRON creation fails, mark the explicit row `BLOCKED` or `FAILED` when present, report, and stop.
- If concrete bootstrap state already exists, verify the CRON job identity/schedule when possible before selecting implementation work.

Required CRON parameters:

- schedule
- repository path and plan path
- execution mode
- branch strategy and worktree path pattern
- max phases/tasks per run; sequential CRON defaults to `1`
- verification commands
- delivery target, if not current chat
- self-stop identity: job id or unique name
- self-stop action: default `pause`; use `remove` only if requested

Required plan section:

```markdown
## CRON Bootstrap

Status: enabled
Job name: run-<plan-slug>
Job id: <unknown until created>
Schedule: every 2h
Max phases per run: 1
Self-stop action: pause
Delivery target: origin/current chat
Bootstrap rule: the interactive setup run creates the CRON job, records this section, updates any CRON bootstrap status row, reports the job id/name/schedule, and stops.
```

### CRON Prompt Requirements

Create the job from the interactive bootstrap session. The prompt must include repository path, plan path, execution mode, branch/worktree strategy, max phases per run, verification commands, commit format, valid statuses, terminal statuses, self-stop identity/action, and these rules:

1. CRON runs cannot ask questions; stop and report missing/ambiguous parameters.
2. Re-read the plan before selecting work.
3. Run git preflight and stop on unrelated uncommitted changes.
4. Require recorded CRON bootstrap state and any explicit status row to be complete.
5. Sequential mode executes at most one `TODO` phase per tick, then verifies, reports, and exits.
6. Parallel mode uses only explicitly independent phases, distinct branches, and distinct worktrees.
7. Local verification only: no PRs, CI, merge automation, destructive git operations, or cleanup unless authorized.
8. Do not auto-resolve branch, worktree, merge, or status-table conflicts.
9. Completion verifier is shallow and read-only except self-stop; it must not implement work, start phases, reconcile branches, rewrite code, or make speculative fixes.
10. If complete and verification passes, list CRON jobs, identify only this CRON job, then pause by default or remove only if configured.

End-of-run report:

- Phase attempted
- Phase result
- Verification result
- Commit hash/message or none
- Completion verifier result
- CRON action
- Next expected action

Add `delegation` to CRON `enabled_toolsets` only if the CRON prompt may use subagents. Include `cronjob` because self-stop is required.

### CRON Stop Rules

CRON runs stop and report on missing parameters, ambiguous phase ownership, existing sequential `IN PROGRESS`, another runner on the phase, branch/worktree/status-table conflicts, verification failure without an obvious scoped fix, or required user authorization.

## Completion / Signoff Verifier

Run at normal checkpoints and every CRON tick. It is read-only except narrow CRON self-stop after completion.

Steps:

1. Re-read the plan.
2. Parse the bottom `## Phase Status` table.
3. Determine accepted terminal statuses. By default every phase must be `DONE`; `SKIPPED` and `DEFERRED` count only when explicitly accepted.
4. Run configured safe local verification commands.
5. Check `git status --short`.
6. Decide complete, incomplete, or ambiguous.

The verifier must not implement work, start another phase, perform broad review, rewrite code, reconcile branches, make speculative fixes, or create CRON jobs. In CRON, if complete and verified, list jobs and pause/remove only this CRON job. Otherwise leave CRON active and report why.

## Reconciliation and Cleanup

This skill does not include PR creation, CI polling, merge automation, automatic branch reconciliation, or cleanup. Merging phase branches or removing worktrees requires explicit user authorization. CRON self-stop is the only supported automation outside phase execution.

Before authorized reconciliation, report:

- plan and phase branch names
- assigned worktree paths
- commits per phase
- verification commands and results
- files changed per phase
- likely merge/conflict risks, especially around the status table

Stop and present status-table merge conflicts; never auto-resolve them. Do not remove any worktree whose `git status --short` is non-empty.

## Verification and Reporting

Local verification replaces PR/CI monitoring. Use plan commands and the smallest extra safe checks needed.

Common commands:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
git check-ref-format --branch plan/<slug>
pytest -q
ruff check .
python -m compileall .
```

Always report the real commands run and results. Parent-orchestrator verification is mandatory; do not rely only on subagent self-reports.

## Stop Conditions

Stop on failed verification without an obvious in-scope fix, required user input, unrelated uncommitted changes, destructive git actions, unauthorized merge/reconciliation, ambiguous parallel ownership, or conflict you cannot safely resolve.

## Common Pitfalls

1. Assuming `main` instead of discovering the base branch.
2. Treating a worktree as a branch replacement.
3. Letting parallel workers edit the canonical status table.
4. Creating PR/CI automation for a local-git plan.
5. Using CRON without a self-contained prompt and self-stop identity.
6. Continuing implementation after CRON bootstrap; bootstrap records state, reports, and stops.

## Execution Readiness Checklist

- [ ] A fresh session can resume from the plan file alone.
- [ ] Branch and worktree strategies are explicit.
- [ ] Phase scopes and verification commands are concrete.
- [ ] Parallel dependencies/file ownership are explicit when needed.
- [ ] CRON records concrete `## CRON Bootstrap` state and self-stop identity/action.
- [ ] Stop conditions and excluded PR/CI/merge/cleanup behaviors are documented.
- [ ] Bottom `## Phase Status` table is present.

## Skill File Checklist

- [ ] File starts at byte 0 with `---` and valid YAML frontmatter.
- [ ] Description is no more than 1024 characters.
- [ ] Body is non-empty and no more than 100,000 characters.
- [ ] Required workflow sections are present.
- [ ] No user-local Hermes skill paths were created or modified.
