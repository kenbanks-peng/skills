Task reference: SKL-BYB5
Evidence directory: /Users/kenbanks/Software/Public/skills/dispatch/.ralph/run.6sZzDO/SKL-BYB5

Complete only the assigned Aven task. Use its reference as `<ref>`. Do not select another task.

1. Read the tasks skill and run `aven context <ref>`.
2. Implement the task and verify every acceptance criterion with the required checks.
3. Commit the task changes. Include the task reference in the commit message.
4. Append a concise handoff with `aven note <ref> --file <file>`: outcome, key decisions, check results, blockers, and next steps. Include essential evidence in the note or link durable evidence.
5. Only when every acceptance criterion passes and the note is saved, mark complete:
   `aven edit <ref> --status done --clear-agent`

After marking the task done, report the outcome and exit.

Fix check failures before declaring the task blocked. Run local and isolated checks with the same commands and relative working directory. Do not skip or weaken checks.

If a check failure remains and you need a fresh worker, save the handoff and failure evidence in the evidence directory. Include the exact check commands, working directory, and output. Write `repair-request.json` there with exactly:
`{"reason":"check_failure"}`
Leave the task active and exit. Ralph permits only one fresh repair attempt.

Never request repair for missing approval, credentials, unclear requirements, safety blockers, or failed commit or Aven commands. For these blockers, record why if possible, leave the task active for review, and exit. Do not retry indefinitely or mark incomplete work done.

This is explicit recovery of an active task, not a new assignment.
Read the Aven context and handoff notes before making changes.
Inspect prior evidence under /Users/kenbanks/Software/Public/skills/dispatch/.ralph; match tasks using each ref file.
Preserve prior evidence and existing changes. Resume from observed state; do not repeat completed work.
Recheck prior blockers. Do not bypass approvals, safety checks, or acceptance criteria.
