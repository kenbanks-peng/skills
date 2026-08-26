---
name: implement-sequential
description: "Implement every ticket for a spec sequentially, with one fresh agent per ticket, then summarize and close the spec ticket."
disable-model-invocation: true
---

# Implement All

Implement the implementation tickets for the spec supplied by the user. This is a **sequential orchestrator**: run exactly one ticket agent at a time. Do not start the next agent until the current agent has returned its result summary and its ticket is confirmed closed.

The issue tracker and triage-label vocabulary should have been provided to you. If not, tell the user to run `/setup-matt-pocock-skills`.

## Process

1. Read the parent spec ticket and all of its implementation tickets. Read enough of the tickets, their blocking edges, and their status to understand the task graph. Use the tracker configuration to find the tickets. Do not treat the parent spec ticket itself as an implementation ticket.

2. Work the ticket frontier sequentially:

   - A ticket is ready only when it is open and all of its blockers are closed.
   - Ignore tickets that are already closed.
   - If more than one ticket is ready, select one deterministically in the tracker or published dependency order.
   - Never run ticket agents concurrently or in the background.

3. For each ready ticket, start a **fresh implementation agent**. The agent works on the orchestrator's current branch, after the commits from all earlier ticket agents. Give it context pointers to the parent spec ticket, the ticket it owns, and any needed prior summaries or commits. Do not duplicate those sources in the prompt.

   Require the agent to:

   - implement only its assigned ticket;
   - use TDD where possible at the agreed seams;
   - run type checks and focused tests regularly, then the full test suite before completion;
   - run `/code-review` and fix the issues it finds;
   - commit its completed work to the current branch;
   - close its ticket in the configured tracker only after the work is complete; and
   - return a concise completion summary containing the ticket reference, commit SHA, delivered behavior, verification and review results, and confirmation that the ticket is closed.

4. Wait for the agent's completion summary. Verify that its ticket is closed, then post the agent's complete summary as one comment on the parent spec ticket. Do this before selecting another ticket. Retain each verified summary for the final parent-spec comment.

   If an agent fails, cannot close its ticket, or does not provide the required result, stop immediately. Do not start another ticket agent and do not close the parent spec ticket. Report the blocked ticket and the agent result to the user.

5. Repeat steps 2–4 until every implementation ticket is closed. If no ticket is ready while open tickets remain, stop and report the unresolved blocking edges; do not close the parent spec ticket.

6. Post one final consolidated completion comment on the parent spec ticket. Include the retained ticket summaries, grouped by ticket, so the final implementation and verification evidence is easy to audit. Do not modify the spec ticket body.

7. Close the parent spec ticket only after the final completion comment was posted successfully.
