# Coordination and recovery

## Shared work

Resolve the current owner's handoff before taking ownership. Reread shared cards before replacing content and merge concurrent changes. Record decisions with progress updates.

## Blockers

Record the prerequisite and resolver, and set the Handoff action to the concrete check or action needed to proceed. Move to Blocked until resolved.

## Session interruptions

At session end, record unfinished work and blockers, and set the Handoff action for the next agent or session. On resume, reconcile relevant cards with actual work, including the [dependency and readiness checks](orchestrator.md#2-find-or-create-cards).

If Doska is unavailable, report unsaved updates, leave a conversation handoff, and reconcile when access returns.

## Unfinished and cancelled work

- **Failed or unrun checks:** record results and, when handing off, set the Handoff action; keep the card unfinished and unmet acceptance items unchecked.
- **Pending approval:** set the Handoff action to the required approval and use Review until approved.
- **Cancellation:** prefix the title with `Cancelled:`, record the reason and any replacement card, set `Handoff action: None — cancelled`, and move to Done. Leave unmet acceptance items unchecked.
