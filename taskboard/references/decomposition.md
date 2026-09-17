# Multi-card outcomes and dependencies

Coordinators read this before creating or coordinating a multi-card outcome, including resuming existing parent/child work. Use a checklist for steps sharing one owner, lifecycle, and acceptance decision; use a child card for separate ownership, parallel execution, independent review/deadlines, or independent blocking. Split outcomes that cannot be verified in a bounded work session; avoid activity-only cards such as “think about approach.”

A multi-card outcome gets a parent card with scope, overall acceptance, and a child index. Each child links back to the parent. State dependencies separately from hierarchy: belonging to the same parent does not imply an execution order.

- Parent index: `- [ ] [[12]] — API contract accepted`.
- Child relationship: `Parent: [[8]]`.
- Dependency: `Depends on: [[12]] — contract must be accepted before implementation`.
- Link cards by their board-local number in Markdown; retain opaque IDs in execution handoffs. Across boards, use a supported URL or explicit board/card identity rather than assuming `[[12]]` resolves globally.

Update parent checkboxes only when children are accepted. Children in Review, or merely reporting success, remain unchecked. A cancelled child requires an explicit parent scope decision.

Parents remain In Progress while the coordinator has actionable coordination work; otherwise use Blocked with the dependency and next trigger. Parent orchestration is exempt from the worker’s one-executable-card limit. A parent reaches Done only when all required children and overall integration/acceptance are complete; child completion alone is insufficient.

At accepted results, refresh affected parent indexes and dependent cards. Reread dependencies, clear resolved blockers, and return cards to their recorded columns; promote unassigned work to Ready when all entry gates hold.

## Parent template

Before creating or editing bodies, apply [card writing](card-writing.md), which also supplies the executable child template. Substitute actual references for the placeholder numbers below.

```markdown
<Overall outcome and value.>
Owner: <coordinator identity>
Next: <coordination or integration action>
-cut-
## Scope
<Included outcomes and explicit boundaries.>

## Acceptance

- [ ] <End-to-end outcome>
- [ ] <Overall integration and required review verified>

## Children

- [ ] [[12]] — <accepted deliverable>
- [ ] [[13]] — <accepted deliverable>

## Dependencies

<Execution order and external prerequisites; use card links where available.>

## Integration

- Target: <branch/environment/artifact>
- Reviewer: <identity>
- Evidence: <end-to-end checks and final artifacts>

## Decisions and handoffs

- <timestamp with timezone> — <decision or handoff>
```
