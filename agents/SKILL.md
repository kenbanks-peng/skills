---
name: agents
description: Orchestrate multiple coding agents with Aven tasks and Workmux worktrees. Use when work must be split across parallel or dependent agents, tracked through completion, merged safely, or delegated to avoid context limits in long-running agent sessions.
---

# Multi-agent orchestration

## Document variables

{{AGENT}} = pi

## Related Skills

- **aven** owns task scope, dependencies, assignment, state, and durable handoff context. Use the Aven skill if available; otherwise, consult `aven skill`.
- **coordinator** owns Workmux spawning, prompt construction, monitoring, session reuse, serialized merging, and cleanup. Load it alongside this skill. This skill adds Aven ownership, task-state transitions, dependency scheduling, and acceptance gates.

## Workflow

1. **Prime the tools.**
   - Run `aven agent --help` before assignment.
   - Confirm the intended Git repository and integration base branch. Initialize a repository only when creating one is part of the requested work.
   - Using `aven project`, ensure that an appropriately mapped project is available. Create one if necessary.
   - Ensure that Workmux status hooks are installed for {{AGENT}}. Include `--agent {{AGENT}}` in every `workmux add` call, including session reuse.
   - The coordinator's examples assume Claude Code and `/merge`. Before dispatch, confirm that {{AGENT}} can invoke the merge skill and record its supported invocation in worker prompts. Use that invocation wherever the coordinator specifies `/merge`; if unavailable, report the blocker rather than assuming compatibility.

2. **Build execution waves.**
   - Run `aven list --ready` and inspect each candidate with `aven context <task-ref>`.
   - Map task dependencies. Waves govern dispatch eligibility, not merge timing: independent tasks can run together; dependent tasks become eligible only after their prerequisites are merged.
   - Give each task one Workmux handle and one stable, exact session ID, such as `workmux:<handle>`.
   - Assign ownership of all planned and discovered session tasks with `aven agent assign <task-ref> --session <session-id>`.
   - The orchestrator alone maintains Aven task state. Mark a task `done` only after its acceptance criteria are verified and its branch is confirmed merged into the integration base.
   - If assignment reports a server compatibility error, report degraded ownership tracking. Continue only when task status and durable notes provide unambiguous ownership; do not claim that session assignment succeeded.

3. **Dispatch one active task per worktree.**
   - Follow the coordinator's dispatch and session-reuse procedures. Create new worktrees from the integration base; before dependent work starts in a reused worktree, require it to incorporate all merged prerequisites while preserving existing changes.
   - Give the agent the Aven task reference, its ownership boundary, the integration base, and these completion requirements:
     1. Run `aven context <task-ref>`.
     2. Make only the requested change.
     3. Verify the acceptance criteria.
     4. Commit the complete change.
     5. Report verification evidence, commit IDs, and any blockers to the orchestrator; leave Aven state changes to the orchestrator.

4. **Monitor evidence, not only process state.**
   - Follow the coordinator's monitoring loop. Reconcile worker reports with Git state and `aven show <task-ref>`; a Workmux `done` status is not an Aven completion decision.
   - `No agent running` can mean that the agent exited. Inspect its branch and Aven task before you restart it.
   - For partial work, follow the coordinator's follow-up procedure, preserving changes and reconciling the Aven assignment and task state.

5. **Merge and unlock dependent work.**
   - Merge only a clean, committed branch whose task meets its acceptance criteria. Use the coordinator's serialized, worker-executed merge procedure as accepted results arrive; do not wait for the entire wave.
   - Confirm the merge landed in the intended integration base before marking the task `done`. Then run `aven list --ready` again and check newly eligible tasks against their merged prerequisites.
   - Release stale Aven assignments when work is abandoned or reassigned.

## Completion gate

The orchestration is complete only when:

- every selected Aven task is `done` or has a documented blocker;
- every accepted branch is merged;
- dependent outputs were built from merged prerequisite work;
- tests and exact-output checks pass on the integration branch;
- all orchestration changes are committed, with pre-existing user changes preserved; and
- worktrees and branches created for completed work are cleaned up. For blocked work, retain changes and record the task, assignment, handle, branch, blocker, and next action in a durable handoff. This explicit blocked handoff is an exception to the coordinator's merge-or-remove lifecycle; it does not permit silently dropping a running agent from monitoring.
