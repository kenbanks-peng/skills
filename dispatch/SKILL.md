---
name: dispatch
description: Orchestrate coding agents with native tuios worktrees, fleet, queues, review, checkpoints, ship, and a live dashboard. Support Linux workers without human-input steps.
---

# Dispatch

Use tuios as the orchestration system. Use Aven for durable tasks and outcomes.
Use the supplied scripts for repeatable operations. Native tuios still owns
live state, queues, mail, and worktrees; do not build a second scheduler.
Read [script procedures](references/automation.md) before starting a run.

## Working rules

- Work within the objective. Preserve unrelated work. Never ask a person a question or initiate an approval flow; record missing authority as a blocker.
- Do not use `ask-human`, `respond`, `request-approval`, approval forms, or unattended `ship push/pr`. Never type into `needs_input` or bypass a refusal.
- Keep one writer per task checkout. A finished turn permits review and checks; task acceptance requires passing checks and review.
- Use explicit session/pane IDs and native state. Reconcile uncertain delivery before retrying.
- Visible windows are limited to dispatch (with its dashboard), Aven, and active Linux workers. No visible shell, merge, review, check, integration, or monitoring windows. Use windowless execution first; required auxiliary windows must be hidden from creation. `--no-focus`, a background workspace, and closing later do not mean hidden.
- Before launch, confirm that native operations and their implicit starter/check windows obey this rule. If hidden execution is not supported, use a windowless path or record a blocker; do not create a visible fallback. At the end, close all run-owned windows except dispatch, including Aven and Linux workers. Preserve evidence, not extra windows.
- Use the requested execution environment. Linux work must run on Linux. Do not silently replace it with local macOS work.

## Run

1. **Prepare.** Read repository instructions and [planning](references/planning.md). Read `tuios --skill recipes` and needed topics. Run `workspace.py --run-dir DIR init --repo REPO --session SESSION --dispatch UUID` before creating resources. On resume, reuse DIR and run `status`, not init. Confirm actual daemon support.
2. **Plan.** Search Aven. Record tasks, acceptance checks, dependencies, target branch, merge policy, and concurrency. Use sensible repository defaults: current branch as target; squash for independent task branches unless instructed otherwise. Keep records short.
3. **Show the run.** Use `workspace.py --run-dir DIR status` and `dashboard.py observe/report` for [status in the existing dispatch pane](references/dashboard.md). Refresh after meaningful native events. Do not open an extra dashboard window.
4. **Launch.** Use [native workers](references/workers.md) and [Linux host execution](references/pi.md). Confirm that implicit starter windows stay hidden from creation. After each launch, use `workspace.py register` with the returned full IDs and run `audit`. Aven and Linux workers are the only permitted visible additions.
5. **Coordinate.** Use [ask, queue, mail, grouped waits, and events](references/coordination.md). Use `workspace.py queue --id ID --prompt-file FILE` for authorized follow-ups; reuse the ID to prevent duplicate submissions. Use state events, not repeated captures, to follow progress. Update the same dashboard after meaningful changes.
6. **Review and repair.** Inspect native review diffs and checkpoints. Use an independent reviewer or review the work yourself. Send line-specific corrections with `review note/send`; queue other follow-ups once. See [review and delivery](references/review-delivery.md).
7. **Check and deliver.** Use `checks.py --plan PLAN --cwd CHECKOUT --output DIR --require-system Linux` (or authorized Darwin). After review acceptance, use `deliver.py` with recorded source/target, policy, check evidence, and integration plan. It runs native ship and integrated checks without visible helper windows. See [delivery](references/review-delivery.md).
8. **Finish.** Use [cleanup and recovery](references/recovery.md). Save results and unresolved work, stop queues/writers, then run `workspace.py --run-dir DIR cleanup --evidence-saved` and `audit --final`, including hidden windows. Leave final status in dispatch. Report changes, checks, blockers, and retained non-window resources.

## Native tools by purpose

| Purpose | Use |
| --- | --- |
| Isolation | `worktree new/ls/diff/rm`; remote `worktree pull` |
| Parallel alternatives | `fan`, `compare`, `verify`, `diff`, verdict, `keep` |
| Assignment | `start-agent --prompt`, `ask-agent`, `queue` |
| Coordination | `send-agent-message`, explicit reply/read, thread waits |
| Monitoring | fleet selectors, `wait-for`, `subscribe`, `list-attention` |
| Visibility | workspace.py ownership/audit/status; dashboard.py observe/report |
| Review/recovery | `review note/send`, `checkpoint list/diff/restore` |
| Delivery | deliver.py; native `ship status` |
| Checks | checks.py plan execution, logs, timeouts, and evidence |

Use features for a purpose, not to inflate command counts. Read only the linked
guide needed for the current step. Installed command contracts define syntax.
[Acceptance](references/acceptance.md) defines the live release checks; static
tests do not prove that orchestration works.
