# Establish the project board

1. Create a project-named doska task board and save the returned ID in `.taskboard/settings.md`:

```yaml
---
board_id: "<board ID>"
---
```

2. Establish these columns in order, reusing suitable defaults: Backlog, Ready, WIP, Review, Done, Blocked. Mark Done as the board's done column. The orchestrator manages Ready using the [readiness and dependency rules](orchestrator.md#readiness-and-dependencies).
