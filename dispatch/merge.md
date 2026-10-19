# Authorized worker merge

Dispatch sends this procedure with the task ref, recorded local base branch, and required checks. It authorizes one merge attempt; a failed attempt needs reconciliation before retrying.

## Preconditions

1. Confirm you are in the assigned worker worktree on its branch, with all intended changes committed and no unrelated uncommitted changes. If not, stop and report to dispatch.
2. Read `branch.<worker-branch>.workmux-base` from local Git config. Require it to equal the recorded base and require `refs/heads/<base>` to exist. Missing or mismatched configuration is a blocker; there is no default target.
3. Confirm there is no unfinished merge/rebase. Preserve any existing operation and ask dispatch to reconcile it rather than starting another.

## Rebase and check

1. Rebase onto the explicit local `refs/heads/<base>`; this workflow integrates local work, not a fetched remote branch. Rebase separately so the required checks run on the rebased result before Workmux integrates it; Workmux's pre-merge hooks run before its internal rebase.
2. For conflicts, inspect both sides and the relevant base history. Preserve both intended behaviors. Continue only when the resolution is understood; report ambiguous conflicts for guidance.
3. Run the required checks after rebasing. Record the resulting worker commit with `git rev-parse HEAD`.
4. Execute checks and the merge they gate in fail-fast Bash blocks beginning with `set -euo pipefail`. A failing check must prevent the merge command and any success note.

## Merge and report

1. Run `workmux merge --rebase --into <base> --keep` from the worker worktree after substituting the verified base. Explicit `--rebase` overrides the configured merge strategy and preserves commit ancestry. Keep hooks enabled. Dispatch handles user notification and cleanup.
2. After the merge succeeds, run `sleep 2` before reading refs or checking ancestry, allowing host-side ref updates to become visible through the sandbox's shared filesystem. Require the worker HEAD to equal the captured, checked post-rebase commit, then confirm that commit is an ancestor of `refs/heads/<base>` and record the resulting base revision. Run these assertions once; on failure, stop and report. If Workmux rewrote the worker commit, report that integration succeeded but the checked SHA changed; dispatch must reconcile and validate the integrated revision before closure.
3. Append `MERGE: merged worker <SHA> into <base> at <SHA>; <worker checks>; awaiting dispatch verification.` Obtain displayed short SHAs from Git.
4. End your turn with the worktree retained and task status/assignment unchanged. Dispatch independently checks the base before closure.

## Failure

On any failed check, rebase, merge, or ancestry assertion, stop and append `BLOCKED`: failed command, working directory, error, worker/base refs and SHAs, Git/common directories, and Workmux/worktree state. For lock failures include lock metadata and owning processes when identifiable; label unknown causes as unknown. Preserve work and potentially live locks. If reporting fails, retain the report locally and alert dispatch before any further action.
