# Orchestrator workflow

The orchestrator owns board updates, including Ready and dependency reconciliation. A solo agent follows this workflow and executes work directly; delegated workers return results for the orchestrator to record.

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and utilize that board in Doksa.

If settings are missing or unusable, read [project-board setup and recovery](project-board.md).

## 2. Identify the work

If the user specifies a card, open it directly. Otherwise, search the board for tracked work matching the user's request. Reuse matching unfinished cards, adjusting column state as needed.

Failing reuse, create new untracked work using the [card format](cards.md). Set its initial column using the [readiness and dependency rules](#readiness-and-dependencies).

Update the Dependencies checklists of cards dependent on the new card.

When the user asks you to pick up available work instead, choose a Ready card within the authorized scope.

## 3. Start or delegate the identified work

Before starting or delegating the identified work, reconcile its dependencies and readiness against current evidence. On session resume, also reconcile relevant cards with actual work, including changes made outside the previous session.

### Readiness and dependencies

Use these states when creating cards and when reconciling existing work:

- **Ready:** clearly defined outcome and acceptance criteria, authorized scope, satisfied dependencies, and no blockers.
- **Backlog:** work needing clarification or scope authorization.
- **Blocked:** work waiting on a prerequisite or other blocker; record the prerequisite, resolver, and Handoff action as described in step 4.

After results or prerequisite changes, verify evidence, tick or untick affected dependency items, and update affected cards' columns accordingly.

Start the identified work only when ready. If it is blocked, record what prevents it from starting rather than substituting unrelated Ready work. Read any Handoff action and resolve the current owner's handoff before taking ownership. Record the executor as owner and move the card to WIP; prefer one active card per executor.

Execute directly or delegate. For delegation, provide the worker a direct pointer to [worker instructions](worker.md), board/card IDs, scope, acceptance criteria, dependencies, file boundaries, and required verification. Workers execute assigned scope and return results to the orchestrator.

## 4. Track progress and handle interruptions

Throughout execution, keep evidence and decisions current. Reread shared cards before replacing content and merge concurrent changes. Evaluate worker reports, update the cards, and apply the [readiness and dependency rules](#readiness-and-dependencies) to affected work before starting more work.

- **Blockers:** record the prerequisite and resolver, set the Handoff action to the concrete check or action needed to proceed using the [card format](cards.md), and move to Blocked until resolved.
- **Session interruptions:** record unfinished work and blockers, and set the Handoff action for the next agent or session. Resume with the reconciliation in step 3.
- **Doska unavailable:** report unsaved updates, leave a conversation handoff, and reconcile when access returns.

## 5. Verify and finish

Record verification against every acceptance criterion and tick verified items. After required review and integration, set `Handoff action: None — complete` and move to Done, retaining owner and evidence.

Reconcile affected work using the [readiness and dependency rules](#readiness-and-dependencies).

- **Failed or unrun checks:** record results and, when handing off, set the Handoff action; keep the card unfinished and unmet acceptance items unchecked.
- **Pending approval:** set the Handoff action to the required approval and use Review until approved.
- **Cancellation:** prefix the title with `Cancelled:`, record the reason and any replacement card, set `Handoff action: None — cancelled`, and move to Done. Leave unmet acceptance items unchecked.

## 6. Report the result

Report board/card references, delivered outcomes, and verification. Include remaining work or unsaved updates when present.
