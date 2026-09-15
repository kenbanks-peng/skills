---
name: kanban-lite
description: Use for all work-item tracking when involving significant implementation, bug fixes, refactoring, research, reviews, planning, and multi-step project work, even when the user does not mention kanban-lite.
---

# kanban-lite

kanban-lite is the default source of work-item status. Use the `kl` CLI. Simple answers need no card. Follow explicit user instructions to skip tracking or use another system.

## Initialization

If the task requires tracking, complete these steps before creating or changing cards. Simple answers do not require initialization.

1. Check for an existing workspace in the intended project directory. If none exists, run `kl init` in that directory.
2. Confirm the workspace with `kl pwd`. Use `--dir <path>` or `--config <path>` when needed, and keep the same target options on all commands.
3. List boards with `kl boards --json` and inspect the target board with `kl boards show <board-id> --json`. Use `--board <board-id>` to select the board explicitly.
4. Use `kl columns --board <board-id> --json` to find the board's status IDs.

## Work cycle

1. Before significant work, use `kl list --board <board-id> --json` to find an existing card. Read it with `kl show <id> --board <board-id> --json`, or create one with `kl add --title "..." --body "..." --board <board-id> --json`. Record the intended result and completion criteria in the card body. Move the card to the board's active-work status with `kl move <id> <status> --board <board-id>`. Use the board's actual status IDs.
2. Keep status and scope current. Record meaningful progress, blockers, verification, and handoffs with `kl comment add <id> --author "<agent-name>" --body "..." --board <board-id>`. Use separate cards when work needs its own status, owner, or handoff. Record related card IDs in their bodies. Use card checklists for internal steps; they do not replace cards.
3. Before the final response, add a comment with the result and verification. Move the card to the board's completed status only when its completion criteria are met. Otherwise, record the blocker or next action and leave the status accurate.

## Checklists

Use `kl checklist list <id> --board <board-id> --json` to read the checklist before changes. Use the current checklist token for `checklist add --expected-token <token>` and the item's current `modifiedAt` value for commands that require `--modified-at <iso>`. If a write fails because the data changed, read the checklist again and check the intended change before retrying.

## Subagent work

- Delegate only when the user instructs you to use subagents.
- The main agent owns the parent card and final acceptance.
- Before delegation, the main agent creates or reuses a separate card with scope, completion criteria, and the parent card ID. Record the child card ID on the parent card. Retries use the same card.
- Each subagent owns and updates only its assigned card, recording progress, verification, blockers, and completion.
- Subagents confirm the kanban-lite workspace and board before writes. If access fails, the main agent records their reports.
- The main agent verifies the combined result before closing the parent card.

## Safeguards

- Use `kl`, not direct storage edits. Read existing records before changes.
- Confirm the workspace and board before writes. Resolve unclear targets before writes. Confirm unclear deletion scope or global settings changes. Initialize a workspace or change board, storage, plugin, or server configuration only when required by the task.
- If `kl` is unavailable or an operation fails, report the tracking failure. Do not silently substitute a checklist or claim that records were saved.
