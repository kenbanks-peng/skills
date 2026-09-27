---
name: agents
description: Orchestrate multiple coding agents with Aven tasks and Workmux worktrees. Use when work must be split across parallel or dependent agents, tracked through completion, merged safely, or delegated to avoid context limits in long-running agent sessions.
---

# Multi-agent orchestration

## Variables

- `{{AGENT}}` = `pi`
- `{{SESSION_PREFIX}}` = `workmux`

Treat these as document substitutions, not shell variables. Resolve them before constructing commands or worker prompts.

## Skill boundaries

This skill connects Aven's task records to the coordinator's Workmux lifecycle. Load **aven** and **coordinator** before execution, and the supporting skills before using their procedures. Use them as the source of truth:

- **aven**: task operations, dependencies, assignment commands, and durable notes.
- **coordinator**: dispatch, monitoring, session reuse, serialized worker-executed merging, and cleanup.
- **workmux**, **worktree**, and **merge**: CLI, worktree setup, and integration mechanics.

This skill governs Aven ownership, task completion, dependency readiness, and blocked-work retention. Coordinator governs dispatch (including tmux session selection), monitoring, serialized worker-executed merging, and cleanup within those constraints, including its full lifecycle rather than worktree's dispatch-only completion rule. Supporting skills govern command mechanics. If a procedure cannot satisfy these rules, report the blocker before executing it.

## Workflow

1. **Establish the integration context.**
   - Confirm the Aven project maps to the intended repository and choose the integration base branch.
   - When resuming orchestration after context loss, reconstruct the unfinished task/session set from Aven and reconcile it with Workmux and Git before dispatching new work. Resume dispatch only when each unfinished task has a known owner, worktree/branch state, and integration state. Treat unresolved discrepancies as blockers for the affected tasks.
   - Use `{{AGENT}}` as the worker agent, including for session reuse. Apply that selection through the related skills' agent-selection procedures; verify status hooks and a supported merge-skill invocation before dispatch. Adapt the coordinator's Claude Code examples to that invocation. If unavailable, report the blocker.

2. **Bind tasks to sessions.**
   - Select ready Aven tasks and inspect their context using the Aven skill. Dispatch independent tasks together; a dependent task is eligible only once its prerequisites satisfy the completion gate below, even if Aven already lists it as ready.
   - Keep one active task per worktree. Record each task's Workmux handle, branch, integration base, and stable Aven session ID (`{{SESSION_PREFIX}}:<handle>`) in its durable context. Reused sessions retain that ID.
   - Assign each dispatched task to that session through Aven. If assignment is unsupported, report degraded ownership tracking and continue only after recording the owning session unambiguously in the task's durable context.
   - The orchestrator alone changes Aven task status and assignments: mark work `active` when it starts, retain `active` status through review and merge, and apply the completion gate below before marking it `done`. Workers report progress and discovered work to the orchestrator.

3. **Dispatch through the coordinator.**
   - Add the Aven task reference, session ID, ownership boundary, and integration base to the coordinator's worker prompt. Require the worker to read its Aven context and return acceptance evidence, commit IDs, and blockers, leaving status and assignment changes to the orchestrator.
   - Create worktrees from the integration base. Before any new task starts in a reused worktree, reconcile retained changes and have the worker update it to the recorded integration base, including all merged prerequisites. Preserve unrelated work separately before reuse: merge's commit step stages all changes, so the worktree must contain only the assigned task's work.
   - Workers return results for review; the coordinator triggers merging after acceptance rather than having workers merge automatically on implementation completion.

4. **Reconcile results and unlock work.**
   - At each coordinator review, reconcile the worker report and Git state with the Aven task. Workmux `done` means the agent finished its turn, not that the task is complete. An exited agent likewise requires reconciliation before restart or reassignment.
   - For accepted work, use the coordinator's merge procedure. Before triggering a merge, verify that the procedure's effective rebase and merge targets match the task's recorded integration base; resolve any mismatch before proceeding. Request merge's `--keep` option to retain the worktree and session through verification; its default cleanup is premature for this workflow.
   - Mark the Aven task `done` only after acceptance criteria are verified, integration into the recorded base is confirmed, and required checks (including any task-specified exact-output assertions) pass on the resulting integration revision. Record that revision and verification evidence in Aven before unlocking dependents, then complete cleanup for that task. If integration checks fail or cannot run, retain `active` status and the worktree, record that integration already occurred, and use the retained session for corrections or handoff.
   - For corrections, use the coordinator's session-reuse procedure and keep Aven ownership aligned. Before reassigning a task, confirm that its previous worker has stopped acting on it, preserve its work, and reconcile any pending merge. Then transfer ownership and record the handoff. Release stale assignments when abandoning work.

## Completion and handoff

**Successful completion:** every selected task satisfies the completion gate above, any additional run-wide checks pass on the final integration revision, and the coordinator's cleanup is complete for accepted work.

**Blocked handoff:** every unfinished task or failed/unavailable check has a durable blocker and next action. Complete cleanup only for tasks that passed the completion gate; retain worktrees for tasks still awaiting verification or corrections.

For blocked or interrupted work, retain changes and leave an Aven handoff with the task, assignment, handle, branch, integration base, progress, verification evidence, blocker, and next action. Retaining blocked work is an explicit exception to the coordinator's merge-or-remove lifecycle. A durable blocker does not end monitoring responsibility. Continue monitoring running workers unless further coordinator action requires user input.
