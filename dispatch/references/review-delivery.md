# Review, checks, and delivery

## Review and corrections

Wait for the implementation turn to end and any queued writing to finish.
Workers must end without background writers. Record the candidate HEAD and
pending diff. Review independently: the dispatcher can review a small change;
use a read-only agent for substantial changes. Run review without a window or
in a verified hidden window; review is not an exception to the visibility rule.

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

Run checks through the agent's execution tool without creating a terminal
window. Set the checkout as cwd and save output, exit status, and candidate
identity outside disposable worktrees. Run the actual project checks as well
as diff --check. Use the required host: Linux checks must execute on Linux.

```sh
(cd "$WORKTREE" && env GIT_PAGER=cat PAGER=cat git --no-pager diff --check) > "$LOG" 2>&1
check_exit=$?
printf '\nexit_code=%s\n' "$check_exit" >> "$LOG"
```

If a native terminal is required, first confirm a supported method that keeps
it hidden from creation. Reuse one hidden checks shell per checkout where
possible. `run` requires OSC 133; if unavailable, return to windowless execution
or record a blocker. Do not open a visible command pane as a fallback.
`--no-focus` only prevents focus changes; it does not hide a window.
Do not assume a detached session or another workspace makes windows invisible.
Save results and close hidden command windows after success or failure.

Do not use a pager for noninteractive Git. Do not modify global Git settings
to repair a missing pager. Check-generated files belong in the task checkout;
handle them according to repository conventions before delivery.

## Local delivery

Use ship commit as the normal commit operation. Dedicated task worktrees make
its inclusion of all nonignored changes useful, not a reason to avoid it.
Review scope and checks once at the candidate, then deliver. Execute ship
through the windowless tool, not a merge terminal. Confirm that the installed
ship path does not create visible helper windows; if it does, use supported
hidden execution or record the delivery blocker before running it:

```sh
tuios ship commit -s "$SESSION" -w "$PANE" -m "$COMMIT_MESSAGE"
tuios ship merge -s "$SESSION" -w "$PANE" --into "$TARGET" --squash -m "$COMMIT_MESSAGE"
```

Use --ff-only instead of --squash when the plan calls for fast-forward delivery.
Use the worker's full pane ID and recorded target, not focus. The candidate
must be at rest; the target checkout must be ready for integration. Let native
ship enforce its commit/merge preconditions. Resolve conflicts in the task
branch, then recheck; do not switch policies just to make a merge pass.

Save source/target SHAs and run integrated checks without visible windows.
Apply the same rule to conflict repair, Git commands, and delivery retries.
For remote candidates, link the Linux check evidence to the pulled local candidate. Observe existing CI
with `tuios ship status -s "$SESSION" -w "$PANE" --json`.
Do not initiate push/PR approval. Mark tasks done only after acceptance passes.
