# Binding checks

Coordinators read this on every start/resume; workers use their supplied assignment.

## Resolve the binding

Use the repository root, or workspace root for non-Git projects. In multi-root workspaces, select the root containing the requested work. Branches and worktrees share a binding.

- **Default:** `.taskboard/settings.md`. Validate `server`, `board_name`, `board_id`, `charter_id`, and `setup_state` together; preserve unrelated fields and notes.
- **Effective:** the user’s explicit board reference, otherwise the default. Store temporary overrides separately, including verified IDs, name changes, charter, and setup progress. Use that identity on cards, handoffs, and pending records. A temporary override need not create a default.
- **Default change:** requires a user request. Verify the target, then read [board setup](board-setup.md) before writing binding fields. Do not transfer the old charter or initialization authority.

Read settings without rewriting them. Support version `1`; preserve unsupported versions or contradictory bindings and ask for resolution. `setup_state: null` identifies an existing board; `complete` means initialization finished. For `planned`, `creating`, or `initializing`, read board setup before further setup operations. Reconcile unknown or inconsistent states.

Missing/incomplete settings require board setup’s main-checkout and shared-journal checks, not immediate creation. A fully specified temporary override can proceed independently.

## Open the board

Use the configured server or sole available Doska connection. If several fit, inspect project context before asking. Resolve tools and pagination from the live MCP server.

1. Open by `board_id`, or exact specified name if direct name addressing is supported. If the API requires an ID, ask for the ID/link. Never list boards, search names, compare repositories, or inspect candidate charters to select one.
2. Verify server/board identity, charter, and lifecycle mapping. Use the saved charter ID, otherwise inspect this board for its charter before creating one. Missing/incomplete policy or authorized initialization requires [board setup](board-setup.md). Preserve existing workflow and completion history.
3. Record verified IDs and name changes in the appropriate store. Default updates require the setup writer protocol. Temporary overrides use a separate record containing project/server/board/charter identity and initialization provenance; leave default fields unchanged. Task state must remain durable on cards or in recovery records.

For unavailable boards, access/persistence failures, or uncertain writes, read [recovery](recovery.md). Retain the binding; replacement requires an explicit decision, even after confirmed deletion.

Return to the coordinator after verifying the binding, charter, and lifecycle, or recording a recovery outcome. Load the work group and reconcile pending records before selecting work; binding checks create no task cards.
