# Board setup

Use when no matching project board exists or the user asks to establish a tracking system.

1. **Choose scope.** Default to one board per repository/project, reused across sessions and agents. For cross-repository work, agree the boundary first. Ask only for unresolved scope or policy choices; use the defaults below otherwise.
2. **Create once.** Name the board after the project. Inspect the returned/default columns and reuse them: rename the initial To Do column to Backlog, keep In Progress and Done, then add Ready, Blocked, and Review and arrange them in the skill’s default order. Set Done as the sole native done column. Verify the resulting board before adding work; after partial failure, inspect and finish setup rather than creating a duplicate.
3. **Make status legible.** Suggested colors: Backlog unset, Ready blue, In Progress amber, Blocked rose, Review violet, Done green. Collapse Done if desired; leave active work visible. These are presentation defaults, not status logic.
4. **Write the charter.** Use the charter template in [templates.md](templates.md). Place it first in Backlog by card ordering, titled `[Board] <project> — working agreement`. It is a reference card, not unfinished delivery work; exclude it from workload summaries. Record the repository identity, workflow mapping, writer/claim protocol, review policy, integration target, and project-specific verification commands or links to their authoritative location.
5. **Seed the current request.** Capture the requested outcomes, split only where ownership or acceptance differs, and record dependencies. Move only executable work to Ready. Leave speculative work in Backlog. Assign real deadlines only when established by the user or project.
6. **Verify and report.** Reread the board: correct project, columns ordered, one done column, charter present, current work captured without duplicates. Tell the user which board was created and which defaults were adopted.

Creating a board for actual project tracking is part of this workflow. Drafting or editing this skill alone is not a request to provision a live project board.

## Existing boards

Read the local charter first. Map its columns onto the lifecycle gates rather than imposing names. If the mapping is ambiguous, or changing the done column would reclassify existing cards, ask before migrating. Preserve existing cards, relationships, and completion history.

When multiple coordinators use a board, record non-overlapping work ownership and who may change shared structure. Each active work group needs one agreed writer; overlapping claims require direct coordination. The board is not a distributed locking service.
