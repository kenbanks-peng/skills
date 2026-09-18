# Orchestrator workflow

The orchestrator owns board updates, including Ready and dependency reconciliation. A solo agent follows this workflow and executes work directly; delegated workers return results for the orchestrator to record.

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and open that board in Doska.

If settings are missing or unusable, read [project-board setup and recovery](project-board.md). If an existing board lacks Ready, add it between Backlog and WIP.

## 2. Find or create cards

Search the board for work matching the user's request. Reuse matching unfinished cards in Backlog, Ready, WIP, Review, or Blocked. Create untracked work in Backlog using the [card format](cards.md). For completed work, reopen the card if its original acceptance fails; otherwise create a linked follow-up.

Link prerequisites in each dependent card's Dependencies checklist. Reconcile dependencies before selecting work, after prerequisite changes or completion, and on session resume:

- Inspect affected dependent cards and verify each dependency against current evidence. Tick satisfied dependencies; untick any that are no longer satisfied.
- Move Backlog or Blocked cards to Ready only when all dependencies are satisfied, the work is clearly defined, falls within the user's request, and has no unresolved blockers.
- Reassess Ready cards when prerequisites change: return underspecified or out-of-scope work to Backlog; move blocked work to Blocked and record the prerequisite, resolver, and next check.

## 3. Execute and update

Choose a Ready card, record ownership and next action, and move it to WIP. Keep evidence and next action current; prefer one active card per executor.

For delegation, provide the worker a direct pointer to [worker instructions](worker.md), board/card IDs, scope, acceptance criteria, dependencies, file boundaries, and required verification. Evaluate the returned evidence, update the card, and reconcile affected dependencies before selecting more work.

For shared work, blockers, or session interruptions, read [coordination and recovery](execution.md).

## 4. Verify and finish

Record verification against every acceptance criterion and tick verified items. After required review and integration, set `Next: None — complete` and move to Done, retaining owner and evidence. Reconcile affected dependent cards.

For failed or unrun checks, pending approval, or cancellation, read [unfinished and cancelled work](execution.md#unfinished-and-cancelled-work).

## 5. Report the result

Report board/card references, delivered outcomes, and verification. Include remaining work or unsaved updates when present.
