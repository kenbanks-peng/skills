# Workflow and policy

Coordinators read this before claiming or transitioning work; setup writers read it when initializing a charter. Apply existing charter policy and stricter project requirements; these are defaults, not authority to overwrite human decisions.

## Decision defaults

- **Scope:** one board per repository across sessions, branches, and worktrees. Track the requested outcome and its necessary prerequisites; capture optional discoveries in Backlog without implementing them.
- **Review:** self-review for low-risk, reversible work. Security, authentication/authorization, sensitive data, destructive migrations, and production-impacting changes require an independent reviewer. Dispatch a separate agent when available and permitted by project policy; otherwise name the required human and leave the card in Review. Existing stricter review requirements prevail.
- **Integration:** default to verified changes in the current working tree or the requested document/artifact. An explicit project or user target overrides this. Tracking does not authorize commits, merges, deployment, or publishing; when these are required but unavailable, retain the appropriate pending status.
- **Verification:** discover authoritative project instructions and test/build commands. Run checks appropriate to the changed surface and record actual outcomes; use explicit content/source checks for documentation and research. Missing tooling is a recorded verification gap, not a pass.
- **Escalation:** first inspect configuration, repository context, server state, and handoffs. Ask only for unresolved project scope, unusable board references, ownership conflicts, missing access, consequential policy/scope choices, or destructive/shared-workflow changes. Ask a focused question with a recommended path; continue independent authorized work when safe.

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

The coordinator arranges review rather than leaving an unnamed review queue. Record self-review explicitly; it may occur in the same session as implementation. Moving to Review does not claim that review happened. Reviewers record the decision and remaining work through the assigned checkpoint channel; the coordinator applies the resulting transition.

**Cancellation:** retain the card and record the reason plus a replacement link if relevant. Use a non-done Cancelled column, created when first needed if board permissions and charter permit it. Cancelled is not delivered and does not satisfy a dependency unless the dependent scope is explicitly revised. Preserve history rather than deleting cards.

## Acceptance gate

Before Done, verify every acceptance item, required review, and integration into the agreed target. Record exceptions only when the responsible human accepts the scope change; do not quietly redefine success. A passing branch test does not prove a merge or deployment occurred. Use the completion record in [card writing](card-writing.md); preserve the finishing owner for attribution.
