# Authorized worker merge

Attempt one merge with the supplied task ref, local base branch, and required checks. Reconcile a failed attempt before retrying.

## Preconditions

1. Confirm you are in the assigned worker worktree on its branch, with all intended changes committed and no unrelated uncommitted changes. If not, stop and report to dispatch.
2. Read `branch.<worker-branch>.workmux-base` from local Git config. Require it to equal the recorded base and require `refs/heads/<base>` to exist. Missing or mismatched configuration is a blocker; there is no default target.
3. Confirm there is no unfinished merge/rebase. Preserve any existing operation and ask dispatch to reconcile it rather than starting another.

## Rebase and check

1. Rebase onto the explicit local `refs/heads/<base>` before running checks and Workmux integration.
2. For conflicts, inspect both sides and the relevant base history. Preserve both intended behaviors. Continue only when the resolution is understood; report ambiguous conflicts for guidance.
3. Run the required checks after rebasing. Record the resulting worker commit with `git rev-parse HEAD`.
4. Execute checks and the merge they gate in fail-fast Bash blocks beginning with `set -euo pipefail`. A failing check must prevent the merge command and any success note.

## Merge and report

1. Run `workmux merge --rebase --into <base> --keep` from the worker worktree after substituting the verified base. Keep hooks enabled. Dispatch handles user notification and cleanup.
2. After the merge succeeds, run `sleep 2` before reading refs or checking ancestry. Require the worker HEAD to equal the captured, checked post-rebase commit, then confirm that commit is an ancestor of `refs/heads/<base>` and record the resulting base revision. Run these assertions once; on failure, stop and report. If Workmux rewrote the worker commit, report that integration succeeded but the checked SHA changed; dispatch must reconcile and validate the integrated revision before closure.
3. Append `MERGE: merged worker <SHA> into <base> at <SHA>; awaiting dispatch verification.` Follow the `tasks` selective-note policy: summarize post-rebase check results and commit/ancestry assertions, plus consequential conflict resolutions and their rationale. Reference unchanged launch metadata; omit the routine precondition and command narrative. Use one lead sentence and at most three short bullets, normally under 80 words, with the authorization ID. Use Git-generated unambiguous short SHAs in prose; retain full worker/base SHAs in a linked evidence file for dispatch's verification helpers. Display home paths with `~`.
4. End your turn with the worktree retained and task status/assignment unchanged.

## Failure

On any failed check, rebase, merge, or ancestry assertion, stop and append `BLOCKED:`, leading with the blocker and next action, then a compact recovery summary and evidence-file reference. Retain authorization ID, failed command, working directory, exact error, worker/base refs and full SHAs, Git/common directories, and Workmux/worktree state in that file. For lock failures include lock metadata and owning processes when identifiable; label unknown causes as unknown. Preserve work and potentially live locks. If reporting fails, retain the report locally and alert dispatch before any further action.
