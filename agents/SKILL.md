---
name: agents
description: Orchestrate multiple coding agents with Aven tasks and Workmux worktrees. Use when work must be split across parallel or dependent agents, tracked through completion, merged safely, or delegated to avoid context limits in long-running agent sessions.
---

# Multi-agent orchestration

Use two authoritative skills:

- **Aven skill:** read [`../aven/SKILL.md`](../aven/SKILL.md), then run `aven skill`. Aven owns task scope, dependencies, assignment, state, and durable handoff context.
- **Workmux skill:** read [`../workmux/SKILL.md`](../workmux/SKILL.md). Workmux owns isolated branches, worktrees, agent processes, monitoring, and merge cleanup.

## Workflow

1. **Prime the tools.**
   - Run **`aven agent --help`** before assignment. This command is the source of truth for session assignment and release commands.
   - Confirm that the repository has a base commit.
   - Check the effective Workmux configuration. Use its configured `agent` and a pane with `command: <agent>`. Pass `--agent` only when an explicit override is required.
   - If agent status tracking is required, confirm that Workmux hooks are installed.

2. **Build execution waves.**
   - Run `aven list --ready` and inspect each candidate with `aven context <task-ref>`.
   - Map task dependencies. Put independent tasks in the same wave. Put each dependent task in a later wave.
   - Give each task one Workmux handle and one stable, exact session ID, such as `workmux:<handle>`.
   - Assign ownership with `aven agent assign <task-ref> --session <session-id>` and mark the task `active` when work starts.

3. **Dispatch one task per worktree.**
   - Create each worktree from the correct base branch with `workmux add`.
   - Let Workmux use its configured agent unless the plan requires a different agent.
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
