# Alternate workflow paths

Read the applicable section when a condition in `SKILL.md` routes here. These instructions supplement the normal workflow; they do not authorize additional work.

## Lookup incomplete or completed match found

Resolve incomplete lookup, including additional result pages where relevant, before assuming a card is absent. If completed work needs a distinct follow-up, link a new card; reopen only when its original acceptance no longer holds.

## Optional discoveries

Capture optional discoveries in Backlog without expanding the authorized assignment. Link non-blocking follow-up work from the relevant card.

## Ownership conflict or shared-card writes

Resolve an existing owner's handoff before taking over. Coordinate shared-card writes; rereading before replacement is not a lock. Preserve human edits, checklist state, and attachment references.

## External blocker

Move externally blocked work to Blocked. Add or update this section in the card:

```markdown
## Handoff

- Progress: <what is finished>
- Remaining: <work still required>
- Blocker: <what prevents progress, or none>
- Unblock: <required action and responsible person or dependency, or not applicable>
- Check again: <when to revisit an external blocker, or not applicable>
- Next actor: <who acts next>
```

Keep Ownership and next action current. Return the card to the appropriate active state when the blocker is resolved. Continue other authorized work where possible.

## Delegation

The delegating agent supplies the board/card reference, scope, acceptance criteria, file boundaries, and expected verification. Delegated workers use their supplied board and card and skip project setup, even when their checkout lacks settings.

Workers return results, evidence, blockers, and remaining work to the delegating agent, who updates the cards and decides completion. Delegation alone does not satisfy acceptance.

## Doska unavailable

Report unsaved updates explicitly and leave a conversation handoff with the board/card references, progress, remaining work, blockers, and next actor. Continue only work that does not require an unresolved assignment or board decision. Reconcile unsaved progress when access returns; never claim an update was saved without confirmation.

## Review pending or acceptance unmet

Use Review while a required decision is pending, naming the reviewer and next action. Address requested changes before completion.

If an acceptance, verification, review, or integration requirement remains unmet, leave the card unfinished with a concrete next action, or obtain the user's explicit scope change. Implementation finished is not necessarily task complete. Record failed checks and checks not run as evidence.

## Cancelled or superseded work

Record the reason and replacement, if any, without presenting the work as successfully completed.

## Unfinished session or ownership handoff

Before stopping, ensure every unfinished card touched in this session has a current Handoff using the fields under [External blocker](#external-blocker). Update the summary in place while retaining material decisions and evidence. Release ownership explicitly when handing work to another executor.

Report outstanding blockers and the next action to the user along with board/card references and delivered outcomes.

## Resume

Read the relevant cards and dependencies, compare their handoffs with the actual work, and reconcile differences before continuing. Stay within the requested work rather than auditing the entire board.
