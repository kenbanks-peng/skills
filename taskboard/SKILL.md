---
name: taskboard
description: Set up and operate an agent-owned Doska taskboard for significant implementation, bug fixes, refactoring, research, reviews, planning, and multi-step project work. Use when initializing project tracking, decomposing work, delegating ownership, resuming a session, or reconciling progress and handoffs.
---

# Taskboard

Use Doska as the durable record of **what needs doing, who owns it, and what proves it is finished**. Own the system: initialize configuration, use the previously specified board or specify and create one, write actionable cards, coordinate execution, verify outcomes, and leave a resumable handoff. The user supplies intent, not routine taskboard administration.

Keep implementation detail in the repository; link it from cards. `.taskboard/settings.md` binds the project to its board; the board charter owns shared workflow policy; cards own live task state. Tool parameters and capabilities come from the live MCP server, not this skill.

## Start or resume

1. **Bind the project.** On every invocation, follow [board setup and recovery](references/board-setup.md): locate the project root, read or create `.taskboard/settings.md`, read live server capabilities, and use the specified board directly. If no board is specified, choose and persist its name, then create it. Board selection never involves searching or discovering candidates. Finish partial setup without asking the user to choose routine defaults. This step ends with a verified binding or an explicit degraded tracking outcome under the recovery rules.
2. **Load the working agreement.** Read the board, charter, active cards, dependencies, and latest handoffs. Initialize a missing charter and map an existing workflow as specified in board setup. Reconcile pending local records before selecting work.
3. **Establish roles.** Act as coordinator for the requested outcome unless delegated or an existing agreement assigns that role elsewhere. Execute work yourself or assign child cards to workers. Record session-qualified identities and the checkpoint channel on each delegated card: the parent owns coordination and transitions; the worker owns execution reporting. Confirm existing ownership before taking over inherited work.
4. **Make the request executable.** Search for the outcome across all statuses before creating a card. Reuse an unfinished match; reopen accepted work only if its acceptance no longer holds, otherwise link a new follow-up. Infer bounded scope, observable acceptance, verification, and dependencies from the request and repository. Use [card templates](references/templates.md). A small, single-owner job needs one card, not an epic.
5. **Start the work.** Set normal requested work to medium priority, order prerequisites first, promote scoped and unblocked work to Ready, then claim it. Choose the next Ready card within the authorized outcome; ask only when a material scope decision cannot be inferred. Track meaningful deliverables, not every tool call.

**Ready to proceed:** the work has a durable card, clear ownership, acceptance criteria, and a next action—or a durable local record under the outage rules. Remote-only tracking may proceed when local settings cannot be saved. If neither store is writable, leave a conversation-only blocked handoff and pause tracked execution until durable tracking is available. Report setup choices briefly and continue; routine defaults do not need an approval round.

## Decision defaults

- **Scope:** one board per repository across sessions, branches, and worktrees. Track the requested outcome and its necessary prerequisites; capture optional discoveries in Backlog without implementing them.
- **Review:** self-review for low-risk, reversible work. Security, authentication/authorization, sensitive data, destructive migrations, and production-impacting changes require an independent reviewer. Dispatch a separate agent when available and permitted by project policy; otherwise name the required human and leave the card in Review. Existing stricter review requirements prevail.
- **Integration:** default to verified changes in the current working tree or the requested document/artifact. An explicit project or user target overrides this. Tracking does not authorize commits, merges, deployment, or publishing; when these are required but unavailable, retain the appropriate pending status.
- **Verification:** discover authoritative project instructions and test/build commands. Run checks appropriate to the changed surface and record actual outcomes; use explicit content/source checks for documentation and research. Missing tooling is a recorded verification gap, not a pass.
- **Escalation:** first inspect configuration, repository context, server state, and handoffs. Ask only for unresolved project scope, unusable board references, ownership conflicts, missing access, consequential policy/scope choices, or destructive/shared-workflow changes. Ask a focused question with a recommended path; continue independent authorized work when safe.

## Workflow

Columns carry status; card bodies carry context. Default columns, left to right:

| Column      | Meaning and entry/exit rule                                                                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backlog     | Captured but not committed. Clarify scope, acceptance, dependencies, and priority before advancing. Also holds the explicitly labelled board charter. |
| Ready       | Bounded, actionable, and unblocked; available to claim. Order top to bottom by intended execution order.                                              |
| In Progress | An owner is actively executing. Default limit: one executable card per worker.                                                                        |
| Blocked     | Progress requires something outside the owner’s current work. Record the blocker, unblock owner, next check/trigger, and intended return column.      |
| Review      | Work and verification evidence are available; a named reviewer must decide acceptance. Record the next check and reviewer.                            |
| Done        | Acceptance criteria are met, evidence is recorded, and required review/integration is complete. This is the board’s sole native done column.          |

Normal flow: Backlog → Ready → In Progress → Review → Done. Blocked work returns to the recorded column once the dependency is resolved. Failed review returns to In Progress with specific remaining work. Reopened work gets a reason and a fresh next action.

Apply the charter’s review policy, initialized from Decision defaults. The coordinator arranges the review rather than leaving an unnamed review queue. Record self-review explicitly; it may occur in the same session as implementation. Moving to Review does not claim that review happened.

**Cancellation:** retain the card and record the reason plus a replacement link if relevant. Use a non-done Cancelled column, created when first needed. Cancelled is not delivered and does not satisfy a dependency unless the dependent scope is explicitly revised. Preserve history rather than deleting cards.

## Ownership and delegation

- **Coordinator / parent:** owns the overall outcome, card creation, scope, acceptance criteria, dependencies, assignments, column transitions, integration, and final acceptance. Maintains parent and child card bodies and acceptance checkboxes; delegation transfers execution, not acceptance authority.
- **Owner:** exactly one accountable executor per executable card. Use a recognizable identity with a session/run discriminator, e.g. `agent:api/run-42`, `human:Ken`, or `unassigned`; use real runtime identifiers when available, otherwise record a locally chosen label as such.
- **Worker:** executes its assigned card and reports significant findings, decisions, artifacts, verification results, blockers, and next actions during the work. May append execution comments as specified below; requests transitions or scope changes from the parent rather than applying them.
- **Reviewer:** performs the acceptance check and records the decision and remaining work through the same checkpoint channel. Distinct from the executor when independent review is required; the coordinator applies the resulting transition.
- **Card-body writer:** the coordinator serializes body replacements and lifecycle updates for its work group. This does not reserve authorship of execution evidence. Native assignment/locking is not assumed; these are coordination conventions.

The coordinator claims or assigns work by rereading the card, confirming it is unassigned or explicitly released, recording the executor and next action, and moving it to In Progress. Reread to verify the result. This is a coordination protocol, not an atomic lock: if another session is active or ownership is disputed, agree a writer and assignment before proceeding. Never claim solely because a timestamp looks old.

Before dispatching a subagent:

1. Create/link its child card and assign a locally chosen worker label. Record the returned runtime ID after dispatch so the label maps to the actual run.
2. Supply board/card opaque IDs, parent reference, bounded scope, acceptance criteria, dependencies, allowed files/worktree, and verification expectations.
3. Establish the checkpoint channel below using verified live capabilities and worker access. Supply the relevant card content if the worker cannot read Doska. Require material checkpoints during execution, not just a final report.
4. Require a return report: result, artifacts/commit, checks and outcomes, blockers, and remaining work. The coordinator reconciles checkpoints, records the return, and routes the card through acceptance.

A dispatched job is not completed work. On failure, cancellation, or lost contact, record the actual state, preserve partial artifacts, and explicitly release or reassign ownership. Reassignment requires a handoff; do not infer that an old worker has stopped writing files.

### Execution checkpoints

Choose the channel before dispatch:

- **Append-only comments supported and accessible:** workers may append checkpoints directly to their assigned child card. Verify this operation in the live API; do not assume comments exist or simulate appending by replacing the body. Reviewers may append their decisions to the card under review. Notify the coordinator of blockers, scope decisions, and readiness for review through the agreed reporting channel; do not assume comments generate notifications.
- **Only whole-body updates available, or worker lacks board access:** workers send checkpoints to the coordinator, which promptly records them on the child card with the worker’s identity and original timestamp. Keep one body writer; separate Markdown sections do not make concurrent body replacements safe.
- **No intermediate messaging available:** arrange coordinator-readable per-worker checkpoint files and a concrete polling/check-in point before dispatch, or split delegation into bounded stages that return checkpoints. Record this channel on the card. Do not promise live reporting from a final-response-only worker.

Use the execution checkpoint template in [references/templates.md](references/templates.md) at material findings, approach-changing decisions, verification milestones, blockers, and completion—not after every tool call. Each checkpoint states what changed, supporting evidence, and the next action. The coordinator reads new checkpoints at check-ins, updates the body’s current evidence and Next summary, and applies justified lifecycle changes. Significant execution history stays on the child card, not solely in a final parent summary.

Before any body replacement, reread and preserve human edits, task states, and attachment references. Keep shared board structure with its authorized writer. If competing writes are detected, stop and reconcile; reread/write is not compare-and-swap.

## Tasks, subtasks, and dependencies

Use a **checklist** for steps sharing one owner, lifecycle, and acceptance decision. Use a **child card** when work needs separate ownership, parallel execution, its own review/deadline, or independent blocking. Split outcomes that cannot be verified in a bounded work session; avoid decomposing into activity-only cards such as “think about approach.”

A multi-card outcome gets a **parent card** with scope, overall acceptance, and a child index. Each child links back to the parent. State dependencies separately from hierarchy: belonging to the same parent does not imply an execution order.

- Parent index: `- [ ] [[12]] — API contract accepted`.
- Child relationship: `Parent: [[8]]`.
- Dependency: `Depends on: [[12]] — contract must be accepted before implementation`.
- Link cards by their board-local number in Markdown; retain opaque IDs in execution handoffs. Across boards, use a supported URL or explicit board/card identity rather than assuming `[[12]]` resolves globally.

The coordinator updates parent checkboxes only when children are accepted. Children in Review, or merely reporting success, remain unchecked. A cancelled child requires an explicit parent scope decision.

Parents remain In Progress while the coordinator has actionable coordination work; otherwise use Blocked with the dependency and next trigger. Parent orchestration is exempt from the worker’s one-executable-card limit. A parent reaches Done only when all required children and overall integration/acceptance are complete; child completion alone is insufficient.

## Card writing

Card bodies use GitHub-flavored Markdown: headings, lists, emphasis, code fences, tables, and ordinary `[label](url)` links. Doska adds:

| Syntax                     | Behavior                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `- [ ]` / `- [x]`          | Clickable tasks with a done/total count. Use `check_task` for individual checkbox updates rather than replacing the body. |
| `[[12]]`                   | Card link displaying the current title and column color. `[[12                                                            | Fixed label]]` pins the label instead of following title changes. |
| `==highlight==`            | Highlighted text.                                                                                                         |
| Standalone `-cut-` line    | Ends the board preview; the full body remains visible in the card view.                                                   |
| `![alt](attachment:<key>)` | Embeds an existing attachment. Preserve its key; uploads happen through the app.                                          |

Use the templates in [references/templates.md](references/templates.md) whenever creating a charter, task, parent, or handoff.

- Title: a short verb + outcome, e.g. `Reject expired invitation tokens`. Prefix only special cards: `[Board]`, `[Epic]`. Status and owner belong outside the title.
- Preview: outcome, owner, and next action above a standalone `-cut-`; put detailed context below it.
- Acceptance: observable outcomes expressed as GFM task-list items. Tick only with evidence; task counts are not a measure of effort or proof of completion.
- Relationships: prefer `[[12]]` so titles stay current; use ordinary Markdown links for specs, PRs, builds, and other artifacts.
- Evidence: record what ran, its outcome, and an artifact/commit reference. Distinguish passed, failed, and not run, with reasons for gaps. Research/review cards need source/findings or disposition evidence rather than fictional test runs.
- Updates: use dated, concise checkpoints with an explicit timezone. Keep the latest next action visible; retain consequential decisions and handoffs, not a tool transcript.
- Priority and deadline: use supported native fields, not duplicated body metadata. Assign high to urgent/critical-path unblocking work, medium to normal requested work, and low to optional follow-up; reserve unset for untriaged captures. Leave deadlines empty unless the user or project establishes a real commitment or constraint.

## Maintain and finish

Update at state transitions, material discoveries, blockers, dispatch/return, and session end—not after every tool call. Keep blocked/review cards owned so they cannot disappear between executors.

At each checkpoint, workers report through their assigned channel; the coordinator performs the following reconciliation:

1. Reconcile the active card with actual work and update acceptance/evidence.
2. Record any newly discovered work as a linked card; distinguish required follow-up from optional improvements.
3. Refresh parent indexes and dependent cards affected by accepted results. Reread dependencies, clear resolved blockers, and return cards to their recorded columns; promote unassigned work to Ready when all entry gates hold.
4. Leave a next action with a responsible identity, or a verified completion record.

Before Done, verify every acceptance item, required review, and integration into the agreed target. Record exceptions only when the responsible human accepts the scope change; do not quietly redefine success. A passing branch test does not prove a merge or deployment occurred. Preserve the finishing owner for attribution.

At session end or context handoff, use the handoff template. Release unfinished work to Ready only when it is safe for another worker to claim; otherwise retain ownership or mark Blocked with the specific constraint. Report the board/card references, delivered work, blockers, and next action to the user.

When resuming or asked for status, reconcile stale ownership, unresolved dependencies, review queues, parent/child mismatches, and upcoming deadlines. Repair evidence-backed bookkeeping for this work group, arrange outstanding reviews, and record the next check for anything still blocked. Confirm release before reassigning old ownership. Report observed state, not inferred progress percentages. Destructive cleanup or board restructuring requires explicit agreement; a tracking session does not authorize implementing unrelated backlog items.
