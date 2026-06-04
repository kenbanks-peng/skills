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
- Whether cron continuation is requested.
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
6. Select the next eligible phase:
   - sequential: choose the first `TODO` phase; stop if any phase is already `IN PROGRESS`
   - parallel: choose only a `TODO` phase that is explicitly independent or user-confirmed independent
7. Create or select the correct branch/worktree.
8. Mark the phase `IN PROGRESS` before work only when coordination requires a visible claim. A separate claim commit is optional, not the default.
9. Execute only the scoped work for that phase.
10. Run the phase's local verification commands.
11. Mark the phase `DONE`, or mark `FAILED`, `BLOCKED`, or `DEFERRED` with a short report when appropriate.
12. Inspect status and diff before committing:

```bash
git status --short
git diff --stat
git diff -- <relevant-paths>
```

13. Commit only if the diff is scoped and verification has passed. Prefer committing implementation and the final phase status update together.
14. Re-check clean state after committing:

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

Cron continuation is optional. Only create a cron job when the user requests autonomous continuation and supplies the required schedule, repo, plan, execution mode, branch/worktree, verification, and self-stop parameters.

## Completion / Signoff Verifier

At the end of execution or cron runs, re-read the phase status table, run configured safe local verification commands, check git status, and decide whether the plan is complete. The verifier is not an implementation worker.

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
5. Using cron continuation without a self-contained prompt.

## Generated Plan Quality Checklist

- [ ] Fresh sessions can continue from the plan file alone.
- [ ] Branch strategy and optional worktree strategy are explicit.
- [ ] Phase scopes and verification commands are concrete.
- [ ] Stop conditions and excluded PR/CI/merge behaviors are documented.
- [ ] Bottom `## Phase Status` table is present.

## Verification Checklist

- [ ] File starts at byte 0 with `---` and has valid YAML frontmatter.
- [ ] Description is no more than 1024 characters.
- [ ] Body is non-empty and no more than 100,000 characters.
- [ ] Required workflow sections are present.
- [ ] No user-local Hermes skill paths were created or modified.
