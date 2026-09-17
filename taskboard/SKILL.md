---
name: taskboard
description: Set up and operate an agent-owned Doska taskboard when tracking is requested, required by project policy, or project work needs delegation, multiple independently verifiable deliverables, or a cross-session handoff. Use to initialize tracking, decompose tracked work, resume ownership, or reconcile progress. Excludes quick questions, trivial edits, and reviewing or editing the skill itself unless tracking is required.
---

# Taskboard

Use Doska as the durable record of **what needs doing, who owns it, and what proves it is finished**. The user supplies intent, not routine taskboard administration. Keep implementation detail in the repository and link it from cards.

## Entry gate

Use tracking when the user or project requires it, or when work needs delegation, multiple independently verifiable deliverables, or a cross-session handoff. Quick questions, trivial edits, and reviewing or editing this skill do not create a board or card unless tracking is required. A small job explicitly selected for tracking needs only one card.

Choose one entry path; read additional references only when their stated conditions apply. Resolve relative reference paths from this skill’s directory, not the project being tracked.

- **Delegated worker or reviewer:** read [worker entry](references/worker.md) and follow that path instead of coordinator startup. Use the supplied board/card identity and bounded assignment; request missing context from the coordinator. Local settings and board construction are not prerequisites for a fully specified assignment.
- **Coordinator:** read [coordinator procedure](references/coordinator.md) when starting/resuming tracked work or reconciling status. It routes routine binding checks separately from setup, recovery, and delegation. An existing coordination agreement takes precedence over assuming this role.

## Shared guardrails

- **Sources of truth:** `.taskboard/settings.md` binds the project to its default board; the board charter owns shared workflow policy; cards own live task state. Resolve tool names, parameters, pagination, and capabilities from the live MCP server.
- **Board identity:** use the specified board directly. If none is specified, the coordinator follows setup to specify and create one. Board selection never involves searching for candidates. Temporary overrides leave the default binding unchanged.
- **Authority:** delegation transfers execution, not acceptance authority. The coordinator owns card bodies and lifecycle; workers/reviewers report through their assigned checkpoint channel. Respect established ownership and preserve human edits and attachment references.
- **Evidence:** report actual outcomes, including failures and checks not run. Completion requires acceptance, required review, and integration into the agreed target—not merely dispatch or a worker’s success report.
- **Scope:** tracking does not authorize commits, merges, deployment, publishing, destructive/shared-workflow changes, or implementation of unrelated backlog items.

## Maintaining this skill

After changing these procedures, use the [behavioral regression scenarios](references/scenarios.md) to check entry paths, binding isolation, concurrency, and recovery. These are authoring checks, not steps for ordinary taskboard sessions.
