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

This skill connects Aven's task records to the coordinator's Workmux lifecycle. Use the loaded skills as the source of truth:

- **aven**: task operations, dependencies, assignment commands, and durable notes.
- **coordinator**: dispatch, monitoring, session reuse, serialized worker-executed merging, and cleanup.
- **workmux**, **worktree**, and **merge**: CLI, worktree setup, and integration mechanics.

Use the coordinator's full lifecycle, rather than the worktree skill's dispatch-only completion rule. The rules below govern the connection between task state and that lifecycle.

## Workflow

1. **Establish the integration context.**
   - Confirm the Aven project maps to the intended repository and choose the integration base branch.
   - Use `{{AGENT}}` as the worker agent, including for session reuse. Apply that selection through the related skills' agent-selection procedures; verify status hooks and a supported merge-skill invocation before dispatch. Adapt the coordinator's Claude Code examples to that invocation. If unavailable, report the blocker.

2. **Bind tasks to sessions.**
   - Select ready Aven tasks and inspect their context using the Aven skill. Dispatch independent tasks together; a dependent task is eligible only once its prerequisites are confirmed merged into the integration base, even if Aven already lists it as ready.
   - Keep one active task per worktree. Record each task's Workmux handle, branch, integration base, and stable Aven session ID (`{{SESSION_PREFIX}}:<handle>`) in its durable context. Reused sessions retain that ID.
   - Assign each dispatched task to that session through Aven. If assignment is unsupported, report degraded ownership tracking and continue only with unambiguous ownership in task state and notes.
   - The orchestrator alone changes Aven task state: mark work `active` when it starts, retain that state through review and merge, and apply the completion gate below before marking it `done`. Workers report progress and discovered work to the orchestrator.

3. **Dispatch through the coordinator.**
   - Add the Aven task reference, session ID, ownership boundary, and integration base to the coordinator's worker prompt. Require the worker to read its Aven context and return acceptance evidence, commit IDs, and blockers, leaving task-state changes to the orchestrator.
   - Create worktrees from the integration base. Before dependent work starts in a reused worktree, require it to incorporate the merged prerequisites while preserving existing changes.
   - Workers return results for review; the coordinator triggers merging after acceptance rather than having workers merge automatically on implementation completion.

4. **Reconcile results and unlock work.**
   - At each coordinator review, reconcile the worker report and Git state with the Aven task. Workmux `done` means the agent finished its turn, not that the task is complete. An exited agent likewise requires reconciliation before restart or reassignment.
   - For accepted work, use the coordinator's merge procedure. Mark the Aven task `done` only after acceptance criteria are verified and the merge is confirmed in the intended integration base. Record verification and integration evidence in Aven, then re-evaluate ready tasks against their merged prerequisites.
   - For corrections, use the coordinator's session-reuse procedure and keep Aven ownership aligned. Release stale assignments when abandoning or reassigning work.

## Completion and handoff

Finish when every selected task is either complete under the gate above or has a durable blocker, integration-branch tests and exact-output checks pass, and the coordinator's cleanup is complete for accepted work.

For blocked or interrupted work, retain changes and leave an Aven handoff with the task, assignment, handle, branch, integration base, progress, verification evidence, blocker, and next action. Retaining blocked work is an explicit exception to the coordinator's merge-or-remove lifecycle, not permission to drop a running agent from monitoring.
