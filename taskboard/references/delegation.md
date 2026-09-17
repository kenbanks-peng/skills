# Delegation

Read before dispatching a worker/reviewer or starting a delegated assignment. Coordinators own card bodies, lifecycle, and acceptance; workers and reviewers supply execution evidence. This reference adds dispatch and reporting details to the main skill’s ownership rules.

## Worker or reviewer entry

1. Use the supplied server/board/card opaque IDs, parent reference, and bounded assignment. Confirm your executor/reviewer identity, allowed files/worktree, acceptance or review criteria, dependencies, and checkpoint channel. Read the assigned card and directly relevant dependencies, or use coordinator-supplied content when board access is unavailable.
2. Resolve missing or conflicting assignment context with the coordinator before affected execution. A worker does not bootstrap local settings, create a board, initialize a charter, claim unrelated work, or transition cards.
3. Execute or review within the assignment. Report material checkpoints using the agreed channel; request scope, ownership, and lifecycle changes from the coordinator.
4. Return actual results, artifacts, checks and outcomes, blockers, and remaining work. State whether execution has stopped and whether processes or file writes remain active. Reporting completion does not accept the card.

**Ready when:** the assigned scope, identity, dependencies, and reporting channel are confirmed. Missing local settings do not block a fully specified delegated assignment.

## Coordinator dispatch

Before dispatching a subagent:

1. Create/link its child card and assign a locally chosen worker label. Record the returned runtime ID after dispatch so the label maps to the actual run. For a reviewer, record the reviewer assignment on the card under review.
2. Supply server/board/card opaque IDs, parent reference, bounded scope, acceptance criteria, dependencies, allowed files/worktree, and verification expectations. Make the delegated role explicit so the recipient follows Worker or reviewer entry rather than project setup.
3. Establish the checkpoint channel below using verified live capabilities and worker access. Supply relevant card content if the recipient cannot read Doska. Require material checkpoints during execution, not just a final report.
4. Require a return report using the [handoff template](templates.md). Reconcile checkpoints, record the return, and route the card through acceptance.

**Ready to dispatch when:** ownership and scope are recorded, the recipient has the needed context, and there is a concrete checkpoint delivery/check-in mechanism.

## Checkpoint transport

Choose and record the channel before dispatch:

- **Append-only comments supported and accessible:** workers may append checkpoints directly to their assigned child card; reviewers may append decisions to the card under review. Verify this operation in the live API. Notify the coordinator of blockers, scope decisions, and readiness for review through the agreed reporting channel; comments do not imply notifications.
- **Only whole-body updates available, or recipient lacks board access:** recipients send checkpoints to the coordinator, which promptly records them on the card with the original identity and timestamp. Keep one body writer; separate Markdown sections do not make concurrent replacements safe.
- **No intermediate messaging available:** arrange coordinator-readable per-worker checkpoint files and a concrete polling/check-in point, or split delegation into bounded stages that return checkpoints. A final-response-only worker cannot promise live reporting.

Use the [execution checkpoint template](templates.md) at material findings, approach-changing decisions, verification milestones, blockers, and completion—not after every tool call. Each checkpoint states what changed, evidence, and the next action. The coordinator reads new checkpoints at check-ins, updates the body’s current evidence and Next summary, and applies justified lifecycle changes. Significant execution history stays on the child card, not solely in a final parent summary.

## Failure and return

A dispatched job is not completed work. On failure, cancellation, or lost contact, record the actual state and preserve partial artifacts. Release or reassign ownership only after an explicit handoff establishes execution safety; silence or an old timestamp does not prove the prior worker stopped writing files.

Apply the main skill’s review and acceptance gates to successful returns. The coordinator records reviewer decisions and applies resulting transitions; workers and reviewers do not grant themselves acceptance authority.
