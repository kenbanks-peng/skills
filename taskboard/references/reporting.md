# Checkpoints, blockers, and handoffs

Read at worker/reviewer entry or when recording checkpoints, blockers, or handoffs. Use the assigned channel; direct comments require verified append-only access. Coordinators preserve relayed identities/timestamps and refresh body evidence and Next.

Checkpoint material findings, decisions, verification, blockers, completion, and session end. Include timezone; omit tool transcripts. Record passed, failed, and not-run checks with gap reasons. Research/review evidence consists of sources, findings, and decisions.

## Execution checkpoint

```markdown
### <timestamp with timezone> — <worker identity> — <finding / decision / verification / blocker / completion>

- Changed: <significant result or decision and rationale>
- Evidence: <artifact/path; check and actual outcome, including failures or not-run reasons>
- Next: <concrete action and responsible identity>
- Parent action: <requested decision or transition, or none>
```

## Blocker

Report blockers immediately. The coordinator adds this section, updates Next, and moves the card to Blocked:

```markdown
## Blocker

- Since: <timestamp with timezone>
- Waiting for: <specific input, decision, failure resolution, or [[card]] result>
- Unblock owner: <identity responsible for resolving it>
- Attempted / evidence: <what is known>
- Next check or trigger: <date/event and who checks>
- Return to: <Ready / In Progress / Review>
```

On resolution, record a checkpoint and remove this section. Keep reminder dates here; native deadlines represent actual commitments.

## Session handoff / worker return

Publish through the checkpoint channel and notify the coordinator, who records the handoff and applies ownership/status changes. During outages, coordinators use [recovery](recovery.md); workers use their assigned fallback.

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
