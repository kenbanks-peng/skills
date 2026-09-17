# Worker or reviewer entry

Read when starting a delegated assignment. Follow this path instead of coordinator startup. Local settings and board setup are not prerequisites when the assignment is fully specified.

## Confirm and execute

1. Use the supplied server/board/card opaque IDs, parent reference, and bounded assignment. Confirm your executor/reviewer identity, allowed files/worktree, acceptance or review criteria, dependencies, verification expectations, and checkpoint channel. Read the assigned card and directly relevant dependencies, or use coordinator-supplied content when board access is unavailable. Resolve live tool capabilities before using Doska operations.
2. Resolve missing or conflicting assignment context with the coordinator before affected execution. Work within the supplied scope; the coordinator handles local settings, board/charter setup, unrelated work, card bodies, and lifecycle transitions.
3. Read [reporting](reporting.md) for checkpoint and return formats. Execute or review within the assignment. Report material findings, approach-changing decisions, artifacts, checks and outcomes, blockers, and next actions during the work—not just in a final response. Request scope, ownership, and lifecycle changes from the coordinator.
4. Return actual results, artifacts, checks and outcomes, blockers, and remaining work. State whether execution has stopped and whether processes or file writes remain active. Reporting completion does not accept the card.

**Ready when:** assigned scope, identity, dependencies, verification/review expectations, and reporting channel are confirmed. Ask the coordinator for missing essential context; pause only affected execution.

## Reporting authority

Use only the assigned, verified channel:

- With verified append-only comment access, workers may append checkpoints to their assigned child card; reviewers may append decisions to the card under review. Notify the coordinator of blockers, scope decisions, and readiness for review through the agreed reporting channel; comments do not imply notifications.
- Otherwise, send checkpoints to the coordinator for recording with original attribution and timestamps. Whole-body updates remain serialized by the coordinator; separate Markdown sections do not make concurrent replacements safe.
- If intermediate messaging is unavailable, use the coordinator-arranged checkpoint files/check-in points or bounded stages. Report a missing transport rather than promising live reporting.

On channel/access failure, notify the coordinator and retain evidence through the agreed fallback; do not initialize an independent tracking system. On failure, cancellation, or lost coordination, preserve partial artifacts and report execution-safety state. Explicit handoff is required before safe reassignment; silence or elapsed time does not prove execution stopped.

Reviewers record their acceptance decision and specific remaining work against the supplied criteria. Independent review must be distinct from execution when required. The coordinator owns final acceptance and applies transitions; neither a worker nor a reviewer transitions the card on its own authority.
