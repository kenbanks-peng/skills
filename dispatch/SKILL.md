---
name: dispatch
description: Coordinate Linux coding agents with the linux launcher, tuios worktrees, queues, review, checks, and delivery. Use Aven for durable tasks.
---

# Dispatch

Use tuios for worktrees, panes, coordination, review, and delivery.
Use Aven for durable objectives and outcomes. Use the supplied scripts for
repeatable operations. Read [script procedures](references/automation.md).

## Procedure

1. **Prepare.** Read repository instructions and [planning](references/planning.md).
   Read `tuios --skill recipes`. Save the initial inventory with
   `workspace.py --run-dir DIR init --repo REPO --session SESSION --dispatch UUID`.
   On resume, reuse DIR and run status.
2. **Plan.** Search Aven. Record scope, acceptance checks, dependencies, branch,
   merge policy, and concurrency. Use the current branch as target and squash
   independent task branches. Give each writing task its own checkout.
3. **Show status.** Keep the [dashboard](references/dashboard.md) in the existing
   dispatch pane with dashboard.py observe/report. Refresh after meaningful events.
4. **Launch Linux workers.** Follow [workers](references/workers.md). Create a
   native worktree, then use the execution tool to run
   `tuios new-window -s "$SESSION" "$WORKER" --keep-open --print-id --cwd "$WORKTREE" -- linux container -- pi "$ASSIGNMENT"`.
   The linux launcher selects and starts the Linux environment. Give it the
   task checkout as cwd. Register returned pane IDs and audit ownership.
5. **Coordinate.** Use [queue, mail, asks, and events](references/coordination.md)
   when the worker integration provides them. Use the worker's actual output
   and check results as completion evidence. Record specific tool failures.
6. **Review and repair.** Inspect the candidate diff and checkpoints. Review
   independently, send precise corrections, and rerun checks after repairs.
   See [review and delivery](references/review-delivery.md).
7. **Check and deliver.** Run project checks in the worker's Linux environment.
   Save logs and revision identity. Use checks.py for repeatable check plans
   and deliver.py for reviewed local candidates and integrated checks.
8. **Finish.** Save outcomes, stop queues and writers, then use
   `workspace.py --run-dir DIR cleanup --evidence-saved` and `audit --final`.
   Leave dispatch with final status. Preserve useful branches, worktrees, and
   logs. See [recovery](references/recovery.md).

## Operating practice

- Use `linux container --` for every worker, including review agents.
- Launch directly; the launcher owns runtime and operating-system selection.
- Show active workers in tuios. Register starter and helper panes, and close
  them when their work ends.
- Use explicit session and pane IDs. Reconcile uncertain operations from saved
  state before retrying.
- Use repository defaults for ordinary task decisions. Record unresolved scope
  or authority in Aven and continue independent work.
- Accept a task after its checks and independent review pass.
- Report changes, checks, unresolved work, and retained resources.

Read the linked guide for the current step. Installed tool help defines command
syntax. [Acceptance](references/acceptance.md) separates live checks from tests.
