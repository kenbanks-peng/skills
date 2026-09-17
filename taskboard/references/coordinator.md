# Coordinator procedure

Read when starting/resuming tracked work or reconciling status as the coordinator. Own the overall outcome, card creation, scope, acceptance criteria, dependencies, assignments, transitions, integration, and final acceptance. Existing coordination agreements prevail.

## Start or resume

1. **Bind the project.** Read [binding](binding.md) on every start/resume. Use the specified board directly; follow its conditional pointers for missing/incomplete setup, binding changes, or recovery. This step ends with a verified binding or an explicit degraded tracking outcome.
2. **Load the working agreement.** Read board metadata and charter, then this work group’s cards, dependency closure, and latest relevant handoffs. Read [workflow](workflow.md) before claiming or transitioning work. If the charter or lifecycle mapping is missing/incomplete, follow [board setup](board-setup.md). Check for pending records; read [recovery](recovery.md) when any need reconciliation, and reconcile only the effective binding before selecting work. Reserve board-wide reconciliation for an explicit board status/audit request.
3. **Establish roles.** Execute work yourself or assign child cards to workers. Confirm existing ownership before taking over inherited work. Before dispatching a worker or reviewer, read [delegation](delegation.md) for assignment, checkpoint transport, and return handling.
4. **Make the request executable.** Search for the outcome across all statuses before creating a card. Exhaust relevant result pages, including archived work if supported; use summaries/search results before loading bodies. If the API lacks adequate search, page through card summaries. An incomplete lookup is not evidence of absence: resolve it or use [recovery](recovery.md) to record a local pending task rather than create a likely duplicate. Reuse an unfinished match; reopen accepted work only if its acceptance no longer holds, otherwise link a new follow-up. Infer bounded scope, observable acceptance, verification, and dependencies from the request and repository. Read [card writing](card-writing.md) before creating or editing a card body. A small, single-owner job needs one card, not an epic.
5. **Choose granularity.** Use a checklist for steps sharing one owner, lifecycle, and acceptance decision. Use child cards for separate ownership, parallel execution, independent review/deadlines, or independent blocking. Before creating or coordinating a multi-card outcome, read [decomposition](decomposition.md), including when resuming existing parent/child work.
6. **Start the work.** Set normal requested work to medium priority, order prerequisites first, promote scoped and unblocked work to Ready, then claim it under the ownership protocol below. Choose the next Ready card within the authorized outcome; ask only when a material scope decision cannot be inferred. Track meaningful deliverables, not every tool call.

**Ready to proceed:** the work has a durable card, clear ownership, acceptance criteria, and a next action—or a durable local record under the recovery rules. Remote-only tracking may proceed when local settings cannot be saved. If neither store is writable, leave a conversation-only blocked handoff and pause tracked execution until durable tracking is available. Report setup choices briefly and continue; routine defaults do not need an approval round.

## Ownership and writes

Exactly one accountable executor owns each executable card. Use a recognizable identity with a session/run discriminator, e.g. `agent:api/run-42`, `human:Ken`, or `unassigned`; use real runtime identifiers when available, otherwise record a locally chosen label as such.

Claim or assign work by rereading the card, confirming it is unassigned or explicitly released, recording the executor and next action, and moving it to In Progress. Reread to verify the result. This is a coordination protocol, not an atomic lock: if another session is active or ownership is disputed, agree a writer and assignment before proceeding. Never claim solely because a timestamp looks old.

The coordinator serializes body replacements and lifecycle updates for its work group, including parent/child bodies and acceptance checkboxes. This does not reserve authorship of execution evidence. Native assignment/locking is not assumed; these are coordination conventions. Workers and reviewers may append evidence only through their verified checkpoint channel; the coordinator applies resulting transitions.

Before any body replacement, reread and preserve human edits, task states, and attachment references. Keep shared board structure with its authorized writer. If competing writes are detected, stop and reconcile; reread/write is not compare-and-swap.

## Maintain and finish

Read [reporting](reporting.md) when recording checkpoints, blockers, or handoffs. Update at state transitions, material discoveries, blockers, dispatch/return, and session end—not after every tool call. Keep blocked/review cards owned so they cannot disappear between executors. Keep current evidence and Next visible; significant delegated execution history belongs on the child card.

At each checkpoint, workers report through their assigned channel; the coordinator reconciles:

1. Reconcile the active card with actual work and update acceptance/evidence.
2. Record newly discovered work as a linked card; distinguish required follow-up from optional improvements.
3. Refresh parent indexes and dependent cards affected by accepted results under [decomposition](decomposition.md). Reread dependencies, clear resolved blockers, and return cards to their recorded columns; promote unassigned work to Ready when all entry gates hold.
4. Leave a next action with a responsible identity, or a verified completion record.

Before Done, apply the acceptance gates in [workflow](workflow.md) and record completion using [card writing](card-writing.md). Preserve the finishing owner for attribution.

At session end or context handoff, use the [handoff template](reporting.md). Release unfinished work to Ready only when safe for another worker to claim; otherwise retain ownership or mark Blocked with the specific constraint. Report board/card references, delivered work, blockers, and next action to the user.

When resuming or asked for status, reconcile stale ownership, unresolved dependencies, review queues, parent/child mismatches, and upcoming deadlines within the requested work group and its dependency closure. Expand to the entire board only for an explicit board-wide status/audit request. Repair evidence-backed bookkeeping for this work group, arrange outstanding reviews, and record the next check for anything still blocked. Confirm release before reassigning old ownership. Report observed state, not inferred progress percentages. Destructive cleanup or board restructuring requires explicit agreement; a tracking session does not authorize implementing unrelated backlog items.
