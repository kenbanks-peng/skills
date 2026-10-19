Task reference: SKL-BYB5
Evidence directory: /Users/kenbanks/Software/Public/skills/dispatch/.ralph/run.keWTxw/4

Complete only the assigned Aven task. Use its reference as `<ref>`. Do not select another task.

1. Read the tasks skill and run `aven context <ref>`.
2. Implement the task and verify every acceptance criterion with the required checks.
3. Commit the task changes. Include the task reference in the commit message.
4. Append a concise handoff with `aven note <ref> --file <file>`: outcome, key decisions, check results, blockers, and next steps. Include essential evidence in the note or link durable evidence.
5. Only when every acceptance criterion passes and the note is saved, mark complete:
   `aven edit <ref> --status done --clear-agent`

After marking the task done, report the outcome and exit.

If blocked, acceptance remains unverified, or a required commit or Aven command fails, record why if possible, leave the task active for review, and exit. Do not retry indefinitely or mark incomplete work done.
