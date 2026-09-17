# Card writing

Coordinators read this before creating or editing card bodies, including recording completion. Workers/reviewers use [reporting](reporting.md) through their assigned channel instead of replacing bodies. Follow the coordinator’s serialized read-preserve-write protocol for every replacement.

## Format and fields

Card bodies use GitHub-flavored Markdown: headings, lists, emphasis, code fences, tables, and ordinary `[label](url)` links. Doska adds:

| Syntax | Behavior |
| --- | --- |
| `- [ ]` / `- [x]` | Clickable tasks with a done/total count. Use a verified individual-checkbox operation when available; otherwise use the serialized body-update protocol. |
| `[[12]]` | Card link displaying the current title and column color. `[[12\|Fixed label]]` pins the label instead of following title changes. |
| `==highlight==` | Highlighted text. |
| Standalone `-cut-` line | Ends the board preview; the full body remains visible in the card view. |
| `![alt](attachment:<key>)` | Embeds an existing attachment. Preserve its key; uploads happen through the app. |

- **Title:** a short verb + outcome, e.g. `Reject expired invitation tokens`. Prefix only special cards: `[Board]`, `[Epic]`. Status and owner belong outside the title.
- **Preview:** outcome, owner, and next action above a standalone `-cut-`; detailed context below it.
- **Acceptance:** observable outcomes expressed as GFM task-list items. Tick only with evidence; task counts are not a measure of effort or proof of completion.
- **Relationships:** prefer `[[12]]` so titles stay current; use ordinary Markdown links for specs, PRs, builds, and other artifacts. Card numbers are board-local; across boards use a supported URL or explicit board/card identity.
- **Evidence and updates:** record what ran, its actual outcome, and an artifact/commit reference. Use [reporting](reporting.md) for dated checkpoints, blockers, and handoffs; keep the latest next action visible.
- **Priority and deadline:** use supported native fields, not duplicated body metadata. Assign high to urgent/critical-path unblocking work, medium to normal requested work, and low to optional follow-up; reserve unset for untriaged captures. Leave deadlines empty unless the user or project establishes a real commitment or constraint.

Fill templates from the request, repository, verified server state, and [workflow defaults](workflow.md); routine choices are the agent’s responsibility. Omit irrelevant optional sections. Owner/writer entries are working agreements in Markdown, not server-enforced fields. Use explicit local-only identifiers for offline records until reconciliation provides real references.

For parent cards, use [decomposition](decomposition.md). For charter creation or changes, follow [board setup](board-setup.md). These templates are conditional, not prerequisites for an ordinary task card.

## Executable task or child

```markdown
<One-sentence outcome and why it matters.>
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

For a tiny standalone task, omit Relationships and optional execution fields. Keep outcome, owner, next action, acceptance, and evidence. Checklists are acceptance gates or same-owner subtasks—not a second status system. Before entering Review, replace any reviewer policy placeholder with a named reviewer (the owner for permitted self-review), the required decision, and a next check.

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
