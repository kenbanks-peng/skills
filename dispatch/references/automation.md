# Script procedures

Use these scripts through the execution tool, not through a new terminal.
Set skill to the installed skill directory. Use an absolute run_dir outside all
task and target checkouts. Use a fresh directory for init.
Python 3.10+ on Linux or macOS is required. No Python packages are needed.

## Start and record ownership

Before launch, save the inventory and protect the existing dispatch pane:

```sh
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" init --repo "$REPO" --session "$TUIOS_SESSION" --dispatch "$TUIOS_PANE_ID"
```

The server route is saved from TUIOS_SERVER. Supply --server NAME only for a
different named server. Keep the saved route for the run.
Init fails if any configured host is unavailable or a required schema is unknown.

After each permitted launch, register its full returned UUID and session address:

```sh
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" register --session "$SESSION" --window "$PANE" --role linux-worker --system Linux
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" audit
```

Use role aven for a run-owned Aven window. Use --system Linux for workers
started with linux container; the flag records the launcher's contract.
Use HOST:SESSION for remote windows. Register each view once.
A pre-existing unrelated window cannot be adopted or closed. If an unrelated
window appears later, use exclude with its exact --session and --window.
Register starter and helper panes as role auxiliary so cleanup owns them.
Audit tracks ownership during execution and dispatch-only inventory at run end.
To close one finished resource during a run, use workspace.py --run-dir DIR
close --session SESSION --window UUID --evidence-saved after saving its result.

## Checks

Write one JSON plan from the project's acceptance commands:

```json
[
  {"name": "unit", "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"], "timeout_s": 300},
  {"name": "diff", "argv": ["git", "--no-pager", "diff", "--check"], "timeout_s": 30}
]
```

Run on the required host before review acceptance, after repairs, and after
integration. Use a new output directory for each attempt:

```sh
python3 "$skill/scripts/checks.py" --plan "$PLAN" --cwd "$WORKTREE" --output "$run_dir/checks-1" --require-system Linux
```

Run worker acceptance checks through linux container, with paths valid there.
Use Darwin for additional local delivery checks on macOS. Keep both results.
Check-generated source changes invalidate passing evidence; inspect them and
rerun checks. Keep result.json as generated evidence.
The plan runs in order, logs each command, and returns failure if any command
fails, times out, cannot start, or changes the checkout. Completed commands
must finish their background processes. Scripts create no terminal windows.
Choose noninteractive check commands: a project command can itself open a UI.

## Follow-ups and status

Use workspace.py queue with a stable follow-up ID and prompt file; see
[coordination](coordination.md). It records submission once, not task completion.
After a native event or meaningful outcome, use workspace status, then
dashboard.py observe/report as described in [dashboard](dashboard.md).
Use fresh native observations for agent states.

## Delivery

After independent review, with workers and queues at rest, deliver the exact
checked local candidate. Use a new output directory. Select the recorded policy:

```sh
python3 "$skill/scripts/deliver.py" --run-dir "$run_dir" --session "$SESSION" --window "$PANE" --cwd "$WORKTREE" --target-repo "$REPO" --into "$TARGET" --policy squash --message "$COMMIT_MESSAGE" --checks "$run_dir/checks-1/result.json" --integration-plan "$PLAN" --output "$run_dir/delivery-1" --reviewed
```

Use ff-only when planned. Local delivery needs local candidate check evidence.
Keep Linux acceptance evidence separately from local delivery evidence.
The script checks ownership, checkout identity, unchanged check evidence, review
confirmation, native rest state, empty queue, and clean target. It runs native
ship commit when needed, ship merge, and target checks. Native refusals stop it.
No push or PR is initiated. Review acceptance remains the agent's decision.

Read result.json after every failure or interruption. A pending ship step has
an uncertain effect. Reconcile Git and native state and the original journal
before choosing the next delivery operation.
A merged target with failed checks is not a completed delivery.

## Finish or resume

On resume, reuse run_dir. Run status before any mutation; reconcile pending
events and native queues. Keep the original evidence and journals.
Before every run end, save outcomes, stop background writers and pending queues,
then close owned windows and verify the final inventory:

```sh
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" cleanup --evidence-saved
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" audit --final
```

Cleanup saves pane logs and closes only registered, idle resources by full ID.
It keeps dispatch and unrelated baseline/excluded windows. It refuses active,
unknown, needs_input, or queued workers. Resolve prompts and pending queues
through native controls, then rerun cleanup with the same
directory; already absent windows are not closed again.
Keep worktrees or stashes on disk when needed. Worktree removal and container
shutdown still need their native tools and an explicit disposition.

Exit codes: 0 = success, 1 = failed check/audit or incomplete operation,
2 = invalid input, blocked precondition, or unsupported capability. Read the
saved result and stderr to determine the operation's actual outcome.
