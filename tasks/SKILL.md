---
name: tasks
description: Use when the user or a calling workflow needs Aven task management, dependencies, or durable handoffs.
---

# Tasks

Use Aven as the durable work record. The user or calling workflow controls assignment and completion. Consult `aven <command> --help` for unfamiliar syntax.

## Find the work

- Run from the target repository using configured database/workspace defaults and project inference. Create project mappings only when missing.
- Search before creating tasks. Use `list --ready` for eligible work, `list --open` for recovery, and project filters to bound scope.
- Read `context <ref>` before acting; use `show <ref> --full` when reviewing complete notes and metadata. Use Aven-provided refs.

## Shape and track

- Give each task a scope, acceptance criteria, and enough rationale to resume independently. Use `inbox` for untriaged work, `todo` for selected work, and `backlog` for deferred work.
- Express ordering with `dep add <blocked> <blocker>`. Use epics for grouping; membership does not establish a dependency. Check dependencies before changing status or order.
- When authorized, start with `edit <ref> --status active --agent <type>`. The agent field identifies an agent type, not an individual session. Mark `done` only after the user or calling workflow's completion criteria pass; clear assignment with `--clear-agent` when leaving active status.

## Leave a usable handoff

- Append new decisions, results, check evidence, blockers, and next actions with `note <ref> --file <file>` or `--stdin`. Keep secrets and scratch logs out; reference existing evidence instead of repeating it.
- Pass long text through files or stdin, not shell interpolation. For concurrent description edits, use `aven text` hash-checked updates. Dry-run bulk changes; preserve unresolved conflict variants.
- If a write fails, retain the report locally and surface the failure. Restore the durable record before claiming the transition succeeded.
