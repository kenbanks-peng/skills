# Checkpoints, blockers, and handoffs

Read when a worker/reviewer starts an assignment, or when a coordinator records a checkpoint, blocker, or handoff. Publish through the assigned channel. Coordinators record relayed reports with original identity and timestamp and maintain current evidence and Next in the card body. Use direct comments only when append-only writes are verified and assigned.

Record dated, concise checkpoints with an explicit timezone at material findings, approach-changing decisions, verification milestones, blockers, completion, and session end—not after every tool call. Retain consequential decisions and handoffs rather than a tool transcript. Report passed, failed, and not-run checks with reasons for gaps; research/review evidence is sources, findings, or disposition rather than fictional test runs.

## Execution checkpoint

```markdown
### <timestamp with timezone> — <worker identity> — <finding / decision / verification / blocker / completion>

- Changed: <significant result or decision and rationale>
- Evidence: <artifact/path; check and actual outcome, including failures or not-run reasons>
- Next: <concrete action and responsible identity>
- Parent action: <requested decision or transition, or none>
```

## Blocker

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

When resolved, the coordinator folds the resolution into a checkpoint and removes the obsolete blocker section. If a date represents a follow-up reminder rather than the task’s actual deadline, keep it here instead of overwriting the native deadline.

## Session handoff / worker return

Publish through the card’s checkpoint channel and notify the coordinator of the return. The coordinator records relayed handoffs and applies ownership/status changes; the worker’s report alone does not change the card lifecycle. During a Doska outage, coordinators follow [recovery](recovery.md) to save pending records with known remote IDs and unsynchronized changes; workers use their assigned fallback and report to the coordinator.

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
