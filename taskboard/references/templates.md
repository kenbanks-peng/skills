# Card templates

Fill placeholders from the request, repository, verified server state, and the skill’s Decision defaults; routine template choices are the agent’s responsibility. Omit irrelevant optional sections. Numbers below are placeholders: substitute actual card references. Use supported native priority/deadline fields separately. Owner and writer entries are working agreements in Markdown, not server-enforced fields. For offline records, use explicit local-only identifiers until reconciliation provides real card references. Record the effective project/server/board identity in every recovery record; temporary overrides must remain separate from the project default.

## Binding record for temporary overrides and recovery

Keep this header in the session handoff or durable pending record, not in unrelated default settings. Include it before task/handoff content for degraded tracking. An in-memory or conversation record alone does not count as durable persistence.

```markdown
## Tracking identity

- Binding: <project default / temporary override>
- Project: <canonical repository identity>
- Server: <verified connection identity, no secrets>
- Board: <name; opaque ID, or explicitly unknown>
- Charter: <opaque ID, or unknown>
- Setup state: <if initialization is authorized; otherwise not applicable>
- Initialization authority: <creation provenance or explicit authorization, if applicable>
- Local record: <session-qualified local-only ID, if applicable>
- Unsynchronized changes: <intended writes and uncertain operation results, or none>
```

## Board charter

```markdown
Tracking agreement for <project>.
Coordination: parent owns lifecycle and acceptance; workers report execution on child cards.
-cut-

## Scope

- Repository/project: <canonical URL or identity>
- Tracks: <outcomes included>
- Specs/plans: <links or repo-relative paths>

## Working agreement

- Workflow: <actual column-to-lifecycle mapping; Done is sole native done column for new boards>
- Ownership: one coordinator/card-body writer per work group; one executor per task; session-qualified identities
- Execution reporting: <verified append-only comments or coordinator-recorded checkpoints; reporting channel and check-in points>
- Shared structure writer: <bootstrap coordinator identity or existing authorized identity>
- Claims/handoffs: reread, confirm unassigned or explicitly released, write claim, reread to verify; card checkpoints carry releases and handoffs
- WIP: one executable card per worker
- Review: <concrete policy initialized from project requirements and the skill’s Decision defaults>
- Integration target: <current working tree/requested artifact unless project or user specifies another target>
- Verification: <authoritative instructions or discovered project commands; explicit check plan if none exists>
- Priority/deadlines: high urgent/critical-path unblocking, medium requested, low optional; deadlines only for established constraints

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

For a tiny standalone task, omit Relationships and optional execution fields. Keep the outcome, owner, next action, acceptance, and evidence. Checklists are acceptance gates or same-owner subtasks—not a second status system. Before entering Review, replace any reviewer policy placeholder with a named reviewer (the owner for permitted self-review), the required decision, and a next check.

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

## Execution checkpoint

Workers publish through the channel recorded on the card; the coordinator records relayed reports with their original attribution. Use comments only when the live API supports append-only writes. Otherwise the coordinator appends to the card’s Checkpoints section and summarizes current evidence and Next in the body.

```markdown
### <timestamp with timezone> — <worker identity> — <finding / decision / verification / blocker / completion>

- Changed: <significant result or decision and rationale>
- Evidence: <artifact/path; check and actual outcome, including failures or not-run reasons>
- Next: <concrete action and responsible identity>
- Parent action: <requested decision or transition, or none>
```

## Blocker section

The worker reports the blocker immediately through its checkpoint channel. The coordinator adds this section to the existing card, sets its preview’s Next action, and moves it to Blocked:

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

Publish through the card’s checkpoint channel and notify the coordinator of the return. The coordinator records relayed handoffs and applies ownership/status changes; the worker’s report alone does not change the card lifecycle. During a Doska outage, save it in the pending record specified by [board setup and recovery](board-setup.md), with known remote IDs and unsynchronized changes.

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
