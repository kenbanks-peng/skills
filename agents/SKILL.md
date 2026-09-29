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

Pass the absolute path of this skill's sibling `workmux.yaml` as `--config` to every `workmux add` and `workmux open`, including session reuse. Do not pass `--agent` or edit user/project Workmux configuration.

### Workmux setup

Even for parallel workers, serialize `workmux add` and `workmux open` per repository to avoid Git/Workmux metadata contention. Preserve prompt-file preparation and startup checks.

On a lock error, pause dispatch. Inspect owning processes, `workmux list`, and `git worktree list` before retrying. Preserve existing work, reconcile partial resources, and remove only resources confirmed safe to discard. Never delete a potentially live lock.

### Multiplexer context

This workflow uses Herdr, not tmux. Preserve inherited `HERDR_ENV` and `HERDR_SESSION`. Omit `--parent-session` and skip the required skills' tmux session lookup and placement instructions.

If startup confirmation fails, inspect `workmux status` and `workmux capture <handle>` for each unconfirmed worker before retrying or monitoring completion. Preserve unfinished work under [Recovery and handoff](#recovery-and-handoff).

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
- When setting status with `aven edit`, include `--agent <agent>` (for example, `--agent pi`) while in`active` state, otherwise include `--clear-agent`.
- Use one worktree per task, with at most one active task per worktree.
- Create tasks for discovered work, each with scope and acceptance criteria. Exclude deferred work from the current run.

## Workflow

### 1. Prepare the tools and repository

1. If needed, initialize the Git repository with `git init` and an initial commit.
2. Use the base branch for merges.
3. Use `aven project` to find (or if needed, to create) an Aven project mapped to the repository.

### 2. Select ready tasks

1. Ensure any missing prerequisites are recorded in Aven before scheduling any task.
2. Select tasks with `aven list --ready` and applicable filters; inspect each with `aven context <task-ref>`. Mark prerequisites `done` only after [Verify and complete the task](#5-verify-and-complete-the-task).
3. Mark the task `active` when starting it.

### 3. Prepare and dispatch a worker

1. Start from the chosen base branch, including merged prerequisites.
2. Before reusing a worktree, preserve unrelated changes separately and ensure its task branch includes the latest base revision. The merge skill stages all changes.
3. Create or reuse the task's worktree through the coordinator workflow.
4. Record the Workmux handle, branch, and base branch in the task's Aven notes.
5. Give the worker the task reference, the base branch, and the instructions in [Worker brief](#worker-brief).

### 4. Review and merge the result

1. Follow the coordinator review process.
2. Validate the worker's report against Git state and `aven show <task-ref>`.
3. Treat the summary as a draft until the merged work passes verification. Workmux `done` is not Aven task completion.
4. Follow the coordinator merge process and apply the [Pi merge command](#pi-merge-command) override.

### 5. Verify and complete the task

1. Confirm that the merge reached the base branch. Run the required checks on the merged revision.
2. If checks fail or cannot run, keep the task `active` and retain its worktree. Record the merge, check results, and next action in Aven.
3. When acceptance criteria and checks pass, add a durable Aven completion comment containing the validated [worker report](#worker-brief), merged revision, check results for that revision, and `cleanup pending`.
4. Run `aven edit <task-ref> --status done --clear-agent`, then query `aven list --ready` with the current run's filters for newly eligible tasks.
5. Clean up the completed task's worktree and branch. Record `cleanup complete` in Aven.

### 6. Complete the run

1. Confirm that all selected tasks are verified and merged.
2. Run the run-wide checks on the final base revision and confirm that they pass.
3. Confirm that cleanup is complete.
4. If any condition is unmet, record a handoff under [Recovery and handoff](#recovery-and-handoff).

## Worker brief

Give each worker these instructions:

1. Act as a delegated worker and report completion only to the orchestrator.
2. Run `aven context <task-ref>`.
3. Implement the task, verify the acceptance criteria, and commit.
4. Report a concise implementation summary, notable decisions, affected components, check results, commit IDs, blockers, and discovered work.
5. Treat Aven as read-only. Leave Aven updates and user notification to the orchestrator.

## Recovery and handoff

### Interrupted work

After context loss or worker exit, find unfinished tasks with `aven list --open` and inspect each with `aven context <task-ref>`. Before restarting, check Workmux and Git using the handle and branches in Aven notes. Resolve conflicting ownership or merge records first.

### Pending cleanup

Finish pending cleanup for `done` tasks without merging again.

### Reassignment

Before reassigning work, stop the previous worker, preserve its changes, check whether it merged, and record the handoff. Follow the status/agent rule in [Operating invariants](#operating-invariants) for reassignment or any move out of `active`.

### Unfinished tasks

For unfinished tasks, record progress, check results, blockers, and next actions in Aven. Retain their worktrees, even if the coordinator would normally remove them.
