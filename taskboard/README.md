# Taskboard

A workflow skill for tracking software work in Doska. Start at [SKILL.md](SKILL.md).

The skill creates a project board once, saves its reference in `.taskboard/settings.md`, and reuses it in later sessions. It defines card content, execution, verification, and handoffs; Doska's live MCP server supplies tool documentation.

`SKILL.md` contains the happy-path workflow and card template. Read [project-board setup and recovery](references/project-board.md) when settings are missing or unusable, and the relevant section of [alternate paths](references/alternate-paths.md) for delegation, blockers, recovery, or unfinished work. Each branch has a conditional link in the main skill; ordinary execution with an existing board needs neither reference.

## Maintenance

Validate changes against [regression scenarios](references/scenarios.md). These are maintainer checks, not steps in task execution. Report static walkthroughs separately from executed agent tests.
