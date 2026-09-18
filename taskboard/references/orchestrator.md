# Orchestrator workflow

The orchestrator owns board updates, including Ready and dependency reconciliation. A solo agent follows this workflow and executes work directly; delegated workers return results for the orchestrator to record.

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and open that board in Doska.

If settings are missing or unusable, read [project-board setup and recovery](project-board.md). If an existing board lacks Ready, add it between Backlog and WIP.

## 2. Find or create cards

Search the board for any tracked work matching the user's request. Reuse matching unfinished cards in Backlog, Ready, Review, or Blocked, adjusting column state as needed.

Create untracked work in Backlog using the [card format](cards.md).

Any cards dependent on the new card should have their Dependencies checklist updated.

## 3. Execute and update

Before selecting or delegating work, reconcile dependencies as described below, including on session resume. Choose a Ready card, read any Handoff action, record ownership, and move it to WIP. Keep evidence current; prefer one active card per executor. When blocking or handing off work, record the Handoff action using the [card format](cards.md).

For delegation, provide the worker a direct pointer to [worker instructions](worker.md), board/card IDs, scope, acceptance criteria, dependencies, file boundaries, and required verification. Evaluate the returned evidence, update the card, and reconcile affected dependencies before selecting more work.

For shared work, blockers, or session interruptions, read [coordination and recovery](execution.md).

## 4. Verify and finish

Record verification against every acceptance criterion and tick verified items. After required review and integration, set `Handoff action: None — complete` and move to Done, retaining owner and evidence.

After results or prerequisite changes, align affected cards' dependency checklists and columns with current evidence. Only clearly defined, in-scope work with satisfied dependencies and no blockers belongs in Ready; otherwise use Backlog or Blocked and record what needs resolving.

For failed or unrun checks, pending approval, or cancellation, read [unfinished and cancelled work](execution.md#unfinished-and-cancelled-work).

## 5. Report the result

Report board/card references, delivered outcomes, and verification. Include remaining work or unsaved updates when present.
