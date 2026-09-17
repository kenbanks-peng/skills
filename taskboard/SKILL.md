---
name: doska
description: Track significant implementation, bug fixes, refactoring, research, reviews, planning, and multi-step project work in Doska. Use when setting up a taskboard, decomposing work, delegating ownership, resuming a session, or reconciling progress and handoffs.
---

# Taskboard

Use Doska as the durable record of **what needs doing, who owns it, and what proves it is finished**. Keep implementation detail in the repository; link it from cards. Tool parameters and capabilities come from the live MCP server, not this skill.

## Start or resume

1. Read the server instructions and discover the relevant board. Prefer a board explicitly supplied by the user, then a board whose charter matches the repository/project. Ask when several match.
2. Read the board and its charter. For a new board, follow [board setup](references/board-setup.md). Respect an existing workflow; propose migrations rather than silently renaming columns or moving everyone’s cards.
3. Identify this session’s coordinator and board writer. Read active cards, dependencies, and the most recent handoff before choosing work. An inherited card is not automatically yours.
4. Find an existing card for the requested outcome before creating one. Track meaningful deliverables, not every tool call. A small, single-owner job needs one card, not an epic.
5. Before substantive work, record scope, acceptance criteria, ownership, and the next action using [card templates](references/templates.md). Claim only Ready work whose dependencies are satisfied.

**Ready to proceed:** the board is unambiguous, the work has a durable card, and ownership is agreed. If Doska is unavailable, tell the user; retain a temporary handoff in the conversation or an agreed local file and reconcile it before claiming the board is current. Do not invent successful writes.

## Workflow

Columns carry status; card bodies carry context. Default columns, left to right:

| Column | Meaning and entry/exit rule |
| --- | --- |
| Backlog | Captured but not committed. Clarify scope, acceptance, dependencies, and priority before advancing. Also holds the explicitly labelled board charter. |
| Ready | Bounded, actionable, and unblocked; available to claim. Order top to bottom by intended execution order. |
| In Progress | An owner is actively executing. Default limit: one executable card per worker. |
| Blocked | Progress requires something outside the owner’s current work. Record the blocker, unblock owner, next check/trigger, and intended return column. |
| Review | Work and verification evidence are available; a named reviewer must decide acceptance. Record the next check and reviewer. |
| Done | Acceptance criteria are met, evidence is recorded, and required review/integration is complete. This is the board’s sole native done column. |

Normal flow: Backlog → Ready → In Progress → Review → Done. Blocked work returns to the recorded column once the dependency is resolved. Failed review returns to In Progress with specific remaining work. Reopened work gets a reason and a fresh next action.

For low-risk work, the owner may perform the acceptance check if the charter permits it; record this as self-review. Honor any required human or independent review. Moving to Review does not claim that review happened.

**Cancellation:** retain the card and record the reason plus a replacement link if relevant. Use a non-done Cancelled column, created when first needed. Cancelled is not delivered and does not satisfy a dependency unless the dependent scope is explicitly revised. Preserve history rather than deleting cards.

## Ownership and delegation

- **Coordinator:** owns the overall outcome, decomposition, assignments, integration, and final acceptance. A parent card remains their responsibility when children are delegated.
- **Owner:** exactly one accountable executor per executable card. Use a recognizable identity with a session/run discriminator, e.g. `agent:api/run-42`, `human:Ken`, or `unassigned`; use real runtime identifiers when available, otherwise record a locally chosen label as such.
- **Reviewer:** the person/agent responsible for the acceptance check. Distinct from the executor when independent review is required.
- **Board writer:** one designated coordinator serializes writes for the active work. Workers report progress to that writer by default. Native assignment/locking is not assumed; these are body conventions.

Claim by rereading the card, confirming it is unassigned or explicitly released, recording owner and next action, and moving it to In Progress. Reread to verify the result. This is a coordination protocol, not an atomic lock: if another session is active or ownership is disputed, agree a writer and assignment before proceeding. Never claim solely because a timestamp looks old.

Before dispatching a subagent:

1. Create/link its child card and assign an identity that can be matched to the actual run.
2. Supply board/card opaque IDs, parent reference, bounded scope, acceptance criteria, dependencies, allowed files/worktree, and verification expectations.
3. Specify whether it reports to the coordinator or has explicit write authority for its card. Give it the relevant card content if it cannot access Doska.
4. Require a return report: result, artifacts/commit, checks and outcomes, blockers, and remaining work. The coordinator records the report and routes the card through acceptance.

A dispatched job is not completed work. On failure, cancellation, or lost contact, record the actual state, preserve partial artifacts, and explicitly release or reassign ownership. Reassignment requires a handoff; do not infer that an old worker has stopped writing files.

If workers are authorized to update their own cards, keep the coordinator as sole writer of parent cards and shared board structure. Before any body replacement, reread and preserve human edits, task states, and attachment references. If competing writes are detected, stop and reconcile; reread/write is not compare-and-swap.

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

| Syntax | Behavior |
| --- | --- |
| `- [ ]` / `- [x]` | Clickable tasks with a done/total count. Use `check_task` for individual checkbox updates rather than replacing the body. |
| `[[12]]` | Card link displaying the current title and column color. `[[12|Fixed label]]` pins the label instead of following title changes. |
| `==highlight==` | Highlighted text. |
| Standalone `-cut-` line | Ends the board preview; the full body remains visible in the card view. |
| `![alt](attachment:<key>)` | Embeds an existing attachment. Preserve its key; uploads happen through the app. |

Use the templates in [references/templates.md](references/templates.md) whenever creating a charter, task, parent, or handoff.

- Title: a short verb + outcome, e.g. `Reject expired invitation tokens`. Prefix only special cards: `[Board]`, `[Epic]`. Status and owner belong outside the title.
- Preview: outcome, owner, and next action above a standalone `-cut-`; put detailed context below it.
- Acceptance: observable outcomes expressed as GFM task-list items. Tick only with evidence; task counts are not a measure of effort or proof of completion.
- Relationships: prefer `[[12]]` so titles stay current; use ordinary Markdown links for specs, PRs, builds, and other artifacts.
- Evidence: record what ran, its outcome, and an artifact/commit reference. Distinguish passed, failed, and not run, with reasons for gaps. Research/review cards need source/findings or disposition evidence rather than fictional test runs.
- Updates: use dated, concise checkpoints with an explicit timezone. Keep the latest next action visible; retain consequential decisions and handoffs, not a tool transcript.
- Priority and deadline: use native fields, not duplicated body metadata. High means urgent/unblocking; medium normal; low deferrable; unset untriaged. A deadline is a real commitment or constraint, not a guessed effort estimate.

## Maintain and finish

Update at state transitions, material discoveries, blockers, dispatch/return, and session end—not after every tool call. Keep blocked/review cards owned so they cannot disappear between executors.

At each checkpoint:

1. Reconcile the active card with actual work and update acceptance/evidence.
2. Record any newly discovered work as a linked card; distinguish required follow-up from optional improvements.
3. Refresh parent indexes and dependent cards affected by accepted results.
4. Leave a next action with a responsible identity, or a verified completion record.

Before Done, verify every acceptance item, required review, and integration into the agreed target. Record exceptions only when the responsible human accepts the scope change; do not quietly redefine success. A passing branch test does not prove a merge or deployment occurred. Preserve the finishing owner for attribution.

At session end or context handoff, use the handoff template. Release unfinished work to Ready only when it is safe for another worker to claim; otherwise retain ownership or mark Blocked with the specific constraint. Report the board/card references, delivered work, blockers, and next action to the user.

When resuming or asked for status, reconcile stale ownership, unresolved dependencies, review queues, parent/child mismatches, and upcoming deadlines. Report observed state, not inferred progress percentages. Destructive cleanup or board restructuring requires explicit agreement; a tracking session does not authorize implementing unrelated backlog items.
