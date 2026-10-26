# Worker contract

Dispatch owns scheduling, task status/assignment, integration, and cleanup. Workers must not spawn workers or perform those lifecycle actions.

1. Use the supplied task context. Refresh with `aven context <task-ref>` only if context is missing, materially inconsistent, or dispatch requests it. Validate the assigned branch and base before editing; report inconsistencies. Work in your actual current worktree (host paths are not worker paths). Follow the task requirements and preserve unrelated changes.
2. Implement, run required checks in fail-fast Bash blocks beginning `set -euo pipefail`, review the actual diff, and commit only intended changes.
3. Use `tasks` for durable Aven reporting. After required checks pass, append `RESULT:` with delivered changes, a Git-generated unambiguous commit SHA, check outcomes, and material decisions/exceptions. Reference detailed evidence and explicitly identify unavailable/skipped checks. On failure, append `BLOCKED:` with blocker and next action, failed command, cwd, observed error, and retained recovery work. If Aven is unavailable, retain the report locally and alert dispatch; restore it durably before integration.
4. Stop after reporting. Resume repairs only when instructed; commit the repair and append a new report.
