# Review, checks, and delivery

## Review

Wait for implementation and queued writes to finish. Record the candidate HEAD
and diff. Review independently in the dispatcher or launch a Linux reviewer
with the [worker procedure](workers.md).

```sh
tuios review -s "$SESSION" -w "$PANE" --stat
tuios review -s "$SESSION" -w "$PANE"
tuios review note -s "$SESSION" -w "$PANE" src/client.go:42 'Record the retry attempt here.'
tuios review send -s "$SESSION" -w "$PANE"
```

Use actual changed paths and lines. Send each correction through one channel.
Wait for the repair, inspect it, and repeat affected checks.

## Checkpoints

Use native checkpoints when the harness integration provides them.

```sh
tuios checkpoint list -s "$SESSION" -w "$PANE" --json
tuios checkpoint diff -s "$SESSION" -w "$PANE" "$TURN"
tuios checkpoint restore -s "$SESSION" -w "$PANE" "$GOOD_TURN"
```

Save current work and stop writers before restore. Review the restored diff
and rerun checks. Preserve useful checkpoint evidence outside disposable trees.

## Checks

Run acceptance checks in the worker's Linux environment. Make the script and
plan available inside that environment. Use a new output directory per attempt.

```sh
python3 "$skill/scripts/checks.py" --plan "$PLAN" --cwd "$WORKTREE" --output "$run_dir/checks-1" --require-system Linux
```

Read result.json and command logs. Inspect check-generated changes and repeat
checks against the resulting candidate. Use noninteractive project commands
and `git --no-pager` for captured Git output.

## Delivery

Use deliver.py for a reviewed local candidate with passing local check evidence.
Keep Linux acceptance evidence linked to that candidate. Use the recorded
integration policy and a fresh delivery output directory.

```sh
python3 "$skill/scripts/deliver.py" --run-dir "$run_dir" --session "$SESSION" --window "$PANE" --cwd "$WORKTREE" --target-repo "$REPO" --into "$TARGET" --policy squash --message "$COMMIT_MESSAGE" --checks "$run_dir/checks-1/result.json" --integration-plan "$PLAN" --output "$run_dir/delivery-1" --reviewed
```

The script checks ownership, checkout identity, evidence freshness, independent
review, resting native state, empty queue, and clean target. It records ship
commit/merge and integrated check results. Use Darwin evidence for the local
delivery step when the dispatcher runs on macOS.
Read result.json after each attempt. Reconcile pending steps against native ship
status and Git history before retrying. Accept delivery after integrated checks
pass. Observe existing CI with tuios ship status.
