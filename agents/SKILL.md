---
name: agents
description: Coordinate Aven tasks through Workmux agents. Use for parallel or dependent work requiring tracked ownership, verified integration, or durable recovery across agent sessions.
---

# Aven + Workmux

Delegate task operations to **aven** and the execution lifecycle to **coordinator**, including its session-selection rules and monitoring through integration—not worktree's dispatch-only endpoint. Read **workmux**, **worktree**, and **merge** before using their mechanics.

This skill adds the task/session binding and completion gate below; these constrain the supporting skills' lifecycle and cleanup.

## Workflow

1. **Prime the tools.**
   - Load **aven** (including its `aven skill` instructions) and **coordinator**.
   - Run `aven agent --help` to confirm assignment commands are available.
   - Confirm the target folder belongs to the intended Git repository; an existing-repository mismatch is a blocker. For an intended new repository, run `git init` and establish an initial commit before dispatch. Choose an existing local integration base branch.
   - Using `aven project`, ensure an appropriately mapped project exists for the target repository. Create one if necessary and verify its folder mapping before dispatch.
   - Ensure Workmux status hooks are installed for `pi`. Include `--agent pi` in every `workmux add` call, including session reuse.
   - Before dispatch, confirm `pi` can invoke the merge skill and record its supported invocation in worker prompts. Use that invocation wherever coordinator's Claude-specific examples specify `/merge`; if unavailable, report the blocker.

2. **Bind ready tasks.**

Assign ownership of all planned and discovered session tasks with `aven agent assign <task-ref> --session <session-id>`.

The orchestrator may create Aven tasks for discovered work, recording scope and acceptance criteria before selecting them for execution. Record deferred discoveries as follow-up tasks outside the selected run.

Use Aven's readiness and context procedures, but dispatch dependents only after prerequisites meet step 4's verified-integration gate and are marked `done`. Cleanup does not block dependents.

Keep one active task per worktree. Record this binding in each task's durable Aven context:

- Workmux handle, branch, and integration base.
- Stable ownership session ID: `workmux:<handle>`, retained on session reuse.

The orchestrator alone changes task status and ownership. Mark tasks `active` when work starts and retain that status through review and integration.

3. **Dispatch through coordinator.** Add the task reference, session ID, integration base, and orchestrator-only status/ownership rule to each worker prompt. Require workers to read their Aven context and report acceptance evidence, commit IDs, blockers, and discovered work. Workers await review before receiving merge instructions.

   Start from the recorded base, including merged prerequisites. Before reusing a worktree for another task, reconcile retained work and update to that base. Preserve unrelated changes separately: merge stages all changes, so only the assigned task's work may remain.

4. **Verify integration before completing the task.** At coordinator review, reconcile the worker report and Git state with Aven. Workmux `done` means a finished turn, not a completed task.

   For accepted work, use coordinator's serialized worker-executed merge procedure. Invoke merge with `--into <recorded-base> --keep` so both rebase and merge use the recorded base and the worktree/session survives verification. Confirm the invocation supports both flags and targets the recorded base before starting it.

   Mark the Aven task `done` only when acceptance criteria are met, integration into the recorded base is confirmed, and required checks pass on the resulting integration revision. Record that revision, verification evidence, and `cleanup pending` in Aven **before** marking done and unlocking dependents. Then clean up and record `cleanup complete` in Aven. If checks fail or cannot run, retain `active` status and the worktree, and record that integration already occurred so recovery does not mistake it for unmerged work.

## Recovery and handoff

After context loss or worker exit, reconstruct unfinished bindings from Aven, including `done` tasks with pending cleanup. Reconcile ownership, worktree/branch state, integration state, and cleanup state with Workmux and Git before restarting or dispatching affected tasks. Finish pending cleanup for verified tasks without repeating integration. Treat discrepancies as blockers.

Use coordinator's session-reuse procedure for corrections. Before transferring ownership, confirm the previous worker has stopped, preserve its work, and reconcile pending integration. Record the handoff and release stale assignments when abandoning work.

For unfinished work, update the task's binding with progress, verification evidence, blocker, and next action. Retain its worktree until verification or correction is complete: this overrides coordinator's merge-or-remove endpoint, not its responsibility to monitor running workers.

The run is complete when every selected task passes step 4, any run-wide checks pass on the final integration revision, and accepted-work cleanup is complete. Otherwise leave a durable blocked handoff.
