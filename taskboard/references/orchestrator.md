# Orchestrator workflow

The orchestrator owns board updates, including Ready and dependency reconciliation. A solo agent follows this workflow and executes work directly; delegated workers return results for the orchestrator to record.

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and utilize that board in Doksa.

If settings are missing or unusable, read [project-board setup and recovery](project-board.md).

## 2. Identify the work

If the user requests you to perform work:

- by pulling, choose a Ready card within the authorized scope.
- by describing work, search the board for any existing tracked work (not in progress) tha aligns with the user's request and reuse the unfinished card, adjusting fields and column state as needed.

If the requested work is found to be untracked, create a new card using the [card format](cards.md). Set its initial column using the [reconciliation rules](#3-start-or-delegate-the-identified-work).

Update the Dependencies checklists of cards dependent on the new card.

## 3. Start or delegate the identified work

On session resume, reconcile relevant cards with actual work, including changes made outside the previous session.

Reconcile cards when created, before dispatch, and after results or prerequisite changes: verify current evidence, update dependency checkboxes, and assign the appropriate column:

- **Backlog:** needs clarification or scope authorization.
- **Blocked:** awaits a prerequisite or blocker resolution; follow step 4.
- **Ready:** outcome and acceptance criteria are clear, scope is authorized, dependencies are satisfied, and no blockers remain.

Dispatch only the identified work, and only when Ready; otherwise record what prevents it from starting. Resolve any existing ownership handoff, record the executor as owner, and move to WIP. Prefer one active card per executor.

The executor needs the board/card IDs, scope, acceptance criteria, dependencies, file boundaries, and required verification. For delegated work, also provide [worker instructions](worker.md).

## 4. Track progress and handle interruptions

Throughout execution, keep evidence and decisions current. Reread shared cards before replacing content and merge concurrent changes. Evaluate worker reports, update the cards, and apply the [reconciliation rules](#3-start-or-delegate-the-identified-work) to affected work before starting more work.

- **Blockers:** record the prerequisite and resolver, set the Handoff action to the concrete check or action needed to proceed using the [card format](cards.md), and move to Blocked until resolved.
- **Session interruptions:** record unfinished work and blockers, and set the Handoff action for the next agent or session. Resume with the reconciliation in step 3.
- **Doska unavailable:** report unsaved updates, leave a conversation handoff, and reconcile when access returns.

## 5. Verify and finish

Record verification against every acceptance criterion and tick verified items. After required review and integration, set `Handoff action: None — complete` and move to Done, retaining owner and evidence.

Reconcile affected work using the [reconciliation rules](#3-start-or-delegate-the-identified-work).

- **Failed or unrun checks:** record results and, when handing off, set the Handoff action; keep the card unfinished and unmet acceptance items unchecked.
- **Pending approval:** set the Handoff action to the required approval and use Review until approved.
- **Cancellation:** prefix the title with `Cancelled:`, record the reason and any replacement card, set `Handoff action: None — cancelled`, and move to Done. Leave unmet acceptance items unchecked.

## 6. Report the result

Report board/card references, delivered outcomes, and verification. Include remaining work or unsaved updates when present.
