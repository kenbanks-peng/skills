# Review, checks, and delivery

## Review and corrections

Wait for the implementation turn to end and any queued writing to finish.
Workers must end without background writers. Record the candidate HEAD and
pending diff. Review independently: the dispatcher can review a small change;
use a read-only agent for substantial changes.

```sh
tuios review -s "$SESSION" -w "$PANE" --stat
tuios review -s "$SESSION" -w "$PANE"
tuios review note -s "$SESSION" -w "$PANE" src/client.go:42 'Record the retry attempt here.'
tuios review notes -s "$SESSION" -w "$PANE"
tuios review send -s "$SESSION" -w "$PANE"
```

Use actual changed lines, not the sample path. review send queues unsent notes;
do not also queue those corrections. Wait for the correction, review it, and
rerun affected checks. Large diffs may be truncated: use bounded path views.
Remote candidates must be pulled locally for native review.

## Checkpoints

Use native turn checkpoints to inspect and recover an unsuccessful attempt.

```sh
tuios checkpoint list -s "$SESSION" -w "$PANE" --json
tuios checkpoint diff -s "$SESSION" -w "$PANE" "$TURN"
tuios checkpoint restore -s "$SESSION" -w "$PANE" "$GOOD_TURN"
```

Restore only while the worker and its queue cannot restart writing. Save the
current evidence first. Native restore makes a safety checkpoint. Inspect the
restored diff and rerun checks. Checkpoints omit ignored/oversized files and
are removed with the worktree; preserve useful evidence before cleanup.

## Checks without pane debris

Use one reusable checks shell per active checkout when shell integration is
available. Name and record it once. Use run to execute commands and return
their output/status:

```sh
tuios run -s "$SESSION" -w "$CHECK_PANE" --timeout 600000 --json -- 'env GIT_PAGER=cat PAGER=cat git --no-pager diff --check'
```

Run refuses a shell without OSC 133; it types nothing in that case. Use a
bounded command pane instead, then close it after saving the log:

```sh
tuios new-window -s "$SESSION" checks --cwd "$WORKTREE" --no-focus --grants none --keep-open --wait -- sh -c 'export GIT_PAGER=cat PAGER=cat; git --no-pager diff --check'
check_exit=$?
tuios capture-pane -s "$SESSION" -w checks --scrollback --lines 0 > "$LOG"
tuios close-window -s "$SESSION" checks
```

Only use the name checks after confirming that no unrelated pane has that name.
Save the exit code with the log and candidate identity. Use the actual project
checks as well as diff --check. Close failed command panes too, after saving
their diagnostics; do not open check-1b/check-1c beside abandoned failures.
Without --keep-open, a command pane closes on exit; write its log from the
command when that is the better choice. new-window --wait returns the command's
status, while wait-for window-exit reports wait success: read its exit_code.

Do not use a pager for noninteractive Git. Do not modify global Git settings
to repair a missing pager. Check-generated files belong in the task checkout;
handle them according to repository conventions before delivery.

## Local delivery

Use ship commit as the normal commit operation. Dedicated task worktrees make
its inclusion of all nonignored changes useful, not a reason to avoid it.
Review scope and checks once at the candidate, then deliver:

```sh
tuios ship commit -s "$SESSION" -w "$PANE" -m "$COMMIT_MESSAGE"
tuios ship merge -s "$SESSION" -w "$PANE" --into "$TARGET" --squash -m "$COMMIT_MESSAGE"
```

Use --ff-only instead of --squash when the plan calls for fast-forward delivery.
Use the worker's full pane ID and recorded target, not focus. The candidate
must be at rest; the target checkout must be ready for integration. Let native
ship enforce its commit/merge preconditions. Resolve conflicts in the task
branch, then recheck; do not switch policies just to make a merge pass.

Save source/target SHAs and run integrated checks. For remote candidates, link
the Linux check evidence to the pulled local candidate. Observe existing CI
with `tuios ship status -s "$SESSION" -w "$PANE" --json`.
Do not initiate push/PR approval. Mark tasks done only after acceptance passes.
