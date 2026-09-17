# Card writing

Coordinators read before body edits and completion records; use the [serialized write protocol](coordinator.md). Workers/reviewers use [reporting](reporting.md) instead.

## Format and fields

Bodies support GitHub-flavored Markdown plus Doska syntax:

| Syntax | Behavior |
| --- | --- |
| `- [ ]` / `- [x]` | Clickable tasks with a done/total count. Use a verified individual-checkbox operation when available; otherwise use the serialized body-update protocol. |
| `[[12]]` | Card link displaying the current title and column color. `[[12\|Fixed label]]` pins the label instead of following title changes. |
| `==highlight==` | Highlighted text. |
| Standalone `-cut-` line | Ends the board preview; the full body remains visible in the card view. |
| `![alt](attachment:<key>)` | Embeds an existing attachment. Preserve its key; uploads happen through the app. |

- **Title:** verb + outcome, e.g. `Reject expired invitation tokens`. Reserve prefixes for `[Board]` and `[Epic]`; omit status and owner.
- **Preview:** outcome, owner, and next action above a standalone `-cut-`; detailed context below it.
- **Acceptance:** observable outcomes as checkboxes; tick only with evidence. Counts measure neither effort nor completion.
- **Relationships:** prefer `[[12]]` so titles stay current; use ordinary Markdown links for specs, PRs, builds, and other artifacts. Card numbers are board-local; across boards use a supported URL or explicit board/card identity.
- **Evidence:** checks, actual results, and artifact/commit references. Use [reporting](reporting.md) for checkpoints, blockers, and handoffs.
- **Priority and deadline:** use supported native fields, not duplicated body metadata. Assign high to urgent/critical-path unblocking work, medium to normal requested work, and low to optional follow-up; reserve unset for untriaged captures. Leave deadlines empty unless the user or project establishes a real commitment or constraint.

Fill templates from the request, repository, verified server state, and [workflow defaults](workflow.md). Omit irrelevant sections. Owner/writer fields are conventions, not server enforcement. Label offline identifiers as local-only until reconciled.

For parents, read [decomposition](decomposition.md); for charters, read [board setup](board-setup.md).

## Executable task or child

```markdown
<Outcome.>
Owner: unassigned
Next: <one concrete action>
-cut-
## Scope
<Bounded deliverable; important exclusions.>

## Relationships

- Parent: <[[number]], or omit>
- Depends on: <[[number]] — required result, or “none”>
- Spec: <link/path, or omit>

## Acceptance

- [ ] <Observable outcome>
- [ ] <Required verification/review/integration outcome>

## Execution

- Coordinator / card-body writer: <identity>
- Checkpoint channel: <direct comments or coordinator-recorded reports; messaging/file channel and check-in points>
- Reviewer: <identity or agreed self-review policy>
- Run/worktree/branch: <when applicable>
- File boundary: <when delegated>

## Evidence

<Fill as work proceeds: artifact/commit; check performed; actual result.>

## Checkpoints

- <timestamp with timezone> — <material result/decision; next action>
```

Tiny tasks need only outcome, owner, Next, acceptance, and evidence. Checklists contain acceptance gates or same-owner subtasks, not duplicate statuses. Before Review, name the reviewer (owner for permitted self-review), required decision, and next check.

## Completion record

```markdown
### <timestamp with timezone> — accepted

- Delivered: <outcome and artifact reference>
- Verified: <acceptance evidence and check results>
- Review: <reviewer and decision, or explicit permitted self-review>
- Integration: <confirmed target/result, or not applicable>
- Follow-up: <linked non-blocking work, or none>
```

Record cancellation or supersession as a dated decision with a reason and replacement reference instead of using the completion template.
