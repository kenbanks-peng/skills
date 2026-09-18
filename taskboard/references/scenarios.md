# Regression scenarios

Walk these cases against the skill and its linked references. For behavioral tests, use stubbed responses or a disposable workspace. Record results as static checks or executed agent tests.

## Board binding

1. **First use:** with settings missing, create a project-named board even if another shared board reference is available, save its returned ID, and establish the skill-defined workflow.
2. **Later session:** open the saved board directly; column setup is already complete.
3. **Malformed reference:** recover the board ID from this workflow's prior initialization or ask the user.
4. **Unavailable board:** report the problem and request approval for replacement.
5. **Uncertain creation:** recover the ID or confirm failure before retrying.
6. **Failed settings save:** report the ID and error; resume by saving the ID.
7. **Column setup:** reuse suitable default columns to establish the workflow and designate Done as the completion column.

## Cards and execution

8. **Small task:** one card with outcome, acceptance, owner, next action, and evidence.
9. **Independent work:** linked cards for independent ownership, blocking, or acceptance; Steps checklist for shared-outcome implementation.
10. **Existing work:** search unfinished and completed cards. Reuse unfinished work, link follow-ups, and reopen when original acceptance fails.
11. **Shared work:** resolve ownership handoffs and merge concurrent card edits.
12. **Blocker:** record prerequisite, resolver, and next check; use Blocked until resolved.
13. **Delegation:** provide references, scope, acceptance, file boundaries, and verification. Workers return evidence and remaining work. The delegating agent evaluates returned evidence and updates the card.
14. **Doska outage:** report unsaved updates, leave a conversation handoff, and reconcile when access returns.

15. **Session end/resume:** record unfinished work, blockers, and the next actor/action; reconcile relevant cards with actual work on resume.

## Verification and completion

16. **Delivery:** record verification for every acceptance criterion, tick verified items, and complete required review/integration before Done. Retain owner and evidence; set Next to complete.
17. **Incomplete delivery:** record failed or unrun checks and the next action; keep the card unfinished.
18. **Cancellation:** prefix the title with `Cancelled:`, record the reason and any replacement, set Next to cancelled, and move to Done without checking unmet acceptance items.

## Document integrity

19. Validate frontmatter, local links, board binding, and the linked card template.
20. Confirm missing or unusable settings route to setup/recovery and instructions sit under their matching section topics.

## Roles and readiness

21. **Role routing:** delegated workers load worker instructions only; a solo agent loads orchestrator instructions and executes directly. Delegation points directly to worker instructions and supplies the assignment context.
22. **Board migration:** new boards include Ready between Backlog and WIP; the orchestrator adds Ready to an existing board when missing.
23. **Dependency satisfied:** after a prerequisite change or completion, the orchestrator verifies evidence, ticks affected dependency items, and promotes eligible Backlog or Blocked cards to Ready. Partially satisfied, underspecified, or out-of-scope work stays outside Ready.
24. **Dependency invalidated:** the orchestrator unticks invalidated dependencies and moves affected Ready cards to Blocked with a prerequisite, resolver, and next check.
25. **Worker boundary:** workers return evidence, blockers, and remaining work without editing the board. The orchestrator evaluates the report, updates cards, and reconciles dependent work.
26. **Resume reconciliation:** the orchestrator checks dependencies against actual work on resume, including changes made outside the previous session.
