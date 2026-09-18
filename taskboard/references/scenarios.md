# Regression scenarios

For skill maintenance only. Walk these cases against `SKILL.md` and the supporting instructions reached through its conditional links; for behavioral tests, use stubbed MCP/filesystem responses or a disposable workspace rather than real project boards. Record pass/fail and divergences. Label document walkthroughs as static checks, not executed agent tests.

## Board binding

1. **First use:** no settings and no known shared reference. Create a project-named board, immediately save its returned ID in `.taskboard/settings.md`, and establish the default workflow. Do not list boards or adopt a name match.
2. **Later session:** valid settings. Open the referenced board directly, preserve existing conventions, and leave settings unchanged. Do not create a board or require a charter.
3. **Unavailable or malformed reference:** preserve existing data and report or resolve the problem. Do not silently create a replacement.
4. **Uncertain creation:** a create call loses its response. Recover the reference or request the board reference/confirmation of failure; do not blindly retry.
5. **Failed local save:** creation returns an ID but settings cannot be written. Report the ID and save failure; do not recreate the board.
6. **Multiple agents/checkouts:** share the existing reference and agree one initializer where initialization is needed. Delegated workers with assignments skip setup even when their checkout lacks settings.

## Cards and execution

7. **Small task:** use one card with outcome, observable acceptance, owner, and next action. Add evidence as work proceeds; omit irrelevant sections.
8. **Independent work:** split independently owned, blocked, or accepted outcomes into linked cards with explicit dependencies. Keep same-outcome implementation steps in a Steps checklist rather than confusing them with acceptance.
9. **Existing work:** look for relevant work on the bound board, including completed cards, and resolve incomplete lookups. Reuse matching unfinished cards. Link a distinct follow-up to completed work; reopen only if original acceptance no longer holds. Incomplete lookup is not proof of absence.
10. **Ownership and human edits:** resolve an existing owner's handoff before taking over. Reread before body replacement and preserve human decisions, checkbox state, and attachment references. Coordinate competing writes without claiming atomicity.
11. **Blocker:** record what is blocking, who or what unblocks it, and when to check. Move to Blocked; return to the appropriate active state after resolution.
12. **Delegation:** supply board/card reference, scope, acceptance, file boundaries, and verification. The worker reports evidence and remaining work; the delegating agent updates the card and evaluates completion.
13. **Doska outage:** disclose unsaved updates and leave a conversation handoff. Continue only independently safe, authorized work; reconcile when access returns. Do not claim persistence succeeded.

## Completion and resume

14. **Successful delivery:** record evidence for every acceptance criterion and satisfy required review/integration before Done. Retain owner and evidence, set Next to complete, and remove stale handoff details.
15. **Incomplete delivery:** failed checks, missing required review, or pending required integration keep the card unfinished with a next action unless the user explicitly changes scope. Do not commit, merge, or deploy solely to satisfy tracking.
16. **Cancellation:** retain a reason and any replacement reference without representing the outcome as successfully completed.
17. **Session end and resume:** unfinished cards identify progress, remaining work, blockers, and next actor. Resume by comparing relevant cards and dependencies with actual work, without a board-wide audit.

## Document integrity

18. Validate frontmatter, local Markdown links and anchors, and the presence of the board-binding rule and inline card template. Ordinary execution with valid settings must require only `SKILL.md`, not these maintainer scenarios or conditional references.
19. **Conditional routing:** missing or unusable settings route to `project-board.md` before setup or recovery.

20. **Workflow boundary:** instructions establish scope, ownership, state transitions, evidence, and handoff policy. Tool capabilities, argument formats, and operation mechanics remain in the live MCP interface rather than being duplicated here.
