# Coordinator procedure

Own scope, cards, assignments, dependencies, integration, and acceptance. Honor existing coordination agreements.

## Start or resume

1. Read [binding](binding.md) and verify the effective board, or establish a recovery outcome.
2. Load the charter, requested work group, its dependencies, and relevant handoffs. Read [workflow](workflow.md) before claims or transitions. Missing charter/lifecycle policy requires [board setup](board-setup.md). Reconcile pending records for this binding through [recovery](recovery.md) before selecting work. Inspect unrelated cards only for an explicit board-wide audit.
3. Confirm ownership of inherited work. Execute it yourself or read [delegation](delegation.md) before dispatching workers or reviewers.
4. Search all statuses and supported archives for the requested outcome before creating a card. Exhaust relevant pages; load summaries before bodies. If search is inadequate, page through summaries. If lookup remains incomplete, save a pending task through recovery rather than risk duplication. Reuse unfinished matches; reopen accepted work only when its acceptance no longer holds, otherwise link a follow-up. Derive scope, acceptance, verification, and dependencies from the request and repository. Read [card writing](card-writing.md) before body edits.
5. Use a checklist for steps sharing an owner, lifecycle, and acceptance decision. For separate ownership, parallel execution, independent review/deadlines, or independent blocking, read [decomposition](decomposition.md). Also read it when resuming multi-card work.
6. Assign medium priority to normal requested work, order prerequisites first, and move scoped, unblocked work to Ready. Claim the next card within the authorized outcome using the protocol below. Ask only for material scope decisions that cannot be inferred.

Proceed once a durable card or recovery record has an owner, acceptance criteria, and next action. Remote-only tracking may proceed if settings cannot be saved. If neither store is writable, leave a conversation-only blocked handoff and pause tracked execution. Report setup choices briefly; routine defaults need no approval.

## Ownership and writes

Each executable card has one accountable executor. Use session-qualified identities such as `agent:api/run-42`, `human:Ken`, or `unassigned`. Prefer runtime IDs; identify locally chosen labels as such.

To claim or assign: reread the card, confirm it is unassigned or explicitly released, record executor and next action, move to In Progress, and reread to verify. This is not an atomic lock. Resolve active or disputed ownership before proceeding; age alone does not release a claim.

Serialize body replacements, lifecycle updates, and parent/child acceptance checkboxes within the work group. Workers and reviewers submit evidence through their checkpoint channels. Native assignment or locking is not assumed.

Before replacement, reread and preserve human edits, task states, and attachment references. Shared board structure remains with its authorized writer. Stop and reconcile competing writes; reread/write is not compare-and-swap.

## Maintain and finish

Read [reporting](reporting.md) for checkpoints, blockers, and handoffs. Update on transitions, material discoveries, blockers, dispatch/return, and session end. Retain owners on Blocked and Review cards; keep evidence and Next current.

At each checkpoint:

1. Reconcile the card’s acceptance and evidence with actual work.
2. Link newly discovered work; distinguish required follow-up from optional improvements.
3. Refresh affected parents and dependents under [decomposition](decomposition.md).
4. Record a next action and responsible identity, or verified completion.

Before Done, apply [workflow acceptance gates](workflow.md) and the [completion record](card-writing.md). Preserve the finishing owner.

At session end, publish a [handoff](reporting.md). Release unfinished work to Ready only when another worker can safely claim it; otherwise retain ownership or record the blocking constraint. Report board/card references, delivered work, blockers, and next action to the user.

On resume or status requests, reconcile ownership, unresolved dependencies, review queues, parent/child mismatches, and deadlines within the requested work group and its dependencies. Repair evidence-backed bookkeeping, arrange reviews, and schedule blocked-work checks. Confirm release before reassignment. Report observed state, not progress percentages. Board-wide audits and destructive restructuring require explicit requests.
