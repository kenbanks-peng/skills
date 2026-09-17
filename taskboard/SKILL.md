---
name: taskboard
description: Use when asked to perform work that will alter a software codebase.
---

# Taskboard

Use Doska as the durable record of outcomes, ownership, and progress. Discover tool arguments and capabilities from the live MCP server; this skill defines the workflow, not the API.

Supporting links resolve relative to this skill. Read the linked instructions when their stated condition applies.

## 1. Establish the project board

Read `.taskboard/settings.md` at the project root, retrieve `board_id` (and `server` if present), and open that board directly. Reuse it across sessions, leave unchanged settings alone, and follow the board's existing conventions.

If the file is missing or its reference cannot be used, read [project-board setup and recovery](references/project-board.md) before proceeding.

## 2. Capture the requested outcomes

Look for relevant cards on this board before creating new ones, including completed work and additional result pages where relevant. Reuse unfinished matches.

- Use **one card per independently finishable outcome**.
- Use a **Steps checklist** for implementation steps sharing that outcome and owner.
- Use **separate linked cards** for independent ownership, blocking, or acceptance. State dependencies explicitly.

Write cards using the template below. Derive scope and acceptance from the request and project context; ask only about material ambiguity. Use native priority and deadline fields when needed; deadlines reflect real constraints, not guesses.

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

Choose an unblocked card within the requested scope. Confirm it is available, record its owner and next action, then move it to In Progress. Prefer one active card per executor.

Update the card on meaningful changes: decisions, progress, and verification results. Before replacing a body, reread it and preserve human edits, checklist state, and attachment references.

## 4. Verify and finish

Compare the delivered result with every acceptance criterion. Record actual checks and results, including failures and checks not run. Follow the project's review requirements.

Mark Done only when the agreed outcome, required verification, review, and integration are complete.

For completed cards, set `Next: None — complete`, retain the finishing owner and evidence, and remove stale handoff information.

Tracking grants no permission to commit, merge, deploy, publish, or execute unrelated backlog work.

## 5. Report the result

Report the board/card references and delivered outcomes to the user.
