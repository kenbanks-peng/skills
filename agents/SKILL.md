---
name: agents
description: Run parallel or dependent coding tasks with Aven and Workmux. Track ownership, verify merges, and resume interrupted work.
---

# Aven + Workmux

## Operating rules

Load **aven** for tasks and follow **coordinator** for dispatch, monitoring, review, session reuse, and merging. Apply the Aven integration and Pi overrides below. Read **workmux**, **worktree**, and **merge** before using their commands.

- Resolve `workmux.yaml` relative to this skill and pass its absolute path as `--config <workflow-config>` to every `workmux add` and `workmux open` call, including session reuse. The workflow config owns the worker pane command; do not pass `--agent` or edit user or project Workmux configuration.
- Pi invokes skills with `/skill:<name>` and appends trailing arguments as a user request (rather than substituting `$ARGUMENTS`). Replace coordinator's `/merge` command with `/skill:merge --into <recorded-base> --keep`, using the task's recorded base branch. This retains the worktree until verification passes.
- Only the orchestrator changes Aven task status, ownership, comments, and notes. Workers use Aven as read-only context.
- Give each task one worktree. Keep one active task per worktree.
- Create tasks for discovered work with scope and acceptance criteria. Keep deferred work outside the current run.

## Workflow

1. **Prime the tools.**
   - Resolve the sibling `workmux.yaml` to an absolute path and confirm it exists before dispatch.
   - Confirm the project is in a Git repository. If not, run `git init` and create an initial commit. Choose the base branch for merging completed work.
   - Use `aven project` to find or create a project mapped to the repository.

2. **Assign ready tasks.**
   - If not already specified, record prerequisite relationships in Aven for planned and discovered tasks before scheduling them. Use those dependencies to determine readiness.
   - Use `aven list` with appropriate filtering options. Inspect candidate tasks with `aven context <task-ref>`.
   - Start dependents only after prerequisites are marked `done` under step 4.
   - Record the Workmux handle, branch, and base branch in the task's Aven notes.
   - Identify the coding agent for all planned and discovered tasks assigned to Pi with `aven edit <task-ref> --agent pi`.
   - Mark tasks `active` when work starts.

3. **Supply task context and review evidence.**
   - Start from the recorded base branch, including merged prerequisites.
   - Before reusing a worktree, preserve unrelated changes separately and update to the base. The merge skill stages all changes.
   - Give each worker the task reference, base branch, and these instructions:
     1. Act as a delegated worker and report completion only to the orchestrator.
     2. Run `aven context <task-ref>`.
     3. Implement the task, verify acceptance criteria, and commit.
     4. Report a concise implementation summary, notable decisions, affected components, check results, commit IDs, blockers, and discovered work. Leave Aven updates and user notification to the orchestrator.
   - During coordinator's review, validate the worker's implementation summary and other report details against Git state and `aven show <task-ref>`. Treat the summary as a draft until merged work passes verification. Workmux `done` is not Aven task completion.

4. **Verify merged work and complete each task.**
   - Confirm the merge reached the base branch and run required checks on the merged revision.
   - If checks fail or cannot run, keep the task `active` and retain its worktree. Record that it was merged, the check results, and the next action in Aven.
   - Once acceptance criteria and checks pass, add a durable Aven completion comment with the validated implementation summary, notable decisions, affected components, merged revision, check results, and `cleanup pending`. Then mark the task `done` and release dependents.
   - Clean up the completed task's worktree and branch; record `cleanup complete` in Aven.

5. **Complete the run.**
   - Confirm all selected tasks are verified and merged, run-wide checks pass on the final base revision, and cleanup is finished.
   - If any condition remains unmet, leave an Aven handoff for unfinished work using the guidance below.

## Recovery and handoff

- After context loss or worker exit, find unfinished tasks with `aven list --open` and inspect them with `aven context <task-ref>`. Use the Workmux handle and branches recorded in Aven notes to check Workmux and Git before restarting work. Resolve conflicting ownership or merge records first.
- Finish pending cleanup for `done` tasks without merging again.
- Before reassigning work, stop the previous worker, preserve its changes, and check whether it merged. Record the handoff and update the coding-agent identification with `aven edit <task-ref> --agent <agent>`, or remove it with `aven edit <task-ref> --clear-agent` if it no longer applies.
- For unfinished tasks, record progress, check results, blockers, and next actions in Aven. Retain their worktrees, even if coordinator would normally remove them.
