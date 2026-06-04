# Git-Managed Plan Execution Skill Implementation Plan

> **For Hermes:** Use `subagent-driven-development` to implement this plan task-by-task, but apply the git/branch/worktree/cron conventions specified here. This plan creates a new Hermes skill that coordinates plan execution, branch management, optional worktree isolation, checkpoint commits, and cron scheduling without PR or CI workflows.

**Goal:** Create a reusable Hermes skill for executing implementation plans on named git branches with minimal phase status tracking, short plan/phase-based commit messages, safe parallel worktree execution, and optional cron-driven continuation.

**Architecture:** Add a new skill named `git-managed-plan-execution`. The skill will be an umbrella workflow that composes existing planning, git, subagent execution, and cron tooling into one operational protocol. Sequential execution uses a single plan branch. Parallel execution uses one phase branch per independent phase, checked out into a dedicated git worktree so subagents and cron runs never share a mutable working directory. It should not require GitHub PRs or CI monitoring.

**Tech Stack:** Hermes skills, `skill_manage`, local file tools, `git`, `git worktree`, `cronjob`, `todo`, `delegate_task`.

---

## Requirements

The new skill must encode these workflow rules:

1. Branch management is first-class.
   - The agent discovers the current repo state before execution.
   - The agent determines the base branch before creating plan or phase branches. Default to the current branch unless the user specifies otherwise; do not assume `main`.
   - The agent creates or switches to a named branch before implementation.
   - Branch naming may be plan-scoped, e.g. `plan/<slug>`, or phase-scoped, e.g. `plan/<slug>-phase-03`, depending on whether phases are sequential or parallel.
   - Branch names must be short, lowercase, and filesystem/git-safe.
   - Branch names should be validated with `git check-ref-format --branch <branch>` before creation when generated programmatically.

2. Worktree management is first-class for parallel execution.
   - Worktrees do not replace branches; a worktree is a separate checkout of a branch.
   - Sequential mode normally uses one plan branch in the main working tree.
   - Parallel mode uses one phase branch per independent phase, with each phase branch checked out into its own worktree.
   - Suggested worktree path: sibling directory `../<repo>-plan-<slug>-phase-<NN>`.
   - The agent must run `git worktree list` before creating or assigning worktrees.
   - The agent must never run two workers in the same worktree.
   - The agent must pass the assigned worktree path explicitly to each subagent and cron prompt.
   - Worktrees must not be removed if they contain uncommitted changes.
   - Worktree removal is cleanup, not required implementation; avoid destructive cleanup unless explicitly authorized or clearly safe.

3. Plans must have a minimal phase status table at the bottom.
   - Columns: `Number`, `Title`, `Status`.
   - Valid statuses:
     - `TODO`
     - `IN PROGRESS`
     - `DONE`
     - `DEFERRED`
     - `FAILED`
     - `BLOCKED`
     - `SKIPPED`
   - The agent updates the table as execution progresses.
   - In sequential mode, the active execution branch may update the table directly.
   - In parallel mode, avoid letting multiple phase branches independently modify the canonical status table. The orchestrator owns canonical status updates on the plan branch, or status updates must be serialized before reconciliation.
   - If status-table merge conflicts appear, stop and reconcile manually rather than auto-resolving.

4. Commits are checkpoint-oriented and terse.
   - Commit message format:
     - `plan:<plan-slug> phase:<N> <keyword>`
   - Examples:
     - `plan:skill-git-exec phase:1 scaffold`
     - `plan:skill-git-exec phase:2 branch-rules`
     - `plan:skill-git-exec phase:3 cron`
   - No long commit bodies unless the user asks.
   - Each commit must reference the plan and phase.
   - Prefer committing implementation and the final phase status update together after verification.
   - A separate `IN PROGRESS` claim commit is optional and should be used only when needed for coordination.

5. No PR and no CI lifecycle.
   - The skill must explicitly avoid PR creation, PR monitoring, CI watching, merge automation, and branch cleanup automation.
   - Verification is local: tests, lint, validation commands, file inspection, and git status.
   - Reconciliation or merging of parallel phase branches must be reported for user decision unless the user explicitly authorizes merge steps.

6. Checkpoint commits happen at least at the end of each phase.
   - More frequent commits are allowed when a sub-step is independently useful and the working tree is clean.
   - Before committing, the agent must inspect `git status --short` and the relevant diff.
   - After committing, the agent must verify `git status --short` again.

7. Cron management is integrated.
   - The skill prompts/asks the user for cron parameters when autonomous continuation is requested.
   - Required cron parameters:
     - schedule
     - repository path
     - plan path
     - execution mode: sequential or parallel
     - branch naming mode: plan branch or phase branch
     - worktree mode and worktree path pattern for parallel execution
     - max phases/tasks per run
     - verification command(s)
     - delivery target, if not current chat
   - The created cron prompt must be self-contained because cron jobs run in fresh sessions.
   - Cron jobs must not recursively create more cron jobs.
   - Sequential mode advances only the next eligible `TODO` phase and must stop if another phase is already `IN PROGRESS`.
   - Parallel mode may work on independent phases using distinct phase branches and distinct worktrees.
   - Cron runs must avoid double-claiming phases by re-reading the plan from disk immediately before selecting work.
   - Cron runs must stop with a clear report when parameters are missing, when phase ownership is ambiguous, or when another runner appears to be working on the same phase.

8. The skill must include clear stop conditions.
   - Stop when a phase is `BLOCKED`, `FAILED`, or needs user input.
   - Stop when local verification fails and no obvious fix is in scope.
   - Stop before destructive git operations unless explicitly authorized.
   - Stop if uncommitted unrelated changes are present.
   - Stop if parallel phases conflict on files, phase ownership, worktree assignment, or phase status updates.
   - Stop before merging/reconciling phase branches unless explicitly authorized.

9. The skill must distinguish user-local and in-repo skill targets.
   - User-local skill creation uses `skill_manage(action='create')` and writes under `~/.hermes/skills/`.
   - In-repo/shared skill creation uses local file tools to create `skills/software-development/git-managed-plan-execution/SKILL.md` and then commits it.
   - The implementer must confirm which target is intended before creating the skill when the user's request is ambiguous.

---

## Proposed Skill

**Name:** `git-managed-plan-execution`

**Category:** `software-development`

**Description:** `Use when executing implementation plans in a git repository with named branches, worktree-isolated parallel phases, phase status tables, checkpoint commits, and optional cron-driven continuation; excludes PR and CI workflows.`

**Related skills:**
- `writing-plans`
- `subagent-driven-development`
- `github-pr-workflow`
- `github-repo-management`
- `hermes-agent-skill-authoring`

**Important note:** Although this skill relates to `github-pr-workflow`, it must explicitly disable PR/CI portions and use only the branch/commit/checkpoint ideas.

---

## Phase Details

### Phase 1: Draft the skill skeleton

**Objective:** Create the new skill with valid frontmatter and a peer-matched structure.

**Files:**
- User-local option: create via `skill_manage(action='create')`: `software-development/git-managed-plan-execution/SKILL.md` under `~/.hermes/skills/`.
- In-repo/shared option: create with local file tools at `skills/software-development/git-managed-plan-execution/SKILL.md` and commit it.

**Steps:**
1. Confirm whether the skill target is user-local or in-repo/shared.
2. Draft valid YAML frontmatter:
   - `name`
   - `description`
   - `version`
   - `author`
   - `license`
   - `platforms`
   - `metadata.hermes.tags`
   - `metadata.hermes.related_skills`
3. Add top-level sections:
   - Overview
   - When to Use
   - Inputs to Collect
   - Branch Management
   - Worktree Management
   - Plan Phase Status Table
   - Execution Workflow
   - Commit Protocol
   - Cron Management
   - Reconciliation
   - Verification
   - Stop Conditions
   - Common Pitfalls
   - Verification Checklist
4. Validate that the content starts with `---`, has non-empty body, and description is under 1024 characters.

**Verification:**
- For user-local creation: `skill_manage(action='create', ...)` succeeds.
- For in-repo/shared creation: file exists at `skills/software-development/git-managed-plan-execution/SKILL.md` and validates locally.
- Skill content is readable with `skill_view(name='git-managed-plan-execution')` if the current session can see it, or inspect the written file path if current session cache prevents discovery.

**Commit:**
- If this repository is used to track the plan only, commit after the skill is created if the user wants this `PLAN.md` tracked.
- Commit message: `plan:git-managed-plan-execution phase:1 scaffold`

### Phase 2: Encode branch, worktree, and plan-status protocol

**Objective:** Add concrete branch naming, worktree isolation, and status table instructions.

**Files:**
- Modify: `git-managed-plan-execution/SKILL.md`

**Steps:**
1. Define base branch and branch naming rules:
   - Determine base branch from current branch unless the user specifies otherwise.
   - Do not assume `main`.
   - Plan branch: `plan/<slug>`
   - Phase branch: `plan/<slug>-phase-<NN>`
   - Optional user-provided branch override.
   - Validate generated branch names with `git check-ref-format --branch <branch>`.
2. Define preflight git checks:
   - `git status --short`
   - `git branch --show-current`
   - `git rev-parse --show-toplevel`
   - `git worktree list`
   - check for unrelated uncommitted changes.
3. Define worktree rules:
   - Worktrees complement branches; they do not replace branches.
   - Sequential mode usually uses one plan branch in the current worktree.
   - Parallel mode uses one phase branch per independent phase and one worktree per phase branch.
   - Suggested creation command:

```bash
git worktree add ../<repo>-plan-<slug>-phase-<NN> -b plan/<slug>-phase-<NN>
```

   - Subagents and cron prompts must receive the exact worktree path and must operate only inside that path.
   - Do not remove a worktree with uncommitted changes.
4. Define the bottom-of-plan phase status table format:

```markdown
## Phase Status

| Number | Title | Status |
|---:|---|---|
| 1 | Draft the skill skeleton | TODO |
| 2 | Encode branch and plan-status protocol | TODO |
```

5. Define valid statuses and transitions:
   - `TODO -> IN PROGRESS -> DONE`
   - `TODO/IN PROGRESS -> DEFERRED`
   - `IN PROGRESS -> FAILED`
   - `TODO/IN PROGRESS -> BLOCKED`
   - `TODO -> SKIPPED`
6. Define parallel status-table ownership:
   - Sequential mode may update the table on the plan branch directly.
   - Parallel mode must not let several phase branches race to update the canonical table.
   - The orchestrator owns canonical status updates, or status updates are serialized on the plan branch.
   - Stop on status-table conflicts rather than auto-resolving.
7. Optionally define phase dependency metadata for plans that need parallel execution:

```markdown
## Phase Dependencies

| Phase | Depends On | Parallel Safe With | Primary Files |
|---:|---|---|---|
| 1 | - | 2, 3 | `skills/.../SKILL.md` |
```

**Verification:**
- Read the skill and confirm base branch discovery, branch naming, branch validation, worktree rules, status table, canonical status ownership, and transitions are explicit.

**Commit:**
- `plan:git-managed-plan-execution phase:2 branch-worktree-status`

### Phase 3: Encode execution, subagent, commit, and reconciliation workflow

**Objective:** Add the phase execution loop, subagent worktree assignment rules, short commit-message policy, and manual reconciliation boundary.

**Files:**
- Modify: `git-managed-plan-execution/SKILL.md`

**Steps:**
1. Define the execution loop:
   - Read plan.
   - Read bottom phase status table.
   - Read optional phase dependency metadata.
   - Run git preflight checks.
   - Select next phase depending on sequential or parallel mode.
   - In sequential mode, stop if another phase is already `IN PROGRESS`.
   - In parallel mode, select only a phase that is explicitly independent or user-confirmed independent.
   - Create or select the correct branch/worktree.
   - Mark phase `IN PROGRESS` before work when coordination requires a visible claim.
   - Execute scoped work.
   - Run local verification.
   - Inspect diff/status.
   - Mark phase `DONE`, or `FAILED`/`BLOCKED`/`DEFERRED` as appropriate.
   - Commit if clean and scoped.
   - Prefer committing implementation and final status update together after verification.
   - Commit a separate claim/status update only when needed for coordination.
2. Define subagent delegation rules:
   - Pass the assigned repo root or worktree path explicitly.
   - Pass branch name, phase number, phase scope, expected files, verification commands, and commit message format.
   - In parallel mode, instruct each subagent to run all commands inside its assigned worktree only.
   - Never dispatch multiple implementation subagents to the same worktree or overlapping files unless the plan explicitly supports it.
3. Define commit message format:
   - `plan:<plan-slug> phase:<N> <keyword>`
4. Add examples for clean commits and for multiple commits within one phase.
5. State explicitly: no PR creation, no CI polling, no merge automation, no automatic merge/reconciliation of phase branches.
6. Add a reconciliation section:
   - Phase branches/worktrees may be created by this skill.
   - Merging phase branches back into a base or plan branch requires explicit user authorization.
   - End-of-run reports must include branch names, worktree paths, commits created, verification results, and merge/conflict risks.

**Verification:**
- Skill includes exact command examples for:
   - checking current branch
   - determining git root
   - checking status
   - listing worktrees
   - validating and creating a branch
   - creating a worktree
   - committing
   - rechecking clean state
- Skill includes subagent worktree assignment rules.
- Skill includes a manual reconciliation boundary.

**Commit:**
- `plan:git-managed-plan-execution phase:3 execution-commits`

### Phase 4: Add cron integration

**Objective:** Add a cron-driven continuation workflow that asks for required parameters and creates a self-contained cron job.

**Files:**
- Modify: `git-managed-plan-execution/SKILL.md`

**Steps:**
1. Add “When to use cron” guidance:
   - long-running phased work
   - periodic continuation
   - scheduled checks for next eligible phase
   - not for tasks requiring active user decisions every step
2. Add required user questions:
   - What schedule?
   - Which repository path?
   - Which plan path?
   - Sequential or parallel phases?
   - Branch naming mode: plan branch or phase branch?
   - Worktree mode and path pattern for parallel phases?
   - Max phases/tasks per run?
   - Verification command(s)?
   - Delivery target, if not current chat?
3. Add cron prompt template:
   - self-contained repo path
   - plan path
   - execution mode
   - branch rules
   - worktree rules and exact assigned worktree path or path pattern
   - valid statuses
   - phase claim/double-claim prevention rules
   - commit format
   - local verification only
   - no PR / no CI
   - no merge automation
   - no recursive cron creation
4. Add `cronjob(action='create', ...)` example.
5. Add guidance for listing/updating/removing jobs:
   - always `cronjob(action='list')` before update/pause/resume/remove.
6. Define cron stop behavior:
   - Cron runs cannot ask questions.
   - Cron must stop and report when parameters are missing.
   - Cron must stop if phase ownership is ambiguous, another phase is `IN PROGRESS` in sequential mode, or another runner appears to be working on the selected phase.
   - Cron must stop rather than auto-resolving worktree, branch, or status-table conflicts.

**Verification:**
- Skill includes a complete cron prompt template that can run without current-chat context.
- Skill states cron runs must not ask questions and must stop with a clear report when parameters are missing.
- Skill states cron runs must avoid double-claiming phases and must use distinct worktrees for parallel execution.

**Commit:**
- `plan:git-managed-plan-execution phase:4 cron`

### Phase 5: Validate, review, and harden the skill

**Objective:** Verify the skill is actionable, non-duplicative, and safe.

**Files:**
- Modify: `git-managed-plan-execution/SKILL.md` if review finds gaps.

**Steps:**
1. Run a local frontmatter/content validation script or inspect via skill tooling.
2. Compare against related skills:
   - `writing-plans`
   - `subagent-driven-development`
   - `github-pr-workflow`
   - `github-repo-management`
   - `hermes-agent-skill-authoring`
3. Confirm the new skill does not duplicate full PR/CI workflows.
4. Confirm it references existing skills but gives a single coordinated protocol.
5. Confirm destructive git operations require explicit authorization.
6. Confirm generated branch names are validated and worktree paths are explicit.
7. Confirm parallel execution cannot accidentally share one working directory.
8. Confirm status-table ownership is safe in parallel mode.
9. Confirm cron runs cannot recursively create cron jobs or double-claim phases.
10. Confirm merge/reconciliation remains manual unless explicitly authorized.
11. Optionally dispatch a reviewer subagent for spec compliance and quality review.

**Verification:**
- Frontmatter valid.
- Description under 1024 characters.
- Body contains required workflow sections.
- Branch, worktree, commit, status table, cron, subagent, and reconciliation requirements from this `PLAN.md` are all represented.

**Commit:**
- `plan:git-managed-plan-execution phase:5 validate`

---

## Definition of Done

The skill is complete when:

- `git-managed-plan-execution` exists as a user-local Hermes skill or an in-repo/shared skill, depending on the confirmed target.
- The skill provides a single coordinated plan-execution workflow.
- Base branch discovery is explicit and does not assume `main`.
- Branch management is explicit.
- Worktree management is explicit for parallel execution.
- Parallel execution uses distinct phase branches and distinct worktrees.
- Bottom-of-plan phase status table is required and specified.
- Parallel status-table ownership is safe and does not encourage conflicting branch edits.
- Commit messages are short and reference plan + phase.
- PR and CI workflows are explicitly excluded.
- Merge/reconciliation automation is excluded unless explicitly authorized.
- Cron creation and cron management are integrated.
- Cron double-claim prevention and stop behavior are documented.
- Sequential vs parallel phase execution is documented.
- Subagent worktree assignment is documented.
- Stop conditions and safety rules are documented.
- The skill has been validated and reviewed.

---

## What Not To Do

- Do not create PR automation in this skill.
- Do not add CI monitoring or CI auto-fix loops.
- Do not require GitHub; local git is sufficient.
- Do not use long commit bodies by default.
- Do not assume phases are parallel-safe unless the plan or user says so.
- Do not use worktrees as a replacement for branches; use worktrees as isolated checkouts of branches.
- Do not run multiple workers in the same worktree.
- Do not let cron jobs recursively create more cron jobs.
- Do not let cron jobs double-claim the same phase.
- Do not let multiple parallel branches race to update the canonical status table.
- Do not auto-resolve status-table merge conflicts.
- Do not merge or reconcile phase branches without explicit authorization.
- Do not overwrite or discard unrelated working-tree changes.
- Do not remove worktrees with uncommitted changes.

---

## Phase Status

| Number | Title | Status |
|---:|---|---|
| 1 | Draft the skill skeleton | TODO |
| 2 | Encode branch, worktree, and plan-status protocol | TODO |
| 3 | Encode execution, subagent, commit, and reconciliation workflow | TODO |
| 4 | Add cron integration | TODO |
| 5 | Validate, review, and harden the skill | TODO |
