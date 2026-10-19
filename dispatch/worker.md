# Worker contract

Dispatch includes this contract in the worker prompt. You implement the assigned task; dispatch owns scheduling and closure.

## Start

1. Read `aven context <task-ref>` from the assigned repository using configured Aven routing defaults, or explicit overrides supplied by dispatch. Confirm your worktree, branch, assigned write scope, base, and acceptance checks.
2. Use the `tasks` skill for task mechanics. If it is unavailable, use `aven <command> --help`; task reports can be appended with `aven note <task-ref> --file <report-file>`.
3. If context, dependencies, ownership, or acceptance criteria are inconsistent, report the blocker before changing code. Work directly in this worktree rather than dispatching more workers.

## Implement and report

1. Implement within the assigned scope and preserve unrelated changes. Record significant decisions and discovered work on the task; dispatch decides how to schedule follow-ups.
2. Run required checks, review the diff, and commit only intended changes using project conventions. Run checks and gated actions in fail-fast Bash blocks beginning with `set -euo pipefail`; write success reports only after the required checks pass.
3. Append one `RESULT` note following the `tasks` selective-note policy: delivered change and affected components, Git-verified commit SHA, compact acceptance/check results, and material decisions or exceptions. Reference existing task context rather than repeating scope, launch metadata, or routine procedure. State skipped or unavailable checks explicitly as blockers, not passes.
4. On failure, append `BLOCKED` leading with the blocker and next action, followed by the failed command, working directory, observed error, and retained work needed for recovery. If Aven is unavailable, retain the report locally and alert dispatch; restore the durable report before merge.
5. End your turn after reporting. Keep the worktree and leave status/assignment unchanged. Dispatch retrieves results from Aven, not terminal prose.

## Follow-up

Resume repairs when instructed. Merge only after dispatch supplies explicit authorization and the merge procedure. Report every merge result or failure on the task, then leave verification, cleanup, and completion to dispatch.
