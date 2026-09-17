# Coordinator delegation

Coordinators read this before dispatching a worker or reviewer, and when handling failed or lost delegated work. Recipients follow [worker entry](worker.md), not this dispatch procedure. The coordinator owns card bodies, lifecycle, and final acceptance; workers and reviewers supply execution evidence.

## Dispatch

1. For a worker, create/link its child card under [decomposition](decomposition.md) and assign a locally chosen worker label. Record the returned runtime ID after dispatch so the label maps to the actual run. For a reviewer, record the reviewer assignment on the card under review. Record session-qualified identities; follow the coordinator’s ownership protocol before assignment.
2. Supply server/board/card opaque IDs, parent reference, bounded scope, acceptance/review criteria, dependencies, allowed files/worktree, and verification expectations. Make the delegated role explicit and direct the recipient to [worker entry](worker.md) rather than project setup. Supply relevant card content if the recipient cannot read Doska.
3. Establish the checkpoint channel below using verified live capabilities and worker access. Record it on the card and supply it in the assignment. Require material checkpoints during execution, not just a final report.
4. Require a return report using [reporting](reporting.md). Reconcile checkpoints, record the return, and route the card through the review and acceptance gates in [workflow](workflow.md).

**Ready to dispatch when:** ownership and scope are recorded, the recipient has the needed context, and there is a concrete checkpoint delivery/check-in mechanism.

## Checkpoint transport

Choose and record the channel before dispatch:

- **Append-only comments supported and accessible:** workers may append checkpoints directly to their assigned child card; reviewers may append decisions to the card under review. Verify this operation in the live API. Require notification of blockers, scope decisions, and readiness for review through the agreed reporting channel; comments do not imply notifications.
- **Only whole-body updates available, or recipient lacks board access:** recipients send checkpoints to the coordinator, which promptly records them on the card with the original identity and timestamp. Keep one body writer; separate Markdown sections do not make concurrent replacements safe.
- **No intermediate messaging available:** arrange coordinator-readable per-worker checkpoint files and a concrete polling/check-in point, or split delegation into bounded stages that return checkpoints. A final-response-only worker cannot promise live reporting.

Read new checkpoints at check-ins, update the body’s current evidence and Next summary, and apply justified lifecycle changes. Significant execution history stays on the child card, not solely in a final parent summary.

## Failure and return

A dispatched job is not completed work. On failure, cancellation, or lost contact, record actual state and preserve partial artifacts. Release or reassign ownership only after an explicit handoff establishes execution safety; silence or an old timestamp does not prove the prior worker stopped writing files.

Apply the workflow review and acceptance gates to successful returns. Record reviewer decisions and apply resulting transitions; workers and reviewers do not grant themselves final acceptance authority.
