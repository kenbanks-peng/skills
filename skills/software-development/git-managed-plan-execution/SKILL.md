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

When asked to create a plan, write it so a fresh Hermes session can resume from the file alone. Include the repository path or repo-relative paths, clear phase scopes, branch strategy, verification commands, stop conditions, and the bottom `## Phase Status` table.

## Generated Plan Requirements

A generated plan must include a goal, repo/workdir path or repo-relative paths, plan slug, phases, local verification commands, branch strategy, optional worktree strategy, stop conditions, and explicit exclusions for PR/CI/merge automation unless explicitly requested.

## Inputs to Collect

Collect the goal, repo path, desired plan path, plan slug, base branch override if any, sequential vs parallel execution mode, phase scopes, local verification commands, and whether cron continuation is requested.

## Branch Management

Discover the current repository state before execution. Determine the base branch from the current branch unless the user specifies otherwise. Create or switch to a named branch before implementation.

## Worktree Management

Use the main worktree for simple sequential work. Use separate phase branches and separate worktrees for parallel phase work. Worktrees complement branches; they do not replace them.

## Plan Phase Status Table

Every generated git-managed plan must end with a minimal `## Phase Status` table containing `Number`, `Title`, and `Status` columns. Valid statuses are `TODO`, `IN PROGRESS`, `DONE`, `DEFERRED`, `FAILED`, `BLOCKED`, and `SKIPPED`.

## Execution Workflow

Read the plan, inspect the phase status table, run git preflight checks, select one eligible phase, execute scoped work, run local verification, update the durable phase status, inspect diff/status, and commit a terse checkpoint.

## Commit Protocol

Commit message format: `plan:<plan-slug> phase:<N> <keyword>`. Keep messages short and do not add long bodies unless requested.

## Cron Management

Cron continuation is optional. Only create a cron job when the user requests autonomous continuation and supplies the required schedule, repo, plan, execution mode, branch/worktree, verification, and self-stop parameters.

## Completion / Signoff Verifier

At the end of execution or cron runs, re-read the phase status table, run configured safe local verification commands, check git status, and decide whether the plan is complete. The verifier is not an implementation worker.

## Reconciliation

Parallel phase branches and worktrees may be created by this workflow, but merging or reconciling those branches requires explicit user authorization. Report branch names, worktree paths, commits, verification results, and merge/conflict risks.

## Verification

Validate plan and skill file structure locally, inspect relevant diffs before commits, run local verification commands, and re-check `git status --short` after committing.

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
