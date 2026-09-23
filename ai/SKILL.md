---
name: ai
description: Use the ai CLI to find and manage tasks, save handoff notes, control project execution runs and worker attempts, or inspect execution boards.
---

# AI CLI

Use `ai task` for task management. Use `ai run` and `ai attempt` for worker
execution. `ai` with no command prints execution cards as JSON.

Create tasks only when the user asks or active instructions permit automatic
task creation. Start workers only when the user has authorized delegated work.

## Select the correct data

- Run commands from the target repository. Task commands infer the workspace
  and project from the current directory. Execution uses the project assigned
  to the current Git repository.
- Use `ai task doctor` to check task configuration, data, and project routing.
  Use `ai doctor` to check worker dependencies and the Herdr connection.
- Use the same `--data-dir PATH` or `--db FILE` on each command, or configure
  one shared database path. Choose one of these flags, not both.
- `--workspace NAME_OR_KEY` selects task data. It does **not** limit execution
  commands.
- Run `ai --help`, `ai task --help`, or `ai <command> --help` to check commands
  and options before using an unfamiliar operation.

## Find and inspect tasks

```sh
ai task list --ready
ai task list --open --project app --label bug
ai task list --blocked
ai task search --project app "auth bug"
ai task context APP-7KQ9
ai task show APP-7KQ9 --full
```

- Use `list --ready` to choose manual work. It excludes blocked tasks and epics;
  it is not the execution eligibility check.
- Read `context TASK_REF` before work. Use `show TASK_REF --full` when you need
  all details, including metadata.
- Search includes done and canceled tasks. Add `--all` to include deleted tasks.
- Use `--limit` to bound large lists. Use `--json` on task commands that support
  it when you need structured output. Execution inspection commands return JSON.
- Use the task refs printed by the CLI, preferably qualified refs such as
  `APP-7KQ9`. The project prefix can change. If a suffix is ambiguous, use a
  longer suffix. Keep local task refs out of commits, PRs, and external systems.

## Update tasks and save handoff notes

For manual work:

```sh
ai task edit APP-7KQ9 --status active
ai task note APP-7KQ9 --stdin <<'EOF'
Implemented the parser. Tests pass. The migration guide still needs an update.
EOF
ai task edit APP-7KQ9 --status done
```

- Set `active` when work starts. Set `done` only when work and required checks
  are complete. Let the execution system complete worker-owned tasks.
- Use notes to record decisions, blockers, test results, and remaining work.
- Check dependencies and conflicts before changing status or task order.
- Preview broad changes with `ai task bulk-update ... --dry-run`.
- `ai task delete TASK_REF` is a soft delete. Use `ai task restore TASK_REF`
  to recover the task.

## Create tasks

```sh
ai task add "Fix the login error" --project app --status todo \
  --priority high --label bug --description-stdin <<'EOF'
Fix the login error without changing the password reset flow.

Acceptance criteria:
- Add a regression test for the login error.
- Run the affected tests and record their results.
EOF
```

- Include scope, acceptance criteria, and required tests. Record known facts;
  do not invent missing requirements. Report the returned task ref.
- Tasks default to `inbox`. Other statuses are `backlog`, `todo`, `active`,
  `done`, and `canceled`. Priorities are `none`, `low`, `medium`, `high`, and
  `urgent`.
- Use `--description-stdin` or `--description-file` for long descriptions.
  Use `note --stdin` or `note --file` for long notes.
- Keep secrets out of task fields, notes, attachments, and logs.

For dependencies, epics, related links, scheduling, recurring tasks, metadata,
attachments, safe text edits, or sync conflicts, run `ai task skill` to read the
installed task guide. Then check the relevant subcommand with `--help`.
Use the text hash guard for existing long text. Inspect each conflict before
choosing a value. Before an import or backup restore, make and verify a backup;
these operations replace local data.

## Start an authorized execution run

1. Check the project path. If setup is needed, create a project with
   `ai task project create app --path .`, or assign an existing project with
   `ai task project path add PROJECT .`.
2. Put acceptance criteria and required tests in each task description. The
   worker runs these tests. The supervisor checks result evidence, commits,
   and merge safety; it does not run a separate test command.
3. Run `ai doctor`. Workers need Pi with a configured model provider, the
   required workmux fork, and a Herdr session with `HERDR_SOCKET_PATH` set.
4. Run `ai run start --dry-run` from the assigned Git repository. Check the
   returned task list. Eligible tasks need an `Open` execution card, satisfied
   dependencies, and a nonempty description. Task status and execution card
   columns are separate.
5. Run `ai run start --until-idle`. It ends when no eligible task remains.
   A run can become `blocked` if incomplete tasks remain; an idle run does not
   prove that all work is complete.

Workers use separate worktrees. Attempts start from `ai/integration`. If that
branch is absent, execution creates it from the primary worktree's `HEAD`.
An existing branch is not reset. Keep `ai/integration` unchecked out in all
worktrees so the execution system can update it safely. The current branch
stays unchanged. A merge into `main` is a separate operation.

## Inspect and control execution

```sh
ai status
ai run list
ai attempts
ai attempt show ATTEMPT_ID
ai attempt logs ATTEMPT_ID --follow
```

Use run IDs from `ai run list` and attempt IDs from `ai attempts`. Neither is
a task ref. Use these controls as needed, not as a command sequence:

| Command | Effect |
| --- | --- |
| `ai run pause RUN_ID` | Stops new task selection; active workers continue. |
| `ai run resume RUN_ID` | Resumes a paused run. |
| `ai run stop RUN_ID` | Stops new selection and lets the current attempt finish. |
| `ai attempt open ATTEMPT_ID` | Focuses the existing worker terminal without restarting it. |
| `ai attempt stop ATTEMPT_ID` | Stops the worker; keeps its logs and worktree. |
| `ai attempt retry ATTEMPT_ID` | Authorizes one more attempt for a blocked task; does not start a run. |

Inspect the failure before retry. Stop an owned worker before retrying it.
A task permits at most two attempts. After retry authorization, resume a paused
run or start a new run if the previous run is blocked or stopped.
`Ctrl-C` during log viewing stops the viewer, not the worker.

## View boards

- `ai board`: terminal execution board.
- `ai web`: local web execution board. Use the printed URL and access token;
  keep the token private.
- `ai task tui`: task management UI, not the execution board.
- `ai task demo`: disposable sample tasks, discarded on exit.
