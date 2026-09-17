# Routine binding checks

Coordinators read this on each start/resume. Workers and reviewers use their supplied assignment instead. This path opens an existing board without loading construction procedures.

## Resolve the effective binding

Use the repository root, not the current subdirectory or skill installation directory. For a non-Git project, use the workspace project root. In a multi-root workspace, select the root containing the requested work; ask only if scope remains ambiguous. Branches/worktrees reuse the same binding. Repository identity is documentation, not a board-discovery mechanism.

- **Persistent binding:** `.taskboard/settings.md` selects the project default. Treat `server`, `board_name`, `board_id`, `charter_id`, and `setup_state` as one binding; validate them together. Preserve notes and unrelated fields.
- **Effective binding:** an explicit user reference for this request, otherwise the persistent binding. A temporary override is session-scoped: verified IDs, display-name refreshes, charter IDs, and setup progress belong to that override, not the default settings. Use the effective identity on cards, handoffs, and pending records. If no default exists, an explicitly temporary override need not create one.
- Change the default only when the user requests a project-binding change. Verify the target first; never carry the old board’s charter or initialization authority across. Before writing any persistent binding fields, read [board setup](board-setup.md) for the shared claim/journal protocol.

Read existing settings without rewriting them. Supported settings version is `1`; unsupported versions or contradictory bindings remain unresolved: preserve them and ask rather than silently rewriting them. `setup_state: null` denotes a specified existing board; `complete` denotes completed initialization. For `planned`, `creating`, or `initializing`, follow [board setup](board-setup.md) before further setup operations. Unknown or inconsistent states require reconciliation, not guessed repairs.

**Missing/incomplete default settings:** read [board setup](board-setup.md). It checks the main checkout and shared journal before planning creation; missing settings in a worktree do not authorize a new board. A fully specified temporary override can proceed without initializing the default.

## Open the specified board

Resolve tool names, schemas, pagination, and supported operations from live Doska MCP instructions. Use the configured server, otherwise the sole available Doska connection. Inspect project context before asking which of several equally plausible servers to use.

Board selection comes only from the user or settings. Do not list boards, search names, compare repository identities, or inspect candidate charters to choose one.

1. Open the effective board directly by `board_id`, or by its exact specified name if the live API supports direct name addressing. If the API requires an ID and only a name is supplied, ask for that board’s ID/link rather than searching.
2. Verify server/board identity and read its charter and actual lifecycle mapping. Use the saved charter ID where available; otherwise inspect the specified board for its charter before creating anything. If the charter or mapping is missing/incomplete, or initialization is authorized, read [board setup](board-setup.md). Preserve existing workflow and completion history rather than imposing default columns.
3. Record verified IDs or renamed display names in the effective binding’s proper store. Persistent updates require the setup writer protocol; temporary overrides use a separate session record with project/server/board/charter identity and initialization provenance, leaving all default fields unchanged. Ordinary task state must still be durable on cards or in recovery records.

**Unavailable board, access/persistence failure, or uncertain write:** read [recovery](recovery.md). Keep the binding; do not search for a substitute or silently create a replacement. A confirmed deleted board requires an explicit replacement decision.

**Complete when:** exactly one intended board and its charter/lifecycle are verified, with the effective identity recorded, or recovery has established an explicit degraded outcome. Return to the coordinator procedure to load the work group and reconcile any pending records before selecting work. Binding checks do not seed task cards.
