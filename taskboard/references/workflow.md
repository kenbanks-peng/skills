# Workflow and policy

Read before claims, transitions, or charter initialization. Existing charter policy and stricter project requirements override these defaults.

## Decision defaults

- **Scope:** one board per repository across sessions, branches, and worktrees. Track the request and prerequisites; capture optional discoveries in Backlog.
- **Review:** self-review for low-risk, reversible work. Security, authentication/authorization, sensitive data, destructive migrations, and production-impacting changes require an independent reviewer. Dispatch a separate agent when available and permitted by project policy; otherwise name the required human and leave the card in Review. Existing stricter review requirements prevail.
- **Integration:** use the current working tree or requested artifact unless another target is specified. Keep required but unauthorized commits, merges, deployments, or publishing pending.
- **Verification:** follow project check instructions for the changed surface; use content/source checks for documentation and research. Record actual results; missing tooling is a gap, not a pass.
- **Escalation:** inspect configuration, repository, server, and handoffs first. Ask about unresolved scope, board references, ownership, access, consequential policy, or destructive/shared-workflow changes. Recommend a path; continue unaffected authorized work.

## Lifecycle

Columns carry status; card bodies carry context. Default columns, left to right:

| Column | Meaning and entry/exit rule |
| --- | --- |
| Backlog | Captured but not committed. Clarify scope, acceptance, dependencies, and priority before advancing. Also holds the explicitly labelled board charter. |
| Ready | Bounded, actionable, and unblocked; available to claim. Order top to bottom by intended execution order. |
| In Progress | An owner is actively executing. Default limit: one executable card per worker. |
| Blocked | Progress requires something outside the owner’s current work. Record the blocker, unblock owner, next check/trigger, and intended return column. |
| Review | Work and verification evidence are available; a named reviewer must decide acceptance. Record the next check and reviewer. |
| Done | Acceptance criteria are met, evidence is recorded, and required review/integration is complete. This is the board’s sole native done column. |

For existing boards, apply the charter’s mapping to these gates while preserving native done semantics and completion history. Ambiguous mappings or changes to shared workflow require the [board setup](board-setup.md) agreement path.

Normal flow: Backlog → Ready → In Progress → Review → Done. Blocked work returns to the recorded column once the dependency is resolved. Failed review returns to In Progress with specific remaining work. Reopened work gets a reason and a fresh next action.

Name the reviewer and next check before Review; record permitted self-review explicitly. Review status is not acceptance evidence. Reviewers report decisions and remaining work through their checkpoint channel; coordinators apply transitions.

**Cancellation:** retain the card with reason and any replacement link. Use a non-done Cancelled column; create it if permissions and charter allow. Cancellation satisfies no dependency without an explicit dependent-scope revision.

## Acceptance gate

Before Done, verify every acceptance item, required review, and agreed integration target. Exceptions require the responsible human’s scope approval. Branch tests do not prove merge/deployment. Use the [completion record](card-writing.md) and preserve the finishing owner.
