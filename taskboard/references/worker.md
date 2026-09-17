# Worker or reviewer entry

Follow the supplied assignment, not coordinator startup; local settings and board setup are unnecessary.

## Confirm and execute

1. Confirm supplied server/board/card IDs, parent, executor/reviewer identity, scope, allowed files/worktree, criteria, dependencies, verification, and checkpoint channel. Read the card and relevant dependencies, or use coordinator-supplied content without board access. Resolve live capabilities before Doska calls.
2. Ask the coordinator to resolve missing/conflicting context; pause only affected execution. Leave settings, charter, card bodies, and lifecycle transitions to the coordinator.
3. Read [reporting](reporting.md). Execute within scope and report material findings, decisions, artifacts, checks, blockers, and next actions during work. Request scope/ownership/status changes from the coordinator.
4. Return results and remaining work using the handoff template. State whether execution stopped and whether processes or file writes remain active.

## Reporting authority

- **Assigned append-only comments:** workers report on their child card; reviewers on the reviewed card. Notify the coordinator of blockers, scope decisions, and review readiness; comments alone do not guarantee notification.
- **Coordinator-recorded reports:** send checkpoints with identity and timestamp. Do not replace bodies; separate sections cannot prevent lost updates.
- **No intermediate messaging:** use arranged checkpoint files/check-ins or bounded stages. Report missing transport rather than promise live updates.

On access/channel failure, notify the coordinator and retain evidence through the assigned fallback; do not start independent tracking. On failure, cancellation, or lost coordination, preserve artifacts and report execution safety. Reassignment requires explicit handoff, not assumed release after silence.

Review against supplied criteria and report the decision plus remaining work. Required independent review must be separate from execution. The coordinator grants final acceptance and applies transitions.
