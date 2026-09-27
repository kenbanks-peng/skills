---
name: agents
description: Orchestrate multiple coding agents with Aven tasks and Workmux worktrees. Use when work must be split across parallel or dependent agents, tracked through completion, merged safely, or delegated to avoid context limits in long-running agent sessions.
---

# Multi-agent orchestration

## Document variables

{{AGENT}} = pi

## Related Skills

- **aven** owns task scope, dependencies, assignment, state, and durable handoff context. Use the Aven skill if available; otherwise, consult `aven skill`.
- **workmux** owns isolated branches, worktrees, agent processes, monitoring, and merge cleanup. Use the Workmux skill if available; otherwise, consult `workmux --help`. Workmux will reference **merge**, **rebase**, **worktree**, **coordinator**, **open-pr** skills.

## Workflow

1. **Prime the tools.**
   - Run `aven agent --help` before assignment.
   - Confirm that project is part of a git repository. Use `git init` if it doesn't.
   - Using `aven project`, ensure that an appropriately mapped project is available. Create one if neccessary.
   - For agent status tracking, ensure that Workmux hooks are installed.

2. **Build execution waves.**
   - Run `aven list --ready` and inspect each candidate with `aven context <task-ref>`.
   - Map task dependencies. Put independent tasks in the same wave. Put each dependent task in a later wave.
   - Ensure Workmux command includes option --agent {{AGENT}}
   - Give each task one Workmux handle and one stable, exact session ID, such as `workmux:<handle>`.
   - Assign ownership of all planned and discovered session tasks with `aven agent assign <task-ref> --session <session-id>`.
   - As the agent orchestrator, you should maintain task state. Do not delegate state maintenance.

3. **Dispatch one task per worktree.**
   - Create each worktree from the correct base branch with `workmux add`.
   - Give the agent the Aven task reference, its ownership boundary, and these completion requirements:
     1. Run `aven context <task-ref>`.
     2. Make only the requested change.
     3. Verify the acceptance criteria.
     4. Commit the complete change.
     5. Set the Aven task to `done` only after verification.
   - Start all tasks in the current wave before you wait for results.

4. **Monitor evidence, not only process state.**
   - Use `workmux status`, `workmux wait`, and `workmux capture` while an agent runs.
   - Use `workmux list`, `workmux path <handle>`, Git state, and `aven show <task-ref>` to confirm completion.
   - `No agent running` can mean that the agent exited. Inspect its branch and Aven task before you restart it.
   - If work is partial, reopen the existing worktree with a focused completion prompt. Preserve the agent's current changes.
   - If `aven agent assign` reports a server compatibility error, report degraded ownership tracking. Continue only when task status and durable notes can provide unambiguous ownership; do not claim that session assignment succeeded.

5. **Merge and unlock the next wave.**
   - Merge only a clean, committed branch whose task meets its acceptance criteria.
   - Use `workmux merge <handle> --into <base> --cleanup`.
   - After each wave, run `aven list --ready` again. Create dependent worktrees from the updated base so they contain all prerequisite changes.
   - Release stale Aven assignments when work is abandoned or reassigned.

## Completion gate

The orchestration is complete only when:

- every selected Aven task is `done` or has a documented blocker;
- every accepted branch is merged;
- dependent outputs were built from merged prerequisite work;
- tests and exact-output checks pass on the integration branch;
- the integration working tree is clean; and
- temporary Workmux worktrees and branches are removed.
