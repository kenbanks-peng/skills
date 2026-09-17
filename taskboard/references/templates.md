# Card templates

Replace placeholders and omit irrelevant optional sections. Numbers below are placeholders: substitute actual card references. Use native priority/deadline fields separately. The owner and writer entries are working agreements in Markdown, not server-enforced fields.

## Board charter

```markdown
Tracking agreement for <project>.
Coordinator: <identity> · Board writer: <identity>
-cut-
## Scope
- Repository/project: <canonical URL or identity>
- Tracks: <outcomes included>
- Specs/plans: <links or repo-relative paths>

## Working agreement
- Workflow: <column mapping, or “Doska skill defaults”>
- Ownership: <coordinator and writer scope; worker naming convention>
- Claims/handoffs: <coordination channel; how release is confirmed>
- WIP: one executable card per worker
- Review: <self-review allowed for which work; required reviewer otherwise>
- Integration target: <branch/environment/deliverable location>
- Verification: <authoritative instructions or project commands>
- Priority/deadlines: <project-specific policy, if any>

## Decisions
- <timestamp with timezone> — <policy decision and reason>
```

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
- Coordinator / board writer: <identity>
- Reviewer: <identity or agreed self-review policy>
- Run/worktree/branch: <when applicable>
- File boundary: <when delegated>

## Evidence
<Fill as work proceeds: artifact/commit; check performed; actual result.>

## Checkpoints
- <timestamp with timezone> — <material result/decision; next action>
```

For a tiny standalone task, omit Relationships and optional execution fields. Keep the outcome, owner, next action, acceptance, and evidence. Checklists are acceptance gates or same-owner subtasks—not a second status system.

## Parent outcome

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

## Blocker section

Add to the existing card, set its preview’s Next action, and move to Blocked:

```markdown
## Blocker
- Since: <timestamp with timezone>
- Waiting for: <specific input, decision, failure resolution, or [[card]] result>
- Unblock owner: <identity responsible for resolving it>
- Attempted / evidence: <what is known>
- Next check or trigger: <date/event and who checks>
- Return to: <Ready / In Progress / Review>
```

When resolved, fold the resolution into a checkpoint and remove the obsolete blocker section. If a date represents a follow-up reminder rather than the task’s actual deadline, keep it here instead of overwriting the native deadline.

## Session handoff / worker return

Append a concise checkpoint to the card; also send it to the coordinator when the worker is not the board writer.

```markdown
### <timestamp with timezone> — handoff
- From → to: <identity> → <identity or unassigned>
- State: <what actually finished; what remains>
- Artifacts: <paths, branch/worktree, commit/PR/build links>
- Verification: <checks and results; not-run checks with reasons>
- Blockers / risks: <specifics, or none>
- Next: <first executable action and responsible identity>
- Ownership: <retained / explicitly released / transferred and acknowledged>
- Execution safety: <worker stopped; outstanding processes; uncommitted work>
```

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
