---
name: agents
description: Run parallel or dependent coding tasks with Aven and Workmux. Track ownership, verify merges, and resume interrupted work.
---

# Aven + Workmux

## Required skills

Load and follow each skill before its operation:

- **aven** — task management.
- **coordinator** — agent dispatch, monitoring, review, and merging.
- **workmux** — worktree and agent management.
- **worktree** — worktree task delegation.
- **merge** — worker-side commit, rebase, and merge.

## Integration overrides

Integration overrides below take precedence.

### Workmux configuration

Default to Linux sandbox workers using `~/.config/workmux/agents.linux.yaml`. Use `~/.config/workmux/agents.macos.yaml` only when the user explicitly requests macOS workers. Both configurations inherit shared defaults from the global Workmux configuration; the macOS configuration explicitly disables sandboxing.

Resolve the selected configuration to an absolute path and pass it as `--config` to every `workmux add` and `workmux open`, including session reuse. Do not pass `--agent` or edit user/project Workmux configuration. Never silently fall back to macOS if Linux sandbox startup fails.

Record the selected execution mode and configuration path in Aven notes alongside the Workmux handle, task branch, and base branch. Preserve the recorded mode when resuming a task. Before switching modes, stop the existing worker and preserve its work; changing configuration does not migrate a running worker.

These configurations select the worker environment, not the orchestrator environment. The orchestrator remains on macOS unless separately requested.

### Workmux setup

Even for parallel workers, serialize `workmux add` and `workmux open` per repository to avoid Git/Workmux metadata contention. Preserve prompt-file preparation and startup checks.

On a lock error, pause dispatch. Inspect owning processes, `workmux list`, and `git worktree list` before retrying. Preserve existing work, reconcile partial resources, and remove only resources confirmed safe to discard. Never delete a potentially live lock.

### Multiplexer context

This workflow uses Herdr, not tmux. Preserve inherited `HERDR_ENV` and `HERDR_SESSION`. Omit `--parent-session` and skip the required skills' tmux session lookup and placement instructions.

If startup confirmation fails, inspect `workmux status` and `workmux capture <handle>` for each unconfirmed worker before retrying or monitoring completion. Preserve unfinished work under [Recovery and handoff](#recovery-and-handoff).

### Task progress tab

The orchestrator should open one `tasks` tab after initializing Aven. Require `HERDR_ENV=1`; use the project root:

```sh
herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd "<absolute-project-root>" --label tasks
herdr pane run <returned-root-pane-id> "aven --db .aven/tasks.db"
```

Keep it open until all selected tasks are merged, checks pass, and cleanup is complete. Then run `herdr tab close <recorded-tab-id>` before the final response.

### Merge notifications

Run `workmux merge` without `--notification`, overriding the merge skill's notification instructions. Leave user notification to the orchestrator. Include this override in every worker merge request.

### Pi merge command

Pi uses `/skill:<name>`; trailing arguments become a user request, not `$ARGUMENTS` substitutions. The merge target comes from the branch's `workmux-base` Git config.

Before merging, check it against the task's recorded base:

```sh
branch=$(git branch --show-current)
configured_base=$(git config --local --get "branch.$branch.workmux-base")
test "$configured_base" = "<recorded-base>"
```

Stop if the base is missing or mismatched. Otherwise, replace the coordinator's `/merge` with `/skill:merge --keep` to retain the worktree until verification passes.

## Operating invariants

- Only the orchestrator updates Aven task status, ownership, comments, and notes; workers treat Aven as read-only.
- When setting status with `aven --db .aven/tasks.db edit`, include `--agent <agent>` (for example, `--agent pi`) while in`active` state, otherwise include `--clear-agent`.
- Use one worktree per task, with at most one active task per worktree.
- Create tasks for discovered work, each with scope and acceptance criteria. Exclude deferred work from the current run.

## Task note format

Use these prefixes for orchestrator-written Aven notes and comments. They are note templates, not shell commands. These rules override more verbose administrative reporting in the required skills.

- Keep administrative entries to one line per event. Record only actual transitions; do not narrate routine commands, polling, or repeat unchanged metadata.
- Keep agent activity and results substantive and concise: state the key change or finding and its evidence. Include decisions or failures only when they affect the outcome. Do not reproduce the full worker report.
- Reference earlier dispatch metadata rather than repeating it. Record changed handles, branches, or execution modes explicitly.
- Report observed facts only; worker claims remain provisional until verified.
- Reference the Git-verified starting revision in `DISPATCH`, the worker commit in `RESULT`, and the verified base revision in `MERGE`. Use Git short-form SHAs for all revision references in notes and comments, including `SUMMARY`, generated with `git rev-parse --short <revision>` so the abbreviation is unambiguous in the repository. Check each reference against Git; do not use a branch name alone as the revision record.

### Templates

```text
DISPATCH: <agent> started in <handle> on <task-branch> at <starting-revision-short-SHA>, based on <base>. <Linux|macOS> worker using <config-path>.
ACTIVITY: <key progress>. <Significant decision and reason, if needed>.
RESULT: <key change or finding> in commit <commit-short-SHA>. <Decisive check result>. Awaiting merge verification.
MERGE: Merged into <base> at <revision-short-SHA>. <Check results>. Verified and done. Cleanup complete.
BLOCKED: <blocker>. Work retained in <worktree/branch>. <Owner> to <next action>.
SUMMARY: <delivered outcome>. <Acceptance evidence and final checks> at <revision-short-SHA>. <Follow-up work, if any>.
```

Write each event as a separate note in plain sentences, not a list of key-value fields. Display paths under the user's home directory with `~` in notes. Continue to pass resolved absolute configuration paths to Workmux commands. Omit the task reference when the note is attached to that task; include it in shared or run-level notes. Omit optional details when irrelevant; do not fill notes with empty placeholders. `ACTIVITY` is for meaningful developments, not heartbeat updates. `RESULT` records a substantive, concise worker outcome once, not a full report; validate it without copying it into the completion comment. Include closure in the `MERGE` completion comment only after verification, Aven status `done`, and cleanup are complete; do not emit a separate `CLOSED` entry. If cleanup is pending or verification fails, record the verified facts and next action without claiming closure. Use `SUMMARY` once at run completion; an unfinished run needs a handoff, not a closure claim.

## Workflow

### 1. Prepare the tools and repository

1. If needed, initialize the Git repository with `git init` and an initial commit.
2. Use the base branch for merges.
3. Initialize the aven database and project based on instructions in the aven skill.
4. Open the [Task progress tab](#task-progress-tab) before scheduling workers.

### 2. Select ready tasks

1. Ensure any missing prerequisites are recorded in Aven before scheduling any task.
2. Select tasks with `aven --db .aven/tasks.db list --ready` and applicable filters; inspect each with `aven --db .aven/tasks.db context <task-ref>`. Mark prerequisites `done` only after [Verify and complete the task](#5-verify-and-complete-the-task).
3. Mark the task `active` when starting it.

### 3. Prepare and dispatch a worker

1. Start from the chosen base branch with merged prerequisites.
2. Before worktree reuse, preserve unrelated changes separately and update the task branch with the latest base. The merge skill stages all changes.
3. Use the coordinator workflow to create or reuse the task's worktree.
4. Add a `DISPATCH` note using the [Task note format](#task-note-format), including execution mode and configuration path.
5. Give the worker the task reference, base branch, and [Worker brief](#worker-brief).

### 4. Review and merge the result

1. Follow coordinator review.
2. Validate the worker report against Git state and `aven --db .aven/tasks.db show <task-ref>`.
3. Keep the report provisional until merged-work verification passes. Workmux `done` does not complete the Aven task.
4. Follow coordinator merging with the [Pi merge command](#pi-merge-command) override.

### 5. Verify and complete the task

1. Confirm the merge reached the base branch; run required checks on that revision.
2. If checks fail or cannot run, keep the task `active` and retain its worktree. Return actionable failures to the worker for repair, review and merge the fix, then repeat verification on the updated base revision. If blocked, record the merge, check results, blocker, and next action in Aven; report the blocker to the user.
3. Once acceptance criteria and checks pass, retain the Git-verified merged revision and check results for the completion comment. Do not repeat the worker report.
4. Mark the task `done`, then query `aven --db .aven/tasks.db list --ready` with the run's filters for newly eligible tasks.
5. Clean up the task's worktree and branch; add one `MERGE` completion comment in Aven containing the merged revision, check results, and closure: `Verified and done. Cleanup complete.` If cleanup fails, record pending cleanup and the next action without claiming closure.

### 6. Complete the run

1. Confirm all selected tasks are verified and merged.
2. Run run-wide checks on the final base revision; require passing results.
3. Confirm cleanup is complete.
4. If any condition is unmet, record a handoff under [Recovery and handoff](#recovery-and-handoff) and leave the task progress tab open.
5. Otherwise, close the run-owned [Task progress tab](#task-progress-tab) before the final response.

## Worker brief

Give each worker these instructions:

1. Treat Aven as read-only; leave updates and user notification to the orchestrator. Follow the [Merge notifications](#merge-notifications) override.
2. Run `aven --db .aven/tasks.db context <task-ref>`.
3. Implement the task, verify acceptance criteria, and commit.
4. Report only to the orchestrator: a concise implementation summary, notable decisions, affected components, check results, commit IDs, blockers, and discovered work.

## Recovery and handoff

### Interrupted work

After context loss or worker exit, run `aven --db .aven/tasks.db list --open` and inspect each task with `aven --db .aven/tasks.db context <task-ref>`. Before restarting, check Workmux and Git using handles and branches from Aven notes; resolve ownership or merge-record conflicts.

### Pending cleanup

Finish pending cleanup for `done` tasks without merging again.

### Reassignment

Before reassignment, stop the previous worker, preserve its changes, check whether it merged, and record the handoff.

### Unfinished tasks

Record progress, check results, blockers, and next actions in Aven. Retain unfinished worktrees, overriding coordinator cleanup.
