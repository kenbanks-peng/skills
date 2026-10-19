# Authorized worker merge

Dispatch sends this procedure with the task ref, recorded local base branch, and required checks. It authorizes one merge attempt; a failed attempt needs reconciliation before retrying.

## Preconditions

1. Confirm you are in the assigned worker worktree on its branch, with all intended changes committed and no unrelated uncommitted changes. If not, stop and report to dispatch.
2. Read `branch.<worker-branch>.workmux-base` from local Git config. Require it to equal the recorded base and require `refs/heads/<base>` to exist. Missing or mismatched configuration is a blocker; there is no default target.
3. Confirm there is no unfinished merge/rebase. Preserve any existing operation and ask dispatch to reconcile it rather than starting another.

## Rebase and check

1. Rebase onto the explicit local `refs/heads/<base>`; this workflow integrates local work, not a fetched remote branch.
2. For conflicts, inspect both sides and the relevant base history. Preserve both intended behaviors. Continue only when the resolution is understood; report ambiguous conflicts for guidance.
3. Run the required checks after rebasing. Record the resulting worker commit with `git rev-parse HEAD`.
4. Execute checks and the merge they gate in fail-fast Bash blocks beginning with `set -euo pipefail`. A failing check must prevent the merge command and any success note.

## Merge and report

1. Run `workmux merge --into <base> --keep` from the worker worktree after substituting the verified base. Keep hooks enabled. Dispatch handles user notification and cleanup.
2. After the merge succeeds, run `sleep 2` before reading the base ref or checking ancestry, allowing host-side ref updates to become visible through the sandbox's shared filesystem. Then confirm the captured post-rebase worker commit is an ancestor of `refs/heads/<base>` and record the resulting base revision. Run the check once; on failure, stop and report.
3. Append `MERGE: merged worker <SHA> into <base> at <SHA>; <worker checks>; awaiting dispatch verification.` Obtain displayed short SHAs from Git.
4. End your turn with the worktree retained and task status/assignment unchanged. Dispatch independently checks the base before closure.

## Failure

On any failed check, rebase, merge, or ancestry assertion, stop and append `BLOCKED`: failed command, working directory, error, worker/base refs and SHAs, Git/common directories, and Workmux/worktree state. For lock failures include lock metadata and owning processes when identifiable; label unknown causes as unknown. Preserve work and potentially live locks. If reporting fails, retain the report locally and alert dispatch before any further action.
