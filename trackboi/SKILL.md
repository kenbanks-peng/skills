---
name: trackboi
description: Use for all work-item tracking for significant implementation, bug fixes, refactoring, research, reviews, planning, and multi-step project work, even when the user does not mention Trackboi. Only use checklists for tracking work inside a Trackboi work-item. 
---

# Trackboi

Trackboi is the default source of work-item status. Simple answers need no card. Follow explicit user instructions to skip tracking or use another system.

## Work cycle

1. Call `trackboi_orient_agent` and follow its guide. Use `trackboi_get_agent_guide` if the guide is absent. Confirm the project, worktree, board, and active agent before writes; consult tool schemas for operation details.
2. Before significant work, find and read the existing card and linked track, or create a card. Record the intended result and completion criteria, then move the card to the active-work state.
3. Keep status and scope current. Record meaningful progress, blockers, verification, and handoffs in card comments. Use separate cards or subtasks when work needs its own status, owner, or handoff. Session checklists track internal steps only; they do not replace cards.
4. Before the final response, record the result and verification. Mark the card complete only when its completion criteria are met. Otherwise, record the blocker or next action and leave the status accurate.

## Subagent work

- The main agent owns the parent card and final acceptance.
- Before subagent delegation, the main agent creates or reuses a linked card with scope and completion criteria. Retries use the same card.
- Each subagent owns and updates only its linked card, recording progress, verification, blockers, and completion.
- Subagents confirm Trackboi context before writes. If access fails, the main agent records their reports.
- The main agent verifies the combined result before closing the parent card.

## Safeguards

- Use MCP tools, not direct storage edits. Read existing records before changes.
- Resolve unclear targets before writes. Confirm unclear deletion scope or global settings changes. Change project or server configuration only when required by the task.
- If Trackboi is unavailable, report the tracking failure. Do not silently substitute a checklist or claim that records were saved.
