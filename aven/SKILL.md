---
name: aven
description: >-
  `aven` is a local-first task manager. Use it to find and inspect work, maintain task state, create follow-up tasks, manage dependencies, optionally group work into epics, and leave durable handoff context.
---

If the user gives instructions to use tasks (rather than todos):

1. Run `aven skill` and read its output for detailed instructions.
2. If `.aven/tasks.db` does not exist, run `aven --db .aven/tasks.db project create <project> --path .` where <project> corresponds to the project root folder name.
3. Run every Aven CLI command involving the database from the target project's root directory with the option `--db .aven/tasks.db`.

## Guidance

Use the aven --epic option when related tasks benefit from a shared grouping.

Use dependencies when one task must wait for another.
