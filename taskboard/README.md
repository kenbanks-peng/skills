# Taskboard

A workflow skill for tracking software work in Doska. Start at [SKILL.md](SKILL.md).

The skill creates a project board once, saves its reference in `.taskboard/settings.md`, and reuses it in later sessions. It defines card content, execution, verification, and handoffs; Doska's live MCP server supplies tool documentation.

`SKILL.md` contains the workflow and card template. Read [project-board setup and recovery](references/project-board.md) when settings are missing or unusable; ordinary execution with an existing board does not need that reference.

## Maintenance

Validate changes against [regression scenarios](references/scenarios.md). These are maintainer checks, not steps in task execution. Report static walkthroughs separately from executed agent tests.
