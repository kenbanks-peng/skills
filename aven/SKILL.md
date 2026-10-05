---
name: aven
description: >-
  `aven` is a local-first task manager. Use it to find and inspect work, maintain task state, create follow-up tasks, manage dependencies, optionally group work into epics, and leave durable handoff context.
---

If the user gives instructions to use tasks (rather than todos):

1. Run `aven skill` and read its output for detailed instructions.
2. If `.aven/tasks.db` does not exist, run `aven --db .aven/tasks.db project create <project> --path .` where <project> corresponds to the project root folder name.
3. Run every Aven CLI command involving the database from the target project's root directory with the option `--db .aven/tasks.db`.

## Optional grouping with epics

Use epics when related tasks benefit from a shared grouping; standalone tasks need no epic.

- Create an epic: `aven --db .aven/tasks.db add "Epic title" --epic`.
- Add a task: `aven --db .aven/tasks.db epic add <child-ref> <epic-ref>`.
- Inspect its tasks: `aven --db .aven/tasks.db epic list <epic-ref>`.
- Remove membership: `aven --db .aven/tasks.db epic remove <child-ref> <epic-ref>`.

Use the refs printed by Aven. `aven --db .aven/tasks.db list --ready` excludes epics; choose executable work from their child tasks.

## Dependency management

Use dependencies when one task must wait for another. The argument order is **blocked task first, blocker second**: `aven --db .aven/tasks.db dep add A B` means A depends on B.

- Add a dependency: `aven --db .aven/tasks.db dep add <blocked-ref> <blocker-ref>`.
- Inspect blockers and dependents: `aven --db .aven/tasks.db dep list <task-ref>`.
- Remove a dependency: `aven --db .aven/tasks.db dep remove <blocked-ref> <blocker-ref>`.
- Find blocked work: `aven --db .aven/tasks.db list --blocked`.
- Find ready work: `aven --db .aven/tasks.db list --ready`, which excludes blocked tasks.

Inspect dependencies before changing task status or execution order. Remove a dependency when the prerequisite relationship no longer applies; complete finished prerequisites through their task status.
