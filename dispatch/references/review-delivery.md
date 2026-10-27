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

Use checks.py for candidate checks, repairs, competing attempts, and integrated
checks without visible windows. Select the project commands once in a check
plan, then use the same plan after repairs. See [script procedures](automation.md).

```sh
python3 "$skill/scripts/checks.py" --plan "$PLAN" --cwd "$WORKTREE" --output "$run_dir/checks-1" --require-system Linux
```

Use Darwin only when macOS execution is authorized. Linux acceptance must run
on Linux. Preserve its result when pulling a candidate. Each attempt gets a new
output directory outside checkouts. Read result.json and logs; failed, timed
out, or checkout-changing commands do not pass. Do not type checks into panes.
--no-focus does not hide a window. A detached session is not proof of hiding.
If a required check cannot run windowlessly, record the exact blocker instead
of opening a visible command pane.

Do not use a pager for noninteractive Git. Do not modify global Git settings
to repair a missing pager. Check-generated files belong in the task checkout;
handle them according to repository conventions before delivery.

## Local delivery

After checks and independent review, use deliver.py. It is the normal path for
native ship commit/merge and integrated checks. Do not reproduce its operations
manually. Set the recorded target and merge policy; never choose a policy only
to make a merge pass.

```sh
python3 "$skill/scripts/deliver.py" --run-dir "$run_dir" --session "$SESSION" --window "$PANE" --cwd "$WORKTREE" --target-repo "$REPO" --into "$TARGET" --policy squash --message "$COMMIT_MESSAGE" --checks "$run_dir/checks-1/result.json" --integration-plan "$PLAN" --output "$run_dir/delivery-1" --reviewed
```

Use ff-only when required. The script refuses stale checks, unreviewed changes,
active/queued workers, wrong pane/checkouts, and dirty targets. Source worktrees
must be dedicated to the task: ship commit includes all nonignored changes.
Resolve conflicts in the task branch; recheck and review before a new delivery.

Read the saved delivery result. A pending native step is uncertain, not a reason
to repeat it. Reconcile native ship status and Git history first. The journal
records source/target commits, native responses, and integrated check results.
Do not mark done when the target merged but integrated checks failed.
Keep remote Linux evidence linked to the local candidate and its local checks.
Observe existing CI with tuios ship status. No push/PR approval is initiated.
