---
name: dispatch
description: Orchestrate coding agents with native tuios worktrees, fleet, queues, review, checkpoints, ship, and a live dashboard. Support Linux workers without human-input steps.
---

# Dispatch

Use tuios as the orchestration system. Use Aven for durable tasks and outcomes.
Follow native recipes. Do not build a scheduler, state bridge, or terminal wrapper.

## Working rules

- Work within the objective. Preserve unrelated work. Never ask a person a question or initiate an approval flow; record missing authority as a blocker.
- Do not use `ask-human`, `respond`, `request-approval`, approval forms, or unattended `ship push/pr`. Never type into `needs_input` or bypass a refusal.
- Keep one writer per task checkout. A finished turn permits review and checks; task acceptance requires passing checks and review.
- Use explicit session/pane IDs and native state. Reconcile uncertain delivery before retrying.
- Show useful work, not terminal debris: one dashboard, named workers, and at most one check pane per checkout. Save logs before closing temporary panes.
- Use the requested execution environment. Linux work must run on Linux. Do not silently replace it with local macOS work.

## Run

1. **Prepare.** Read repository instructions and [planning](references/planning.md). Read `tuios --skill recipes` and the topics needed for this run. Confirm the running daemon supports the chosen path, not just that CLI help lists it.
2. **Plan.** Search Aven. Record tasks, acceptance checks, dependencies, target branch, merge policy, and concurrency. Use sensible repository defaults: current branch as target; squash for independent task branches unless instructed otherwise. Keep records short.
3. **Show the run.** Open and capture one [live dashboard](references/dashboard.md) in the dispatcher's workspace before launching workers. Group owned sessions in a run space. If the dashboard cannot open, report the exact failure; do not call the run ready or silently omit it.
4. **Launch.** Use [native worktrees and workers](references/workers.md). Choose distinct task workers or native fan for competing solutions. For Linux use [native host execution](references/pi.md). Name each worker by task, role, and host. Remove the unused starter shell after the worker is ready.
5. **Coordinate.** Use [ask, queue, mail, grouped waits, and events](references/coordination.md). Queue authorized next work for busy agents. Use state events, not repeated captures, to follow progress. Update the same dashboard after meaningful changes.
6. **Review and repair.** Inspect native review diffs and checkpoints. Use an independent reviewer or review the work yourself. Send line-specific corrections with `review note/send`; queue other follow-ups once. See [review and delivery](references/review-delivery.md).
7. **Check and deliver.** Run checks through `run` in the reusable check shell, or `new-window --wait` for a bounded command. Use noninteractive Git. Use `ship commit`, then `ship merge` into the recorded target. Run integrated checks.
8. **Finish.** Use [native cleanup and recovery](references/recovery.md). Close completed check/reviewer/view panes; retain useful unresolved work. Leave one final dashboard and report delivered changes, checks, blockers, and retained resources.

## Native tools by purpose

| Purpose | Use |
| --- | --- |
| Isolation | `worktree new/ls/diff/rm`; remote `worktree pull` |
| Parallel alternatives | `fan`, `compare`, `verify`, `diff`, verdict, `keep` |
| Assignment | `start-agent --prompt`, `ask-agent`, `queue` |
| Coordination | `send-agent-message`, explicit reply/read, thread waits |
| Monitoring | fleet selectors, `wait-for`, `subscribe`, `list-attention` |
| Visibility | session spaces, worker names, `pane-view`, TML show/patch/capture |
| Review/recovery | `review note/send`, `checkpoint list/diff/restore` |
| Delivery | `ship commit/merge/status` |
| Checks | reusable `run` shell or `new-window --wait` |

Use features for a purpose, not to inflate command counts. Read only the linked
guide needed for the current step. Installed command contracts define syntax.
[Acceptance](references/acceptance.md) defines the live release checks; static
tests do not prove that orchestration works.
