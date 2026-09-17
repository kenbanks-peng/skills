# Multi-card outcomes and dependencies

Read before creating or resuming multi-card work. Split by ownership, parallel execution, independent review/deadlines, or blocking. Split outcomes too large to verify in one bounded session; name deliverables, not activities.

Give each multi-card outcome a parent with scope, overall acceptance, and a child index; children link back. Record dependencies separately: hierarchy does not imply order.

- Parent index: `- [ ] [[12]] — API contract accepted`.
- Child relationship: `Parent: [[8]]`.
- Dependency: `Depends on: [[12]] — contract must be accepted before implementation`.
- Use board-local numbers in Markdown and opaque IDs in handoffs. Cross-board links require URLs or explicit board/card identities.

Tick parent checkboxes only for accepted children, not Review or reported success. Cancelling a child requires an explicit parent scope decision.

Keep parents In Progress while coordination is actionable; otherwise mark Blocked with dependency and next trigger. Parents are exempt from worker WIP limits. Done requires all required children plus overall integration and acceptance.

At accepted results, refresh affected parent indexes and dependent cards. Reread dependencies, clear resolved blockers, and return cards to their recorded columns; promote unassigned work to Ready when all entry gates hold.

## Parent template

Apply [card writing](card-writing.md) for body edits and child templates; replace example card numbers.

```markdown
<Overall outcome.>
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
