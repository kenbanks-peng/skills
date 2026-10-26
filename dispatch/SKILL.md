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
- Visible windows are limited to dispatch (with its dashboard), Aven, and active Linux workers. No visible shell, merge, review, check, integration, or monitoring windows. Use windowless execution first; required auxiliary windows must be hidden from creation. `--no-focus`, a background workspace, and closing later do not mean hidden.
- Before launch, confirm that native operations and their implicit starter/check windows obey this rule. If hidden execution is not supported, use a windowless path or record a blocker; do not create a visible fallback. At the end, close all run-owned windows except dispatch, including Aven and Linux workers. Preserve evidence, not extra windows.
- Use the requested execution environment. Linux work must run on Linux. Do not silently replace it with local macOS work.

## Run

1. **Prepare.** Read repository instructions and [planning](references/planning.md). Read `tuios --skill recipes` and the topics needed for this run. Confirm the running daemon supports the chosen path, not just that CLI help lists it.
2. **Plan.** Search Aven. Record tasks, acceptance checks, dependencies, target branch, merge policy, and concurrency. Use sensible repository defaults: current branch as target; squash for independent task branches unless instructed otherwise. Keep records short.
3. **Show the run.** Open and capture one [live dashboard](references/dashboard.md) in the dispatcher's workspace before launching workers. Group owned sessions in a run space. If the dashboard cannot open, report the exact failure; do not call the run ready or silently omit it.
4. **Launch.** Use [native worktrees and workers](references/workers.md). Choose distinct task workers or native fan for competing solutions. For Linux use [native host execution](references/pi.md). Name each worker by task, role, and host. Keep starter shells hidden from creation and remove them after the worker is ready.
5. **Coordinate.** Use [ask, queue, mail, grouped waits, and events](references/coordination.md). Queue authorized next work for busy agents. Use state events, not repeated captures, to follow progress. Update the same dashboard after meaningful changes.
6. **Review and repair.** Inspect native review diffs and checkpoints. Use an independent reviewer or review the work yourself. Send line-specific corrections with `review note/send`; queue other follow-ups once. See [review and delivery](references/review-delivery.md).
7. **Check and deliver.** Run task and integrated checks without windows through the execution tool. Use a hidden native command only when needed and supported. Use noninteractive Git and native `ship commit/merge` without visible helper windows. See [review and delivery](references/review-delivery.md).
8. **Finish.** Use [native cleanup and recovery](references/recovery.md). Save results and unresolved work, stop owned agents safely, and close every run-owned window except dispatch. Verify the final inventory, including hidden windows. Leave the final dashboard in dispatch and report changes, checks, blockers, and retained non-window resources.

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
| Checks | windowless execution; hidden native commands only when required |

Use features for a purpose, not to inflate command counts. Read only the linked
guide needed for the current step. Installed command contracts define syntax.
[Acceptance](references/acceptance.md) defines the live release checks; static
tests do not prove that orchestration works.
