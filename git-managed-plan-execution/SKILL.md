---
name: git-managed-plan-execution
description: Use when authoring or executing git-managed implementation plans with phase status tables, named branches, optional worktree-isolated parallel phases, terse checkpoint commits, local verification, and optional cron-driven continuation; excludes PR and CI workflows.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [git, planning, implementation, branches, worktrees, cron, delegation]
    related_skills: [writing-plans, subagent-driven-development, github-repo-management, hermes-agent-skill-authoring]
---

# Git-Managed Plan Execution

## Overview

Use this skill to author and execute implementation plans that are durable on disk and coordinated through local git. The workflow combines self-executing plan documents, named branches, optional worktree isolation for parallel phases, a minimal bottom-of-plan phase status table, terse checkpoint commits, local verification, and optional cron-driven continuation.

This is a local-git workflow. It deliberately excludes GitHub PR creation, CI watching, merge automation, and branch cleanup automation unless the user separately asks for those actions.

## When to Use

Use this skill when:
- A user asks for an implementation plan that future Hermes sessions can continue from disk.
- A plan should be executed with explicit branch names and phase checkpoint commits.
- Parallel phase work needs isolated worktrees so subagents or cron runs do not share one mutable directory.
- A user wants optional scheduled continuation of a phased plan.

Do not use this skill for one-off edits that do not need durable phase tracking, PR-focused workflows, or destructive git cleanup.

## Hermes Dependencies

- Use file tools (`read_file`, `write_file`, `patch`, `search_files`) for plan and skill file work.
- Use `terminal` for git commands, local tests, lint, and validation.
- Use `todo` only for session-local tracking; durable status belongs in the plan file.
- Use `delegate_task` only when subagent implementation or review is beneficial.
- Use `cronjob` only when the user requests scheduled continuation.

## Plan Authoring Workflow

When asked to create a plan, produce a self-executing document. Assume the future executor has the file and the repository, but not the current chat.

1. Discover and record repository context:
   - repository root or workdir path
   - current branch as the default base branch, unless the user specifies a base
   - relevant repo-relative paths
   - local verification commands that are safe to run
2. Choose a short plan slug, lowercase and git/filesystem-safe.
3. Decide execution mode:
   - `sequential`: one plan branch in the current worktree unless the user requests isolation
   - `parallel`: one branch and one worktree per independent phase
4. Write phases with objective, scope, expected files, steps, verification commands, and commit keyword.
5. State whether parallelism is allowed. If it is, include phase dependencies or file-ownership metadata.
6. State explicit exclusions: no PR creation, CI watching, merge automation, destructive git operations, or branch/worktree cleanup unless explicitly requested.
7. Put `## Phase Status` at the bottom of the plan and keep it as the durable control surface.

## Generated Plan Requirements

Every generated plan must include:

- `Goal`: one clear outcome.
- `Scope`: in-scope and out-of-scope work.
- `Repository`: absolute repo/workdir path or explicit repo-relative paths.
- `Plan slug`: short, lowercase, git-safe name used in branches and commits.
- `Base branch`: discovered from `git branch --show-current` unless the user overrides it. Do not assume `main`.
- `Execution mode`: sequential or parallel.
- `Branch strategy`:
  - plan branch: `plan/<slug>`
  - phase branch: `plan/<slug>-phase-<NN>`
  - any user-provided branch override
- `Worktree strategy`: required for parallel execution, optional for sequential execution.
- `Phase list`: objective, files/scope, steps, verification commands, and commit keyword for each phase.
- `Phase Dependencies` or file ownership metadata when parallelism is allowed.
- `Local verification commands`: tests, lint, validation scripts, inspections, or smoke checks.
- If scheduled continuation is requested, a durable `## CRON Bootstrap` section with the concrete cron configuration and bootstrap rule. Keep the generic decision procedure in this skill; plans record only the selected cron state.
- `Stop conditions`: user input, failed verification, unrelated changes, destructive git actions, conflicts, or ambiguous ownership.
- `Explicit exclusions`: no PR creation, CI polling, merge automation, or destructive cleanup unless separately authorized.
- Bottom `## Phase Status` table with `Number`, `Title`, and `Status`.

Use this optional metadata table when parallel execution is possible:

```markdown
## Phase Dependencies

| Phase | Depends On | Parallel Safe With | Primary Files |
|---:|---|---|---|
| 1 | - | 2, 3 | `src/a.py`, `tests/test_a.py` |
| 2 | - | 1, 3 | `src/b.py`, `tests/test_b.py` |
```

## Inputs to Collect

Collect these before authoring or executing:

- Goal and scope.
- Repository/workdir path and plan path.
- Plan slug. Generate one only if the user did not provide it.
- Base branch override, if any. Otherwise discover the current branch.
- Sequential vs parallel mode.
- Phase scopes, expected files, dependencies, and file ownership.
- Local verification commands.
- Branch naming mode: plan branch or phase branch.
- Worktree mode and path pattern for parallel phases.
- Whether scheduled continuation is requested. Treat scheduled continuation as requested only when the user explicitly asks for scheduled/autonomous continuation or when the plan already contains a CRON bootstrap section or explicit CRON bootstrap status row.
- Any accepted terminal statuses besides `DONE` for plan completion.

## Branch Management

Branch management is first-class. Always discover the repo state before creating or switching branches:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```

Rules:

- Default the base branch to the current branch unless the user specifies otherwise. Never assume `main`.
- Stop if `git status --short` shows unrelated uncommitted changes. Ask before touching or moving them.
- Sequential mode normally uses one plan branch: `plan/<slug>`.
- Parallel mode normally uses phase branches: `plan/<slug>-phase-<NN>`.
- User-provided branch names are allowed, but still verify they are safe for the intended operation.
- Generated branch names must be short, lowercase, and git/filesystem-safe.
- Validate generated names before creation:

```bash
git check-ref-format --branch plan/<slug>
git check-ref-format --branch plan/<slug>-phase-03
```

Create or switch only after validation and status checks:

```bash
branch=plan/<slug>
git check-ref-format --branch "$branch"
if git show-ref --verify --quiet "refs/heads/$branch"; then
  git switch "$branch"
else
  git switch -c "$branch"
fi
```

## Worktree Management

Worktrees complement branches; they do not replace branches. A worktree is a separate checkout of one branch.

Rules:

- Run `git worktree list` before creating or assigning worktrees.
- Sequential mode normally uses the current worktree on `plan/<slug>`; do not add worktree overhead unless useful.
- Parallel mode uses one phase branch per independent phase and exactly one worktree per phase branch.
- Never run two workers in the same worktree.
- Never assign parallel phases to overlapping file scopes unless the plan explicitly confirms they are independent.
- Pass the assigned worktree path explicitly to every subagent and cron prompt.
- Do not remove worktrees with uncommitted changes. Worktree removal is cleanup, not required implementation.

Suggested parallel worktree path:

```bash
../<repo>-plan-<slug>-phase-<NN>
```

Suggested creation command:

```bash
git worktree add ../<repo>-plan-<slug>-phase-<NN> -b plan/<slug>-phase-<NN>
```

Before removing a worktree, if cleanup is explicitly authorized, verify it is clean from inside that worktree:

```bash
git -C ../<repo>-plan-<slug>-phase-<NN> status --short
```

If any output appears, do not remove it.

## Plan Phase Status Table

Every generated git-managed plan must end with this durable status table:

```markdown
## Phase Status

| Number | Title | Status |
|---:|---|---|
| 1 | Draft the skill skeleton | TODO |
| 2 | Encode branch and plan-status protocol | TODO |
```

Valid statuses:

- `TODO`
- `IN PROGRESS`
- `DONE`
- `DEFERRED`
- `FAILED`
- `BLOCKED`
- `SKIPPED`

Allowed transitions:

- `TODO -> IN PROGRESS -> DONE`
- `TODO/IN PROGRESS -> DEFERRED`
- `IN PROGRESS -> FAILED`
- `TODO/IN PROGRESS -> BLOCKED`
- `TODO -> SKIPPED`

Sequential status ownership: the active execution branch may update the canonical table directly.

Parallel status ownership: do not let multiple phase branches race to update the canonical table. The orchestrator owns canonical status updates on the plan branch, or status updates must be serialized before reconciliation. If status-table conflicts appear, stop for manual reconciliation; do not auto-resolve them.

## Execution Workflow

Use this loop for phase execution:

1. Read the plan from disk. Do not rely on chat history.
2. Parse the bottom `## Phase Status` table.
3. Parse `## Phase Dependencies` or file-ownership metadata if present.
4. Run git preflight checks:

```bash
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list
```

5. Stop if unrelated uncommitted changes are present.
6. Run the scheduled-continuation decision/bootstrap gate before selecting implementation work:
   - if scheduled continuation is not requested, continue normally
   - if scheduled continuation is requested and CRON bootstrap has not been completed, execute only the CRON bootstrap procedure, record the concrete cron configuration in the plan, update only an explicit `CRON bootstrap` status row if present, commit/checkpoint when appropriate, report the cron job, and stop
   - do not start, claim, delegate, or execute the next implementation phase in the same interactive run after creating cron
7. Select the next eligible phase:
   - sequential: choose the first `TODO` phase; stop if any phase is already `IN PROGRESS`
   - parallel: choose only a `TODO` phase that is explicitly independent or user-confirmed independent
8. Create or select the correct branch/worktree.
9. Mark the phase `IN PROGRESS` before work only when coordination requires a visible claim. A separate claim commit is optional, not the default.
10. Execute only the scoped work for that phase.
11. Run the phase's local verification commands.
12. Mark the phase `DONE`, or mark `FAILED`, `BLOCKED`, or `DEFERRED` with a short report when appropriate.
13. Inspect status and diff before committing:

```bash
git status --short
git diff --stat
git diff -- <relevant-paths>
```

14. Commit only if the diff is scoped and verification has passed. Prefer committing implementation and the final phase status update together.
15. Re-check clean state after committing:

```bash
git status --short
```

### Subagent Delegation Rules

Use `delegate_task` when isolated implementation or review would improve quality. The parent orchestrator remains responsible for final verification.

Pass every implementer subagent:

- assigned repo root or exact worktree path
- branch name
- phase number and title
- phase objective and scope
- expected files and forbidden files
- phase dependencies and file ownership constraints
- exact local verification commands
- commit message format and commit keyword
- instruction to avoid PR creation, CI polling, merge automation, destructive git operations, and branch cleanup

Parallel mode requirements:

- Each implementation subagent gets exactly one assigned worktree path.
- The subagent must run all commands inside that worktree only, for example `workdir=/abs/path/to/worktree`.
- Never dispatch multiple implementation subagents to the same worktree.
- Never dispatch overlapping file scopes unless the plan explicitly says they are parallel-safe.
- Do not let implementation subagents independently update the canonical phase status table in parallel branches. The orchestrator serializes status updates.

Reviewer subagents may inspect files and run safe local commands, but they must not create PRs, watch CI, merge branches, or clean worktrees.

## Commit Protocol

Checkpoint commits happen at least at the end of each phase. More frequent commits are allowed only when a sub-step is independently useful, verified, and scoped.

Commit message format:

```text
plan:<plan-slug> phase:<N> <keyword>
```

Examples:

```text
plan:skill-git-exec phase:1 scaffold
plan:skill-git-exec phase:2 branch-rules
plan:skill-git-exec phase:3 cron
```

Rules:

- Keep commit messages terse. Do not add long bodies unless the user asks.
- Every phase commit references both the plan slug and phase number.
- Prefer committing implementation and final phase status update together after verification.
- A separate `IN PROGRESS` claim/status commit is optional and only for coordination.
- Before committing, inspect `git status --short` and relevant diffs.
- After committing, verify `git status --short` again.

Suggested command sequence:

```bash
git status --short
git diff --stat
git diff -- <phase-files>
git add <phase-files> <plan-file>
git commit -m "plan:<plan-slug> phase:<N> <keyword>"
git status --short
```

Multiple commits within one phase are acceptable when the plan says so or the sub-step is a clean checkpoint:

```text
plan:parser-cleanup phase:2 tests
plan:parser-cleanup phase:2 parser
plan:parser-cleanup phase:2 docs
```

## Cron Management

Scheduled continuation is the recurring cron-driven execution process. CRON bootstrap is the one-time interactive setup step that creates the cron job and records its configuration. Scheduled continuation is optional; use it for long-running phased work, periodic continuation, or scheduled checks for the next eligible phase. Do not use cron for work that requires active user decisions at every step. Cron runs execute in fresh sessions and cannot ask questions.

### Cron Decision and Bootstrap Gate

The cron decision procedure belongs in this skill. Do not append the generic decision tree to every plan. A plan should record only the concrete cron state when cron is actually used.

Before selecting the first implementation phase, determine whether scheduled continuation is requested:

- Scheduled continuation is requested only when the user explicitly asks for scheduled/autonomous continuation, or when the plan already contains a CRON bootstrap section or explicit CRON bootstrap status row.
- If scheduled continuation is not requested, do not create a cron job, do not add cron metadata to the plan, and continue with normal phase execution.
- If scheduled continuation is requested, run CRON bootstrap before implementation work.

CRON bootstrap from an interactive session:

1. Collect or derive all cron parameters: schedule, repository path, plan path, execution mode, branch/worktree strategy, max phases/tasks per run, verification commands, delivery target, self-stop identity, and self-stop action.
2. Create the cron job with a self-contained prompt.
3. Record the concrete cron configuration in the plan under `## CRON Bootstrap`.
4. If the plan has an explicit `CRON bootstrap` status row, update only that row to `DONE` after successful cron creation. Do not mark an implementation phase `DONE` merely because cron was created, even if that phase is numbered `0`; Phase 0 may be real plan-execution work and should remain eligible for the next cron event.
5. Commit/checkpoint the plan update if operating under git-managed execution and the diff is scoped.
6. Stop immediately. Do not start, claim, delegate, or execute Phase 1 or any other implementation phase in the same initial run.

If cron creation fails, mark the explicit CRON bootstrap row `BLOCKED` or `FAILED` if such a row exists, report the blocker, and stop. Do not start implementation work as a fallback unless the user explicitly asks to continue manually.

Suggested plan section when cron is enabled:

```markdown
## CRON Bootstrap

Status: enabled
Job name: continue-<plan-slug>
Job id: <unknown until created>
Schedule: every 2h
Max phases per run: 1
Self-stop action: pause
Delivery target: origin/current chat
Bootstrap rule: the interactive setup run creates the cron job, records this section, updates only an explicit CRON bootstrap status row if applicable, then stops before implementation work. Implementation Phase 0, if present, is not bootstrap and starts on the next cron event.
```

Only create a cron job when the user requests autonomous continuation. Ask for or derive all required parameters before creation:

- schedule
- repository path
- plan path
- execution mode: sequential or parallel
- branch naming mode: plan branch or phase branch
- worktree mode and worktree path pattern for parallel phases
- max phases/tasks per run; sequential cron defaults to exactly `1` and must not batch phases unless explicitly requested
- verification command(s)
- delivery target, if not the current chat
- cron job identity for self-stop: job id if known, otherwise a unique job name
- self-stop action when the whole plan is complete: default `pause`; use `remove` only if explicitly requested

### Cron Creation Example

Only call `cronjob(action='create', ...)` from an interactive session after collecting parameters. Cron-run sessions must not recursively create additional cron jobs.

```python
cronjob(
    action="create",
    name="continue-<plan-slug>",
    schedule="every 2h",
    prompt="""
You are continuing a git-managed implementation plan. This prompt is self-contained; do not rely on chat history.

Repository path: /absolute/path/to/repo
Plan path: /absolute/path/to/repo/docs/plans/<plan>.md
Execution mode: sequential
Branch naming mode: plan branch
Plan branch: plan/<plan-slug>
Phase branch pattern: plan/<plan-slug>-phase-<NN>
Worktree mode: none for sequential; for parallel use ../<repo>-plan-<plan-slug>-phase-<NN>
Max phases/tasks per run: 1
Verification commands: <commands>
Commit format: plan:<plan-slug> phase:<N> <keyword>
Valid statuses: TODO, IN PROGRESS, DONE, DEFERRED, FAILED, BLOCKED, SKIPPED
Completion terminal statuses: DONE only unless this plan explicitly accepts SKIPPED/DEFERRED.
Self-stop identity: job name continue-<plan-slug>; if a job id is provided in this prompt, use that exact id.
Self-stop action after completion verifier passes: pause

Rules:
1. Cron runs cannot ask questions. If required parameters are missing or ambiguous, stop and report.
2. Do not create more cron jobs. The only allowed cron management side effect is pausing/removing this continuation job after completion verification passes.
3. Re-read the plan from disk immediately before selecting work to avoid double-claiming.
4. Run git preflight: git rev-parse --show-toplevel, git branch --show-current, git status --short, git worktree list.
5. Stop if unrelated uncommitted changes exist.
6. Treat only an explicit `CRON bootstrap` status row as interactive bootstrap state. It must already be DONE before implementation work. Do not treat Phase 0 as bootstrap unless it is explicitly titled CRON bootstrap; otherwise Phase 0 is normal implementation work and may be the next eligible TODO phase for this cron run.
7. Sequential mode: if any phase is IN PROGRESS, stop and report. Select at most one next TODO implementation phase, execute it, run verification, commit, run the completion verifier, report, and exit. Do not start a second phase in the same tick.
8. Parallel mode: select only independent TODO implementation phases with explicit dependency/file-ownership metadata. Use distinct phase branches and distinct worktrees. Never run two workers in the same worktree. Stop on ambiguous ownership or conflicts.
9. Local verification only. No PR creation, no CI watching, no merge automation, no destructive git operations, no branch/worktree cleanup unless explicitly authorized.
10. Do not auto-resolve worktree, branch, merge, or status-table conflicts.
11. Completion verifier is shallow and read-only except self-stop. It re-reads the plan, parses the bottom Phase Status table, runs configured safe verification commands, checks git status --short, and decides whether the plan is complete. It must not implement work, start another phase, reconcile branches, rewrite code, or make speculative fixes.
12. If complete and verification passes, first list cron jobs, identify only this continuation job by provided id or unique name, then pause it by default or remove it only if explicitly configured. If incomplete or ambiguous, leave cron active.

End-of-run report format:
- Phase attempted: <number/title or none>
- Phase result: <DONE/BLOCKED/FAILED/DEFERRED/SKIPPED/none>
- Verification result: <commands and pass/fail>
- Commit: <hash/message or none>
- Completion verifier: <complete/incomplete/ambiguous and why>
- Cron action: <none/paused/removed and job id/name>
- Next expected action: <next phase/user decision/fix blocker>
""",
    enabled_toolsets=["terminal", "file", "cronjob"],
)
```

Add `"delegation"` to `enabled_toolsets` only if the cron prompt may use subagents. Include `"cronjob"` only when self-stop behavior is expected.

### Cron Job Management

Always list jobs before update, pause, resume, or remove:

```python
cronjob(action="list")
cronjob(action="pause", job_id="<confirmed-job-id>")
```

Cron runs may pause or remove only their own continuation job, and only after completion verification passes. Default to pausing. Remove only if the user explicitly requested removal.

### Cron Stop Behavior

A cron run must stop and report when:

- required parameters are missing
- phase ownership is ambiguous
- another phase is already `IN PROGRESS` in sequential mode
- another runner appears to be working on the selected phase
- branch/worktree/status-table conflicts exist
- verification fails without an obvious in-scope fix
- the next step requires user authorization

Sequential cron must execute at most one eligible `TODO` phase per run, then run the completion verifier, report, and exit. It must not start another phase in the same tick, even if more `TODO` phases remain.

CRON bootstrap is not a cron-run responsibility. A cron run must not create another cron job or execute an explicit CRON bootstrap row; if explicit bootstrap state is present but not `DONE`, report the ambiguity and stop. A Phase 0 that describes implementation work is not bootstrap and may start on the next cron event like any other eligible phase.

## Completion / Signoff Verifier

Run a shallow signoff verifier at the end of normal execution checkpoints and every cron run. It is read-only except for the narrow cron self-stop action after completion.

Verifier steps:

1. Re-read the plan from disk.
2. Parse the bottom `## Phase Status` table.
3. Determine accepted terminal statuses. Default plan completion requires every phase to be `DONE`. `SKIPPED` and `DEFERRED` count as complete only if the user or plan explicitly accepts them. `TODO`, `IN PROGRESS`, `BLOCKED`, and `FAILED` are not complete.
4. Run only configured safe local verification commands.
5. Check `git status --short`.
6. Decide whether the plan lifecycle is complete.

The verifier must not:

- start another phase
- perform broad semantic review
- rewrite implementation
- reconcile branches
- make speculative fixes
- create cron jobs

If complete and verification passes in a cron run, list cron jobs and pause/remove only this continuation job according to the configured self-stop action. If incomplete or ambiguous, leave cron active and report the reason.

## Reconciliation

No PR creation, no CI polling, no merge automation, and no automatic merge/reconciliation of phase branches are part of this skill. Use `github-pr-workflow` only as a contrast: this skill does not import the GitHub PR/CI lifecycle.

Parallel phase branches and worktrees may be created by this workflow. Merging phase branches back into a base or plan branch requires explicit user authorization. Before asking for or performing reconciliation, report:

- plan branch and phase branch names
- assigned worktree paths
- commits created for each phase
- verification commands and real results
- files changed by each phase
- likely merge/conflict risks, especially around the canonical phase status table

If status-table merge conflicts appear, stop and present the conflict. Do not auto-resolve status-table conflicts.

Worktree cleanup is optional. Do not remove a worktree if `git status --short` inside that worktree shows uncommitted changes.

## Verification

Local verification replaces PR/CI monitoring in this workflow. Use the commands written in the plan and the smallest extra checks needed to prove the phase. Examples:

```bash
# repository and branch state
git rev-parse --show-toplevel
git branch --show-current
git status --short
git worktree list

# branch validation and creation
git check-ref-format --branch plan/<slug>
git switch -c plan/<slug>

# phase worktree creation
git worktree add ../<repo>-plan-<slug>-phase-03 -b plan/<slug>-phase-03

# local project checks, examples only
pytest -q
ruff check .
python -m compileall .

# commit and post-commit check
git add <paths>
git commit -m "plan:<plan-slug> phase:<N> <keyword>"
git status --short
```

Always report the real verification commands run and their results. Parent-orchestrator verification is mandatory; do not rely only on subagent self-reports.

## Stop Conditions

Stop when local verification fails without an obvious in-scope fix, when user input is required, when unrelated uncommitted changes exist, before destructive git actions, before unauthorized merge/reconciliation, or when parallel work ownership is ambiguous.

## Common Pitfalls

1. Assuming the base branch is `main` instead of discovering it.
2. Treating a worktree as a replacement for a branch.
3. Letting multiple parallel workers edit the canonical phase status table.
4. Creating PR or CI lifecycle automation when only local git execution was requested.
5. Using scheduled continuation without a self-contained cron prompt.
6. Creating cron and then continuing into Phase 1 in the same initial run. CRON bootstrap is a gate: record the cron state, update only an explicit CRON bootstrap status row if present, report, and stop.
7. Treating any numbered `Phase 0` as bootstrap. Only an explicit `CRON bootstrap` status row is bootstrap state. A real implementation Phase 0 remains normal implementation work and may be selected by the next cron event.

## Generated Plan Quality Checklist

- [ ] Fresh sessions can continue from the plan file alone.
- [ ] Branch strategy and optional worktree strategy are explicit.
- [ ] Phase scopes and verification commands are concrete.
- [ ] If cron is enabled, the plan records concrete `## CRON Bootstrap` state while the generic decision/bootstrap procedure remains in this skill.
- [ ] Stop conditions and excluded PR/CI/merge behaviors are documented.
- [ ] Bottom `## Phase Status` table is present.

## Verification Checklist

- [ ] File starts at byte 0 with `---` and has valid YAML frontmatter.
- [ ] Description is no more than 1024 characters.
- [ ] Body is non-empty and no more than 100,000 characters.
- [ ] Required workflow sections are present.
- [ ] No user-local Hermes skill paths were created or modified.
