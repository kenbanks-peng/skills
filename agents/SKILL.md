---
name: agents
description: Run parallel or dependent coding tasks with Aven and Workmux. Track ownership, verify merges, and resume interrupted work.
---

# Aven + Workmux

Use **aven** for tasks and **coordinator** for dispatch, monitoring, session reuse, and merging. Read **workmux**, **worktree**, and **merge** before using their commands.

## Workflow

1. **Prime the tools.**
   - Load **aven** and **coordinator**.
   - Run `aven agent --help`.
   - Confirm the project is in a Git repository. If not, run `git init` and create an initial commit. Choose the base branch for merging completed work.
   - Use `aven project` to find or create a project mapped to the repository.
   - Ensure Workmux status hooks are installed for `pi`. Include `--agent pi` in every `workmux add` call, including session reuse.
   - Pi invokes skills with `/skill:<name>` and appends trailing arguments as a user request (rather than substituting `$ARGUMENTS`). Use `/skill:merge` in place of coordinator's Claude-specific `/merge` examples.

2. **Assign ready tasks.**
   - Run `aven list --ready` and inspect candidates with `aven context <task-ref>`.
   - Run independent tasks together. Start dependents only after prerequisites are marked `done` under step 5.
   - Give each task one worktree and a session ID: `workmux:<handle>`. Keep that ID when reusing the session.
   - Record the handle, branch, base branch, and session ID in the task's Aven context.
   - Assign all planned and discovered session tasks with `aven agent assign <task-ref> --session <session-id>`.
   - Only the orchestrator changes task status and ownership. Mark tasks `active` when work starts.
   - Create tasks for discovered work with scope and acceptance criteria. Keep deferred work outside the current run.

3. **Dispatch through coordinator.**
   - Keep one active task per worktree. Start from the recorded base branch, including merged prerequisites.
   - Before reusing a worktree, preserve unrelated changes separately and update to the base. The merge skill stages all changes.
   - Give each worker the task reference, session ID, base branch, and these instructions:
     1. Run `aven context <task-ref>`.
     2. Implement the task, verify acceptance criteria, and commit.
     3. Report check results, commit IDs, blockers, and discovered work. Leave task status and ownership to the orchestrator.
     4. Wait for review before merging. On approval, follow `/skill:merge --into <recorded-base> --keep`, treating the trailing flags as the merge skill's arguments.

4. **Monitor and review.**
   - Follow coordinator's monitoring loop through merging and verification.
   - Check worker reports against Git state and `aven show <task-ref>`. Workmux `done` means the worker finished its turn, not the task.
   - For corrections, reuse the session with a focused prompt.

5. **Merge, verify, and complete.**
   - Have workers merge accepted work one at a time: `workmux send <handle> "/skill:merge --into <recorded-base> --keep"`. Replace placeholders with the recorded handle and base branch. This retains the worktree for verification.
   - Confirm the merge reached the base branch and run required checks on the merged revision.
   - If checks fail or cannot run, keep the task `active` and retain its worktree. Record that it was merged, the check results, and the next action in Aven.
   - Once acceptance criteria and checks pass, record the merged revision, results, and `cleanup pending` in Aven. Then mark the task `done` and release dependents.
   - Clean up the completed task's worktree and branch; record `cleanup complete` in Aven.

## Recovery and handoff

- After context loss or worker exit, read Aven notes and check Workmux and Git before restarting work. Resolve conflicting ownership or merge records first.
- Finish pending cleanup for `done` tasks without merging again.
- Before reassigning work, stop the previous worker, preserve its changes, and check whether it merged. Record the handoff and release stale assignments.
- For unfinished tasks, record progress, check results, blockers, and next actions in Aven. Retain their worktrees, even if coordinator would normally remove them.

The run is complete when all selected tasks are verified and merged, run-wide checks pass on the final base revision, and cleanup is finished. Otherwise, leave an Aven handoff for unfinished work.
