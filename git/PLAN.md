# Git-Managed Plan Execution Skill Implementation Plan

> **For Hermes:** Use `subagent-driven-development` to implement this plan task-by-task, but apply the git/branch/cron conventions specified here. This plan creates a new Hermes skill that coordinates plan execution, branch management, checkpoint commits, and cron scheduling without PR or CI workflows.

**Goal:** Create a reusable Hermes skill for executing implementation plans on named git branches with minimal phase status tracking, short plan/phase-based commit messages, and optional cron-driven continuation.

**Architecture:** Add a new user-local skill named `git-managed-plan-execution`. The skill will be an umbrella workflow that composes existing planning, git, subagent execution, and cron tooling into one operational protocol. It should not require GitHub PRs or CI monitoring.

**Tech Stack:** Hermes skills, `skill_manage`, `git`, `cronjob`, `todo`, `delegate_task`, local file tools.

---

## Requirements

The new skill must encode these workflow rules:

1. Branch management is first-class.
   - The agent discovers the current repo state before execution.
   - The agent creates or switches to a named branch before implementation.
   - Branch naming may be plan-scoped, e.g. `plan/<slug>`, or phase-scoped, e.g. `plan/<slug>-phase-03`, depending on whether phases are sequential or parallel.
   - Branch names must be short, lowercase, and filesystem/git-safe.

2. Plans must have a minimal phase status table at the bottom.
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

3. Commits are checkpoint-oriented and terse.
   - Commit message format:
     - `plan:<plan-slug> phase:<N> <keyword>`
   - Examples:
     - `plan:skill-git-exec phase:1 scaffold`
     - `plan:skill-git-exec phase:2 branch-rules`
     - `plan:skill-git-exec phase:3 cron`
   - No long commit bodies unless the user asks.
   - Each commit must reference the plan and phase.

4. No PR and no CI lifecycle.
   - The skill must explicitly avoid PR creation, PR monitoring, CI watching, and merge automation.
   - Verification is local: tests, lint, validation commands, file inspection, and git status.

5. Checkpoint commits happen at least at the end of each phase.
   - More frequent commits are allowed when a sub-step is independently useful and the working tree is clean.
   - Before committing, the agent must inspect `git status --short` and the relevant diff.
   - After committing, the agent must verify `git status --short` again.

6. Cron management is integrated.
   - The skill prompts/asks the user for cron parameters when autonomous continuation is requested.
   - Required cron parameters:
     - schedule
     - plan path
     - execution mode: sequential or parallel
     - branch naming mode: plan branch or phase branch
     - max phases/tasks per run
     - verification command(s)
     - delivery target, if not current chat
   - The created cron prompt must be self-contained because cron jobs run in fresh sessions.
   - Cron jobs must not recursively create more cron jobs.
   - Sequential mode advances only the next eligible `TODO` phase.
   - Parallel mode may work on independent phases using distinct phase branches.

7. The skill must include clear stop conditions.
   - Stop when a phase is `BLOCKED`, `FAILED`, or needs user input.
   - Stop when local verification fails and no obvious fix is in scope.
   - Stop before destructive git operations unless explicitly authorized.
   - Stop if uncommitted unrelated changes are present.

---

## Proposed Skill

**Name:** `git-managed-plan-execution`

**Category:** `software-development`

**Description:** `Use when executing implementation plans in a git repository with named branches, phase status tables, checkpoint commits, and optional cron-driven continuation; excludes PR and CI workflows.`

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
- Create via `skill_manage(action='create')`: user-local skill `software-development/git-managed-plan-execution/SKILL.md`

**Steps:**
1. Draft valid YAML frontmatter:
   - `name`
   - `description`
   - `version`
   - `author`
   - `license`
   - `platforms`
   - `metadata.hermes.tags`
   - `metadata.hermes.related_skills`
2. Add top-level sections:
   - Overview
   - When to Use
   - Inputs to Collect
   - Branch Management
   - Plan Phase Status Table
   - Execution Workflow
   - Commit Protocol
   - Cron Management
   - Verification
   - Stop Conditions
   - Common Pitfalls
   - Verification Checklist
3. Validate that the content starts with `---`, has non-empty body, and description is under 1024 characters.

**Verification:**
- `skill_manage(action='create', ...)` succeeds.
- Skill content is readable with `skill_view(name='git-managed-plan-execution')` in a fresh session, or inspect the written file path if current session cache prevents discovery.

**Commit:**
- If this repository is used to track the plan only, commit after the skill is created if the user wants this PLAN.md tracked.
- Commit message: `plan:git-managed-plan-execution phase:1 scaffold`

### Phase 2: Encode branch and plan-status protocol

**Objective:** Add concrete branch naming and status table instructions.

**Files:**
- Modify: `git-managed-plan-execution/SKILL.md`

**Steps:**
1. Define branch naming rules:
   - Plan branch: `plan/<slug>`
   - Phase branch: `plan/<slug>-phase-<NN>`
   - Optional user-provided branch override.
2. Define preflight git checks:
   - `git status --short`
   - `git branch --show-current`
   - `git rev-parse --show-toplevel`
   - check for unrelated uncommitted changes.
3. Define the bottom-of-plan phase status table format:

```markdown
## Phase Status

| Number | Title | Status |
|---:|---|---|
| 1 | Draft the skill skeleton | TODO |
| 2 | Encode branch and plan-status protocol | TODO |
```

4. Define valid statuses and transitions:
   - `TODO -> IN PROGRESS -> DONE`
   - `TODO/IN PROGRESS -> DEFERRED`
   - `IN PROGRESS -> FAILED`
   - `TODO/IN PROGRESS -> BLOCKED`
   - `TODO -> SKIPPED`

**Verification:**
- Read the skill and confirm branch naming, status table, and transitions are explicit.

**Commit:**
- `plan:git-managed-plan-execution phase:2 branch-status`

### Phase 3: Encode execution and commit workflow

**Objective:** Add the phase execution loop and short commit-message policy.

**Files:**
- Modify: `git-managed-plan-execution/SKILL.md`

**Steps:**
1. Define the execution loop:
   - Read plan.
   - Read bottom phase status table.
   - Select next phase depending on sequential or parallel mode.
   - Mark phase `IN PROGRESS` before work.
   - Execute scoped work.
   - Run local verification.
   - Inspect diff/status.
   - Commit if clean and scoped.
   - Mark phase `DONE`, or `FAILED`/`BLOCKED`/`DEFERRED` as appropriate.
   - Commit the phase status update if it is part of the repo.
2. Define commit message format:
   - `plan:<plan-slug> phase:<N> <keyword>`
3. Add examples for clean commits and for multiple commits within one phase.
4. State explicitly: no PR creation, no CI polling, no merge automation.

**Verification:**
- Skill includes exact command examples for:
   - checking current branch
   - creating branch
   - checking status
   - committing
   - rechecking clean state

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
   - Which plan path?
   - Sequential or parallel phases?
   - Branch naming mode: plan branch or phase branch?
   - Max phases/tasks per run?
   - Verification command(s)?
   - Delivery target, if not current chat?
3. Add cron prompt template:
   - self-contained repo path
   - plan path
   - execution mode
   - branch rules
   - valid statuses
   - commit format
   - local verification only
   - no PR / no CI
   - no recursive cron creation
4. Add `cronjob(action='create', ...)` example.
5. Add guidance for listing/updating/removing jobs:
   - always `cronjob(action='list')` before update/pause/resume/remove.

**Verification:**
- Skill includes a complete cron prompt template that can run without current-chat context.
- Skill states cron runs must not ask questions and must stop with a clear report when parameters are missing.

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
3. Confirm the new skill does not duplicate full PR/CI workflows.
4. Confirm it references existing skills but gives a single coordinated protocol.
5. Confirm destructive git operations require explicit authorization.
6. Optionally dispatch a reviewer subagent for spec compliance and quality review.

**Verification:**
- Frontmatter valid.
- Description under 1024 characters.
- Body contains required workflow sections.
- Branch, commit, status table, and cron requirements from this PLAN.md are all represented.

**Commit:**
- `plan:git-managed-plan-execution phase:5 validate`

---

## Definition of Done

The skill is complete when:

- `git-managed-plan-execution` exists as a user-local Hermes skill.
- The skill provides a single coordinated plan-execution workflow.
- Branch management is explicit.
- Bottom-of-plan phase status table is required and specified.
- Commit messages are short and reference plan + phase.
- PR and CI workflows are explicitly excluded.
- Cron creation and cron management are integrated.
- Sequential vs parallel phase execution is documented.
- Stop conditions and safety rules are documented.
- The skill has been validated and reviewed.

---

## What Not To Do

- Do not create PR automation in this skill.
- Do not add CI monitoring or CI auto-fix loops.
- Do not require GitHub; local git is sufficient.
- Do not use long commit bodies by default.
- Do not assume phases are parallel-safe unless the plan or user says so.
- Do not let cron jobs recursively create more cron jobs.
- Do not overwrite or discard unrelated working-tree changes.

---

## Phase Status

| Number | Title | Status |
|---:|---|---|
| 1 | Draft the skill skeleton | TODO |
| 2 | Encode branch and plan-status protocol | TODO |
| 3 | Encode execution and commit workflow | TODO |
| 4 | Add cron integration | TODO |
| 5 | Validate, review, and harden the skill | TODO |
