---
name: agents
description: Run parallel or dependent coding tasks with Aven and Workmux. Track ownership, verify merges, and resume interrupted work.
---

# Multi-Agent Task Workflow using Aven and Workmux

You are the dispatcher. Use Aven to track tasks; Use Workmux to manage workers in separate worktrees. This skill’s instructions take precedence over any successive loaded skills.

## Workflow preparations

### Skills

- **aven** — task management.
- **coordinator** — agent dispatch, monitoring, review, and merging.
- **workmux** — worktree and agent management.
- **worktree** — worktree task delegation.
- **merge** — worker-side commit, rebase, and merge.

### Multiplexer

Use the dispatcher's active multiplexer: Herdr when `HERDR_ENV=1`; otherwise tmux when `TMUX` is set.

- **Herdr:** Omit `--parent-session` and ignore tmux session-selection and window-placement instructions. Identify the dispatcher's own tab and rename it with `herdr tab rename <dispatcher-tab-id> dispatcher`.
- **tmux:** Identify the dispatcher's own window and rename it with `tmux rename-window -t <dispatcher-window-id> dispatcher`.

### Miscellaneous

If no git repository exists, initialize one using `git init` and add a .gitignore as an initial commit.

Create an aven project using the root folder name for <project>. Run `aven project create <project> --path .`

Open a `tasks` tab (Herdr) or window (tmux) by running `sh "<skill-dir>/scripts/open-tasks-tab.sh" "<absolute-project-root>"`.

When setting status with `aven edit`, identify task ownership within Aven by including `--agent <agent>` (for example, `--agent pi`) while in `active` state, otherwise by including `--clear-agent`.

## 1. Create epics and tasks

1. When helpful, create epics.
2. Reuse existing tasks; split remaining work into 'todo' tasks with applicable dependencies, and where feasible, with disjoint parallel write scopes.
3. Keep deferred work in `backlog` and outside the current run.

## 2. Select ready tasks

1. Select tasks with `aven list --ready` and applicable filters; inspect each with `aven context <task-ref>`. Mark prerequisites `done` only after [Verify and complete the task](#5-verify-and-complete-the-task).

## 3. Prepare and dispatch a worker

1. Before dispatch, mark the task `active` with `aven edit <task-ref> --status active --agent <agent>`, identifying the assigned worker.
2. Follow coordinator dispatch with the [Creating workers](#creating-workers) overrides and [Worker brief](#worker-brief).
3. After confirming startup, add a `DISPATCH` note using [Task note format](#task-note-format).

#### Creating workers

Use `workmux add --config ~/.config/workmux/agents.linux.yaml` by default (Linux sandbox). Use `~/.config/workmux/agents.macos.yaml` only when the user explicitly requests macOS or excludes sandboxing. Do not use `--agent`.

Override coordinator's parallel spawning: serialize `workmux add` and `workmux open` per repository to avoid Git/Workmux metadata contention.

On a lock error, pause dispatch; inspect owning processes, `workmux list`, and `git worktree list` before retrying. Never delete a potentially live lock. Preserve work, reconcile partial resources, and discard only confirmed-safe resources.

If startup confirmation fails, inspect `workmux status` and `workmux capture <handle>` for each unconfirmed worker before retrying or waiting for completion. Retain unfinished work under [Recovery and handoff](#recovery-and-handoff).

#### Worker brief

Include the assigned Aven task reference, base branch, and these instructions; add only context not already in the task:

- Read task context with `aven context <task-ref>`.
- Implement the task, verify acceptance criteria, and commit. Run required checks and the actions they gate (commit, merge, or success-report writes) in a fail-fast Bash block beginning with `set -euo pipefail`. Each check must succeed before proceeding; a failure stops the block. Record failures separately as failures, keeping the task active and work retained.
- Log a concise task report in Aven before reporting to dispatch.
- Report only to dispatch: concise implementation summary, notable decisions, affected components, check results, commit IDs, blockers, and discovered work.
- Wait for explicit merge authorization from dispatch. Once authorized, follow the [Pi merge command](#pi-merge-command); dispatch handles user notification.

### 4. Review and merge the result

1. Follow coordinator review.
2. Validate the worker report against Git state and `aven show <task-ref>`.
3. Keep the report provisional until merged-work verification passes. Workmux `done` does not complete the Aven task.
4. Follow coordinator merging with the [Pi merge command](#pi-merge-command) override. Include the worker brief's notification override in every worker merge request.
5. Wait for the worker's merge completion or failure report before verifying the merged work.

#### Pi merge command

Pi uses `/skill:<name>`; trailing arguments become a user request, not `$ARGUMENTS` substitutions. The merge target comes from the branch's `workmux-base` Git config.

Before merging, check it against the task's recorded base:

```bash
set -euo pipefail
branch=$(git branch --show-current)
configured_base=$(git config --local --get "branch.$branch.workmux-base")
test "$configured_base" = "<recorded-base>"
```

Stop if the base is missing or mismatched. Otherwise, replace the coordinator's `/merge` with this worker request:

```text
/skill:merge --keep Omit --notification from the workmux merge command; dispatch handles user notification. Run required checks and the actions they gate in fail-fast Bash blocks beginning with set -euo pipefail; write success reports only after all required checks pass.
```

Follow the merge skill's full procedure. The notification override changes only notification behavior; `--keep` retains the worktree until dispatch verification passes.

### 5. Verify and complete the task

1. Confirm the merge reached the base branch; run required checks on that revision in a fail-fast Bash block beginning with `set -euo pipefail`. Gate cleanup, completion comments, and `done` status on every required check passing; apply the same gate to run-wide checks and the final `SUMMARY`.
2. If checks fail or cannot run, keep the task `active` and retain its worktree. Return actionable failures to the worker for repair, review and merge the fix, then repeat verification on the updated base revision. If blocked, record the merge, check results, blocker, and next action in Aven; report the blocker to the user.
3. Once acceptance criteria and checks pass, retain the Git-verified merged revision and check results for the completion comment.
4. Clean up the task's worktree and branch; add one `MERGE` completion comment in Aven containing the merged revision, check results, and closure: `Verified and done. Cleanup complete.` If cleanup fails, record pending cleanup and the next action without claiming closure.
5. Mark the task `done`, then query `aven list --ready` with the run's filters for newly eligible tasks.
6. Create or reuse Aven tasks for discovered work. Put current-run work in `todo` with applicable dependencies; keep deferred work in `backlog` and outside the current run.

### 6. Complete the run

1. Confirm all selected tasks are verified and merged.
2. Run run-wide checks on the final base revision; require passing results.
3. Confirm cleanup is complete. If all worker worktrees have been removed, remove their parent worktree folder with `rmdir` if it still exists. Preserve a non-empty folder and record pending cleanup.
4. If any condition is unmet, record a handoff under [Recovery and handoff](#recovery-and-handoff) and leave the task progress tab open.
5. Otherwise, close the run-owned task progress tab before the final response using `sh "<skill-dir>/scripts/close-tasks-tab.sh"`.
6. Record the run's `SUMMARY` in Aven and give the user a concise final report of the outcome, validation, and follow-up work.

### Recovery and handoff

#### Interrupted work

After context loss or worker exit, run `aven list --open` and inspect each task with `aven context <task-ref>`. Before restarting, check Workmux and Git using handles and branches from Aven notes; resolve ownership or merge-record conflicts.

#### Pending cleanup

Finish pending cleanup for `done` tasks without merging again.

#### Reassignment

Before reassignment, stop the previous worker, preserve its changes, check whether it merged, and record the handoff.

#### Unfinished tasks

Record progress, check results, blockers, and next actions in Aven. Retain unfinished worktrees, overriding coordinator cleanup.

#### Task note format

Use these prefixes for dispatch-written Aven notes and comments. They are note templates, not shell commands. These rules override more verbose administrative reporting in the required skills.

- Keep administrative entries to one line per event. Record only actual transitions; do not narrate routine commands, polling, or repeat unchanged metadata.
- Keep agent activity and results substantive and concise: state the key change or finding and its evidence. Include decisions or failures only when they affect the outcome. Do not reproduce the full worker report.
- Reference earlier dispatch metadata rather than repeating it. Record changed handles, branches, or execution modes explicitly.
- Report observed facts only; worker claims remain provisional until verified.
- Reference the Git-verified starting revision in `DISPATCH`, the worker commit in `RESULT`, and the verified base revision in `MERGE`. Use Git short-form SHAs for all revision references in notes and comments, including `SUMMARY`, generated with `git rev-parse --short <revision>` so the abbreviation is unambiguous in the repository. Check each reference against Git; do not use a branch name alone as the revision record.

##### Templates

```text
DISPATCH: <agent> started in <handle> on <task-branch> at <starting-revision-short-SHA>, based on <base>. <Linux|macOS> worker using <config-path>.
ACTIVITY: <key progress>. <Significant decision and reason, if needed>.
RESULT: <key change or finding> in commit <commit-short-SHA>. <Decisive check result>. Awaiting merge verification.
MERGE: Merged into <base> at <revision-short-SHA>. <Check results>. Verified and done. Cleanup complete.
BLOCKED: <blocker>. Work retained in <worktree/branch>. <Owner> to <next action>.
SUMMARY: <delivered outcome>. <Acceptance evidence and final checks> at <revision-short-SHA>. <Follow-up work, if any>.
```

Write each event as a separate note. Display paths under the user's home directory with `~` in notes. Omit the task reference when the note is attached to that task; include it in shared or run-level notes. Record `RESULT` once; use the `MERGE` completion comment for closure rather than a separate `CLOSED` entry. Use `SUMMARY` once at run completion.
