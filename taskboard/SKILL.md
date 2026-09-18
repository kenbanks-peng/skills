---
name: taskboard
description: Use when asked to perform work tasks associated with a project.
---

# Taskboard

Use Doska as the durable record of outcomes, ownership, next actions, and evidence. This skill establishes an opinionated workflow; the live MCP interface defines tool capabilities and usage.

## 1. Establish the project board

Read `board_id` from `.taskboard/settings.md` at the project root and open that board directly. Reuse it across sessions and leave valid settings unchanged. Follow existing column conventions; the state names below describe the workflow, not a requirement to rename columns.

If settings are missing or unusable, read [project-board setup and recovery](references/project-board.md) before proceeding. A delegated worker given a board/card assignment uses that reference directly instead of initializing another board.

## 2. Capture the requested outcomes

Before creating a card, look for relevant work on this board, including completed cards. Resolve incomplete lookups before treating an outcome as untracked.

Reuse matching unfinished work. Link a distinct follow-up to completed work; reopen a completed card only when its original acceptance no longer holds.

- Use **one card per independently finishable outcome**.
- Use a **Steps checklist** for implementation steps sharing that outcome and owner.
- Use **separate linked cards** for independent ownership, blocking, or acceptance. State each prerequisite result and confirm it is satisfied before starting dependent work.

Derive scope and acceptance from the request and project context; ask only about ambiguity that would change the work. Use the template below for new cards and preserve useful structure on existing ones. Store priority and deadlines in native fields. Deadlines reflect real constraints, not guesses.

Move a card to Ready once its outcome, acceptance criteria, and dependencies are clear and it is unblocked.

### Card template

**Title:** verb + observable outcome, such as `Reject expired invitation tokens`. Keep status and owner out of the title.

```markdown
## Outcome

<What must change and why. Include scope boundaries where needed.>

## Acceptance

- [ ] <Observable condition that must hold when finished>
- [ ] <Required verification outcome>

## Ownership and next action

- Owner: <responsible agent/person, or unassigned>
- Next: <one concrete action>

## References

<Relevant specification, code paths, related cards, or dependencies.
For each dependency, identify the prerequisite card and required result.
Omit this section when unnecessary.>

## Evidence

<Checks performed, actual results, and links to delivered artifacts.
Record failures and checks not run. Fill as work proceeds.>
```

Fill Outcome, Acceptance, and Ownership and next action before execution. Acceptance describes results, not activities: `Expired tokens are rejected`, rather than `Update validation`. Tick acceptance items only when supported by evidence. Add `## Steps` only when an implementation checklist helps; keep it separate from acceptance.

Keep cards proportional: a small task may need one sentence of outcome, one acceptance item, and one verification result. Keep status in columns, not a duplicate body field. Update the current next action in place while retaining material decisions and evidence; the card is a durable summary, not a transcript.

## 3. Execute and update

Choose an unblocked card within the requested scope. Read its current state and dependencies, resolve any existing owner's handoff, record the owner and next action, then move it to In Progress. Prefer one active card per executor. Agree ownership explicitly when multiple agents could take the same work.

Update at meaningful changes, not after every action:

- **Progress and decisions:** record evidence, material decisions, and the current next action. Preserve earlier findings that explain the work.
- **Shared edits:** reread before replacing card content. Preserve human edits, checklist state, attachment references, and unrelated fields.
- **Blockers:** record the prerequisite, who or what can resolve it, and when to check again. Move to Blocked if available; return to the appropriate state once unblocked.
- **Delegation:** provide the board/card IDs, scope, acceptance, file boundaries, and required verification. Have workers return evidence and remaining work; the delegating agent maintains the card and evaluates completion.

If Doska is unavailable, disclose which updates were not saved and leave a handoff in the conversation. Continue only independently safe, authorized work and reconcile the record when access returns. At session end, unfinished cards must identify progress, remaining work, blockers, and the next actor/action. On resume, reconcile those cards with actual work rather than auditing the whole board.

## 4. Verify and finish

Compare the delivered result with every acceptance criterion. Record actual checks and results, including failures and checks not run. Follow the project's review requirements.

Keep the card unfinished while required checks, review, or integration remain pending. Use Review when appropriate. Mark Done only when every acceptance criterion and required delivery step is satisfied, or the user explicitly revises the scope.

For completed cards, set `Next: None — complete`, retain the finishing owner and evidence, and remove stale handoff details. Mark the card complete using the board's established completion convention.

For cancellation, retain the card with its reason and any replacement link. Follow the board's convention without presenting the outcome as delivered.

Tracking grants no permission to commit, merge, deploy, publish, or execute unrelated backlog work.

## 5. Report the result

Report the board/card references, delivered outcomes, verification results, and any remaining work or unsaved updates. Claim a board update only after the tool confirms it succeeded.
