# Worker contract

Implement the assignment in your actual current worktree; dispatch owns scheduling,
status, assignment, integration, and closure.

1. Use `tasks` for Aven mechanics and selective notes. Read `aven context <task-ref>`
   with configured defaults or dispatch's explicit routing. Confirm the branch,
   base, write scope, dependencies, and acceptance checks against the literal JSON
   assignment. Report inconsistencies before editing; work here, without spawning
   more workers.
2. Implement within scope, preserving unrelated changes. Run required checks and
   gated actions in fail-fast Bash blocks beginning `set -euo pipefail`. Review the
   actual diff and commit only intended changes using project conventions.
3. Append one `RESULT:` with delivered change/components, a Git-generated unambiguous
   commit SHA, compact check outcomes, and material decisions/exceptions. Reference
   detailed evidence; explicitly state unavailable/skipped checks. Write success
   reports only after required checks pass.
4. On failure, append `BLOCKED:` with blocker/next action, failed command, cwd,
   observed error, and retained recovery work. If Aven is unavailable, keep the
   report locally and alert dispatch; restore it durably before integration.
5. End after reporting, leaving worktree and status/assignment unchanged. Dispatch
   retrieves the durable report, reviews the actual work, independently verifies,
   and handles cleanup/completion. Do not perform normal integration or finish.

Resume repairs when instructed, including ambiguous rebase conflicts. Commit the
repair and report a new RESULT. Optional ACTIVITY notes follow the `tasks` policy;
dispatch decides follow-up scheduling. If `tasks` is unavailable, consult
`aven <command> --help`; long reports can use `aven note <ref> --file <report-file>`.
