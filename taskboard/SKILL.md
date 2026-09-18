---
name: taskboard
description: Use when asked to perform work tasks associated with a project.
---

# Taskboard

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and open that board in Doska.

If settings are missing or unusable, read [project-board setup and recovery](references/project-board.md).

## 2. Capture the requested outcomes

Search the board, including completed cards, for matching work. Reuse unfinished cards. Link new follow-ups to completed work; reopen a card when its original acceptance no longer holds.

- Use one card per independently finishable outcome.
- Use a `## Steps` checklist for implementation steps sharing an outcome and owner.
- Use linked cards for independent ownership, blocking, or acceptance. Identify each prerequisite result.

Store priority and deadlines in native fields. Move scoped, unblocked cards to Ready.

### Card template

**Title:** verb + observable outcome, such as `Reject expired invitation tokens`.

```markdown
## Outcome

<What must change and why; scope boundaries.>

## Acceptance

- [ ] <Observable result>
- [ ] <Required verification>

## Ownership and next action

- Owner: <agent/person, or unassigned>
- Next: <concrete action>

## References

<Specifications, code, and related cards. Omit when unnecessary.>

## Evidence

<Checks, results, and delivered artifacts.>
```

Fill Outcome, Acceptance, and Ownership and next action before execution.

## 3. Execute and update

Choose an unblocked card within scope. Confirm prerequisites, resolve the current owner's handoff, record ownership and next action, and move to In Progress. Prefer one active card per executor.

Update cards at meaningful changes:

- **Progress:** record evidence, decisions, and the current next action.
- **Shared edits:** reread before replacing content and merge concurrent changes.
- **Blockers:** record the prerequisite, resolver, and next check. Move to Blocked until resolved.

### Delegation

Provide board/card IDs, scope, acceptance, file boundaries, and verification. Workers return evidence and remaining work; the delegating agent updates the card and evaluates completion.

### Interruptions and handoff

If Doska is unavailable, report unsaved updates, leave a conversation handoff, and reconcile when access returns.

At session end, record unfinished work, blockers, and the next actor/action. On resume, reconcile relevant cards with actual work.

## 4. Verify and finish

Record verification against every acceptance criterion, including failed or unrun checks. Tick acceptance items when verified. Complete required review and integration before marking Done; use Review while awaiting approval.

For completed cards, set `Next: None — complete` and retain owner and evidence. For cancellations, prefix the title with `Cancelled:`, record the reason and any replacement card, set `Next: None — cancelled`, and move to Done. Leave unmet acceptance items unchecked.

## 5. Report the result

Report board/card references, delivered outcomes, verification, remaining work, and unsaved updates.
