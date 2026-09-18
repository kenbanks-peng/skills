---
name: taskboard
description: Use when asked to perform work tasks associated with a project.
---

# Taskboard

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and open that board in Doska.

If settings are missing or unusable, read [project-board setup and recovery](references/project-board.md).

## 2. Capture the requested outcomes

Search the board, including completed cards, for matching work. Reuse unfinished cards; create missing outcomes using the [card format](references/cards.md). Move scoped, unblocked cards to Ready.

For completed matches or dependent outcomes, read [related work](references/cards.md#related-work).

## 3. Execute and update

Choose an unblocked card within scope, record ownership and next action, and move to In Progress. Keep evidence and next action current; prefer one active card per executor.

For shared work, delegation, blockers, or session interruptions, read [coordination and recovery](references/execution.md).

## 4. Verify and finish

Record verification against every acceptance criterion and tick verified items. After required review and integration, set `Next: None — complete` and move to Done, retaining owner and evidence.

For failed or unrun checks, pending approval, or cancellation, read [unfinished and cancelled work](references/execution.md#unfinished-and-cancelled-work).

## 5. Report the result

Report board/card references, delivered outcomes, and verification. Include remaining work or unsaved updates when present.
