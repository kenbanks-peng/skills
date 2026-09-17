# Coordinator delegation

Read before dispatch or when handling failed/lost delegated work. Recipients follow [worker entry](worker.md).

## Dispatch

1. Create/link a worker’s child card under [decomposition](decomposition.md), then assign a session-qualified label using the coordinator’s ownership protocol. Map it to the runtime ID after dispatch. Assign reviewers on the card under review.
2. Supply server/board/card opaque IDs, parent reference, scope, acceptance/review criteria, dependencies, allowed files/worktree, and verification expectations. State the role and link worker entry. Supply card contents if the recipient lacks Doska access.
3. Establish and record a checkpoint channel below; include it and check-in points in the assignment.
4. Require a [return report](reporting.md). Reconcile checkpoints and returns through [workflow review and acceptance](workflow.md).

Dispatch only with recorded ownership, sufficient task context, and a working checkpoint channel.

## Checkpoint channel

- **Verified append-only comments and recipient access:** workers append to their child card; reviewers append to the reviewed card. Require separate notifications for blockers, scope decisions, and review readiness unless comment notifications are verified.
- **Whole-body updates only, or no recipient board access:** recipients report to the coordinator, who records checkpoints promptly with original identity and timestamp. Separate Markdown sections do not make concurrent replacements safe.
- **No intermediate messaging:** provide coordinator-readable per-worker checkpoint files with polling/check-in points, or dispatch bounded stages that return checkpoints. Do not promise live reports from a final-response-only worker.

At check-ins, read checkpoints, refresh evidence and Next, and apply justified transitions. Keep delegated execution history on the child card.

## Failure and return

On failure, cancellation, or lost contact, record state and preserve partial artifacts. Reassign only after an explicit handoff establishes that prior execution cannot conflict; silence or age does not prove file writes stopped.

Record reviewer decisions and apply workflow gates before acceptance. Dispatch and worker success alone do not complete a card.
