---
name: agents
description: Run parallel or dependent coding tasks with Aven and Workmux. Track ownership, verify merges, and resume interrupted work.
---

# Aven + Workmux

## Required skills

Load and follow each skill before the corresponding operation:

- **aven** — task management with the `aven` CLI.
- **coordinator** — worker dispatch, monitoring, review, session reuse, and merge orchestration.
- **workmux** — worktree and agent management with the `workmux` CLI.
- **worktree** — task delegation to worktree agents.
- **merge** — worker-side commit, rebase, and merge workflow.

Apply the integration overrides below when you follow these skills.

## Integration overrides

### Workmux configuration

Resolve the sibling `workmux.yaml` relative to this skill to an absolute path and confirm that it exists. Pass that path as `--config <workflow-config>` to every `workmux add` and `workmux open` call, including session reuse. The workflow config owns the worker pane command. Do not pass `--agent` or edit user or project Workmux configuration.

### Pi merge command

Pi invokes skills with `/skill:<name>` and appends trailing arguments as a user request instead of substituting `$ARGUMENTS`. Replace the coordinator's `/merge` command with `/skill:merge --into <recorded-base> --keep`. Use the task's recorded base branch. The `--keep` option retains the worktree until verification passes.

## Operating invariants

- Only the orchestrator changes Aven task status, ownership, comments, and notes. Workers use Aven as read-only context.
- Couple coding-agent assignment to task status in the same `aven edit` call: use `--status active --agent <agent>` (`pi` for Pi), and `--status <state> --clear-agent` for every non-`active` state.
- Give each task one worktree. Keep one active task per worktree.
- Create tasks for discovered work. Give each task a scope and acceptance criteria. Keep deferred work outside the current run.

## Workflow

### 1. Prepare the tools and repository

1. Ensure the project is in a Git repository. If needed, run `git init` and create an initial commit.
2. Choose the base branch for merging completed work.
3. Ensure an Aven project maps to the repository. If needed, use `aven project` to find or create it.

### 2. Select ready tasks

1. If prerequisite relationships are not specified, record them in Aven for planned and discovered tasks before scheduling the tasks.
2. Select candidates with `aven list --ready` and the applicable filters, then inspect each with `aven context <task-ref>`. Let Aven determine dependency readiness; mark prerequisites `done` only after [Verify and complete the task](#5-verify-and-complete-the-task).
3. When Pi starts work on a planned or discovered task, run `aven edit <task-ref> --status active --agent pi`.

### 3. Prepare and dispatch a worker

1. Start from the recorded base branch, including merged prerequisites.
2. Before you reuse a worktree, preserve unrelated changes separately and update the worktree to the base branch. The merge skill stages all changes.
3. Create or reuse the task's worktree through the coordinator workflow.
4. Record the Workmux handle, branch, and base branch in the task's Aven notes.
5. Give the worker the task reference, the base branch, and the instructions in [Worker brief](#worker-brief).

### 4. Review and merge the result

1. Follow the coordinator review process.
2. Validate the worker's implementation summary and other report details against the Git state and `aven show <task-ref>`.
3. Treat the summary as a draft until the merged work passes verification. Workmux `done` is not Aven task completion.
4. Follow the coordinator merge process and apply the [Pi merge command](#pi-merge-command) override.

### 5. Verify and complete the task

1. Confirm that the merge reached the base branch. Run the required checks on the merged revision.
2. If checks fail or cannot run, keep the task `active` and retain its worktree. Record the merge, check results, and next action in Aven.
3. When the acceptance criteria and checks pass, add a durable Aven completion comment. Include the validated implementation summary, notable decisions, affected components, merged revision, check results, and `cleanup pending`.
4. Run `aven edit <task-ref> --status done --clear-agent`, then query `aven list --ready` with the current run's filters for newly eligible tasks.
5. Clean up the completed task's worktree and branch. Record `cleanup complete` in Aven.

### 6. Complete the run

1. Confirm that all selected tasks are verified and merged.
2. Run the run-wide checks on the final base revision and confirm that they pass.
3. Confirm that cleanup is complete.
4. If a condition is not met, leave an Aven handoff for the unfinished work. Use the guidance in [Recovery and handoff](#recovery-and-handoff).

## Worker brief

Give each worker these instructions:

1. Act as a delegated worker and report completion only to the orchestrator.
2. Run `aven context <task-ref>`.
3. Implement the task, verify the acceptance criteria, and commit.
4. Report a concise implementation summary, notable decisions, affected components, check results, commit IDs, blockers, and discovered work.
5. Treat Aven as read-only. Leave Aven updates and user notification to the orchestrator.

## Recovery and handoff

### Interrupted work

After context loss or worker exit, find unfinished tasks with `aven list --open`. Inspect each task with `aven context <task-ref>`. Use the Workmux handle and branches in the Aven notes to check Workmux and Git before you restart work. Resolve conflicting ownership or merge records first.

### Pending cleanup

Finish pending cleanup for `done` tasks without merging again.

### Reassignment

Before you reassign work, stop the previous worker, preserve its changes, and check whether it merged. Record the handoff. Apply the status and coding-agent rule in [Operating invariants](#operating-invariants) when assigning the task to the replacement agent or moving it to a non-`active` state.

### Unfinished tasks

For unfinished tasks, record progress, check results, blockers, and next actions in Aven. Retain their worktrees, even if the coordinator would normally remove them.
