---
name: tasks
description: Use when the user explicitly requests tasks for Aven task management, or when dispatch needs task records, dependencies, or durable handoffs.
---

# Tasks

Manage work in Aven. This is an independently maintained skill: use `aven <command> --help` for syntax rather than loading the generated `aven skill` primer. The calling workflow decides who may change status and when work is complete.

## Locate and understand

- Run commands from the intended repository; reuse Aven's project inference. Use `aven doctor` when routing is unclear and explicit workspace/project options when needed. Create a project mapping only when missing, using `aven project create <name> --path <path>`.
- Select eligible work with `aven list --ready` and scope filters. Use `aven list --open` for recovery and `aven search` to avoid duplicate tasks; search can find completed work too.
- Read `aven context <task-ref>` before acting. Use `aven show <task-ref> --full` when reviewing reports or decisions that need all notes and metadata.
- Use refs printed by Aven, preferably project-qualified. Keep these local identifiers out of commit messages, PR descriptions, and external systems.

## Shape the work

- Create tasks when requested or authorized by a calling workflow such as dispatch. Include scope, acceptance criteria, and enough rationale for another agent to continue independently.
- Reuse existing tasks. Put selected, actionable work in `todo`, deferred work in `backlog`, and untriaged work in `inbox`.
- Use `aven dep add <blocked> <blocker>` for execution order. Use epics for grouping: `aven add <title> --epic`, then `aven epic add <child> <epic>`. Epic membership does not establish a dependency.
- Prefer epics over grouping labels; create a label before applying it. Inspect dependency/conflict context before changing ordering or status.

## Update and preserve context

- When authorized to start work, use `aven edit <task-ref> --status active --agent <agent-type>`. The agent field identifies a type such as `pi`, not a unique worker; record individual handles in notes.
- Mark work `done` only after the calling workflow's completion criteria pass. Clear assignment with `--clear-agent` when leaving active status.
- Append durable decisions, results, blockers, and next actions with `aven note <task-ref> --file <file>` or `--stdin`. Keep scratch work elsewhere; record new evidence rather than repeating unchanged notes.
- Use `--description-file` or `--description-stdin` for new long descriptions. For existing descriptions that may be edited concurrently, inspect `aven text --help` and use the hash-checked text update workflow.
- Use `aven bulk-update --help` and a dry run before broad mutations. Inspect sync conflicts before resolving them; preserve uncertain variants for review.
- Keep secrets out of task records. If a write fails, retain the intended report locally, report the failure, and restore the durable record before claiming the transition succeeded.

## Less common operations

For scheduling, recurrence, attachments, moves, or conflict resolution, consult the relevant subcommand's `--help` only when needed. Use human-readable output interactively and `--json` when a script needs structured data. This skill defines task mechanics; dispatch-specific note prefixes, worker authority, merge gates, and cleanup rules belong to `dispatch`.
