---
name: tasks
description: Use when the user or a calling workflow needs Aven task management, dependencies, or durable handoffs.
---

# Tasks

Use Aven as the durable work record. The user or calling workflow controls assignment and completion. Consult `aven <command> --help` for unfamiliar syntax.

Common commands:

```sh
aven list --ready
aven context <ref>
aven show <ref> --full
aven add "Task title" --status todo
aven add "Epic title" --epic
aven epic add <child-ref> <epic-ref>
aven dep add <blocked-ref> <blocker-ref>
aven edit <ref> --status active --agent <type>
aven note <ref> --file <file>
aven edit <ref> --status done --clear-agent
```

## Workflow rules

- Run from the target repository; use configured database/workspace defaults and project inference.
- Search before creating tasks; read task context before acting. Give new tasks scope, acceptance criteria, and rationale sufficient to resume independently.
- Prefer epics over labels for grouping. Create labels before applying them. Epic membership is not a dependency; dependency arguments are blocked task first, blocker second.
- Check dependencies before changing status or order. The agent field identifies a type, not a session; clear it when leaving active status. Mark `done` only after completion criteria pass.

## Durable handoffs

- Append decisions, check evidence, blockers, and next actions as notes. Use files or stdin for long text; reference evidence rather than copying logs.
- Use `aven text` hash-checked updates for concurrent description edits. Dry-run bulk changes and preserve unresolved conflicts.
- On write failure, retain the report locally and surface the failure; restore the durable record before claiming success.
