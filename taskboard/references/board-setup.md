# Board setup and binding mutations

Coordinators read this when default settings are missing/incomplete, a persistent binding needs updating, initialization is incomplete/authorized, or the charter/lifecycle mapping is missing or needs repair. Routine existing-board access follows [binding](binding.md) instead. Resolve the effective binding there before setup; temporary overrides never mutate default settings or inherit another board’s initialization authority.

Bootstrap missing state yourself; user configuration is optional. Resolve live Doska MCP capabilities before calls. For access/persistence failure or uncertain writes, read [recovery](recovery.md). For charter/column setup, read [workflow](workflow.md); for charter body creation/edits, also read [card writing](card-writing.md). A binding-only update need not load card-authoring references or reconfigure the board.

## 1. Locate and initialize local settings

Use the project root resolved during binding checks. Branches/worktrees reuse the same binding. If settings are absent, inspect the main checkout and shared setup journal below before planning creation. Copy a verified existing binding under the writer protocol; conflicting copies require reconciliation. Missing checkout settings do not authorize a second board.

### Single bootstrap writer

Before initializing or changing a persistent binding, acquire a repository-shared bootstrap claim. For Git, resolve the absolute common Git directory using `git rev-parse --path-format=absolute --git-common-dir`; use `<common-dir>/taskboard/bootstrap.lock/` as an atomic directory-creation claim and `<common-dir>/taskboard/setup.md` as the durable setup journal. These locations are shared across linked worktrees. For a non-Git project, use `.taskboard/bootstrap.lock/` and `.taskboard/setup.md` at the workspace root.

1. Create the parent directory if needed, then atomically create the claim directory (not a create-if-missing operation that also succeeds when it exists) and record the session identity and start time inside it. An existing directory, even without owner metadata, means initialization is unresolved: read available state and coordinate with its writer. Age alone never authorizes deleting or stealing the claim.
2. After acquiring it, reread current/main-checkout settings and the shared journal. Resume an existing binding or uncertain operation rather than treating missing checkout settings as permission to create. Finish a provably interrupted journal-to-settings copy under step 3; for other conflicts, stop binding mutations and reconcile.
3. On every persistent binding update, save the binding fields and each setup-state transition to the shared journal before the checkout settings and before its corresponding remote operation. Use atomic file replacement for each local write. Immediately journal returned IDs before copying them to settings. Record the prior binding fields and intended replacement so an interrupted copy can be distinguished from independent edits: if settings match the recorded prior fields, finish the copy; otherwise reconcile rather than overwrite. Deliberate binding changes must be recorded as such with old and new identities. Uncertain remote creation follows Interrupted creation below.
4. Hold the claim through initialization or recording a blocked outcome. Release only your own claim after durable state is saved; retain the journal so a later worktree can recover the binding even if the original checkout is unavailable. After a crash, reclaim only with confirmed release/stoppage of the prior initializer and review of any uncertain operation.

The local claim coordinates only processes sharing that filesystem. Separate clones or machines must use an explicitly shared binding/initializer agreement; local locking cannot guarantee uniqueness across them. If no shared claim can be acquired, defer new-board creation and binding mutations. Use an existing explicit board under [recovery](recovery.md) where safe. A temporary override does not acquire or modify the default’s bootstrap state; shared-board initialization still requires agreement on its writer.

For the persistent binding, create `.taskboard/` and `.taskboard/settings.md` if missing. A temporary override skips default initialization and records only its own identity. Read before updating; preserve user notes and unknown fields, fill absent fields, and repair only unambiguous invalid values. The file is Markdown with these binding keys in YAML frontmatter:

```markdown
---
version: 1
project: "<project name>"
repository: "<credential-free canonical repository identity>"
server: null
board_name: "<project name>"
board_id: null
charter_id: null
setup_state: null
---

# Taskboard settings

Project-to-board binding. Shared workflow policy lives in the board charter;
live ownership, progress, and handoffs live on cards. Board selection is explicit:
use the specified board, or specify and create one. Never discover a board.
```

- Infer `project` from repository documentation or package metadata; fall back to the repository directory name. If no board is specified in existing settings or by the user, set `board_name` to that name and `setup_state: planned` before creating it. An existing specified name means use that board, not search for candidates.
- Prefer the canonical Git remote for `repository`, normalized so SSH/HTTPS forms identify the same host/path, with credentials, query strings, and trailing `.git` removed. If no remote exists, use a stable local project identity based on the main checkout’s absolute path. Preserve an existing identity; a move or remote change needs reconciliation, not a second board by default.
- `setup_state` is null for a specified existing board, `planned` for a newly specified board awaiting creation, `creating` immediately before the create call, `initializing` after confirmed creation or explicit initialization authorization, and `complete` after verified initialization. Persist each transition; it grants no authority on another board. Preserve it through interruptions and reset it when deliberately changing the binding.
- `server` identifies the actual MCP connection/workspace when several are available, never a secret. Use the configured connection, otherwise the sole available Doska connection. Inspect project context before asking which of several equally plausible servers to use.
- Quote string values with valid YAML escaping. Store opaque IDs exactly as returned. Preserve unsupported settings versions or contradictory bindings and ask rather than silently rewriting them.
- Keep settings suitable for version control, subject to repository policy; sanitize remote credentials and omit tokens and task contents. Do not commit files automatically. Exclude non-Git local lock/journal files and `.taskboard/pending/` through the project’s existing local-ignore mechanism when available; recovery records may be sensitive.

For a requested default-binding change, verify the target first, then replace `server`, `board_name`, `board_id`, `charter_id`, and `setup_state` together under this protocol. Preserve unrelated fields; do not carry old charter IDs or setup authority across. For temporary initialization, persist board-qualified intent separately using the [recovery identity record](recovery.md).

**Complete when:** default settings exist with project identity and board name (or an explicit temporary binding is recorded separately), existing bindings and notes are preserved, and any bootstrap writer is established. If local writes are unavailable, report the constraint and follow recovery.

## 2. Use the specified board or create the newly specified board

Board selection comes only from the user or settings. Do not list boards, search names, compare repository identities, or inspect candidate charters to choose one.

- **Board specified:** open it directly under [binding](binding.md). Record verified IDs and renamed display names in the effective binding’s proper store, using the protocol above for persistent updates. An ad hoc user reference leaves default binding fields unchanged unless the user changes the project binding.
- **No board specified:** choose and save `board_name` with `setup_state: planned` as above. Then set `setup_state: creating`, create that board without searching or asking approval, and immediately save the returned `board_id` and `setup_state: initializing`. If creation explicitly rejects a duplicate name, choose a qualified name from the repository owner/path, persist it, and retry creation; do not adopt the other board.
- **Specified board unavailable:** report the actual not-found, access, or connection error and enter [recovery](recovery.md). Keep the binding; do not search for a substitute or silently create a replacement. A confirmed deleted board requires an explicit replacement decision.
- **Interrupted creation:** `planned` means creation has not started and may proceed. `creating` with no confirmed result means the outcome is unknown. Recover the exact result from the tool response, a supported operation-status endpoint, or a supported idempotent retry. If none is available, record the uncertainty and request the created board’s ID/link or confirmation that creation failed. Do not search for it or blindly repeat creation. Resume `initializing` directly by its saved ID.

Never fabricate IDs or successful writes. If local settings cannot be saved, use a specified existing board directly under recovery; defer new-board creation until its intent can be persisted.

**Complete when:** exactly one intended board is readable and its verified effective binding is recorded without modifying an unrelated default, or recovery has established an explicit degraded outcome.

## 3. Establish the working agreement

Skip initialization mutations when an existing charter and lifecycle mapping are already verified. For missing/incomplete agreements, load workflow policy and card-writing rules as directed above.

### Agent-created board or authorized initialization

Use this path only for a board just created by this setup or whose persisted `setup_state: initializing` and provenance authorize continuing it. Confirm one shared-structure writer before initialization mutations; a local bootstrap claim alone does not coordinate other clones or remote actors. A pre-existing empty board follows Existing board below unless initialization is explicitly authorized.

1. Inspect returned/default columns and reuse them. Rename initial To Do to Backlog, retain In Progress and Done, add missing Ready, Blocked, and Review, and arrange the default order in [workflow](workflow.md). Set Done as the sole native done column. After partial failure, finish missing steps on the same board.
2. Where supported, use Backlog unset, Ready blue, In Progress amber, Blocked rose, Review violet, Done green. Leave active columns expanded and collapse Done. Cosmetic limitations do not block tracking.
3. Find an existing charter before creating one. Use the charter template below, titled `[Board] <project> — working agreement`, first in Backlog. Exclude this reference card from delivery counts. Fill every policy from repository instructions or workflow defaults: scope, workflow, writer/claim protocol, review, integration, and verification. Link authoritative command documentation rather than inventing commands.
4. Record `charter_id` in this binding’s store after reading it back. On interrupted setup, reuse its ID or identify it by title and repository before creating anything. Verify all initialization steps, then set `setup_state: complete`; resume incomplete steps on the same board even if it now contains cards. Reread for intervening human changes and reconcile conflicts before continuing.

### Existing board

Read the charter and map actual columns onto lifecycle gates rather than imposing names. Preserve cards, relationships, ordering, native done semantics, and completion history. If mapping is unambiguous, record it in the charter and use it. Create a missing charter from observed conventions, repository policy, and workflow defaults for unspecified policy. Fill missing charter sections without replacing human decisions.

Ambiguous mappings, conflicting review policies, moving others’ cards, or changing done semantics require agreement. Propose the smallest migration with its effect; continue work that does not depend on that decision. Adding a non-done Cancelled column when first needed is routine if board permissions and charter permit it.

Record coordinator/card-body writer scope and checkpoint channel on each work group’s cards. Apply the ownership/write protocol in [coordinator procedure](coordinator.md): workers contribute execution evidence while the coordinator maintains bodies and lifecycle. Existing shared-structure authority prevails. The charter records the protocol, not a new global owner on every session.

**Complete when:** lifecycle gates and review/integration policy are explicit, the charter is verified, and no existing work has been silently reclassified.

## 4. Verify and return

Reread the effective binding record and board: matching server/board/charter identities, usable lifecycle, one done column on a newly configured board, and charter present. For a temporary override, confirm default fields remain unchanged. For persistent bootstrap, verify shared journal and checkout settings agree before releasing the claim. Report board name/reference and significant defaults adopted in a short update. Return to the coordinator procedure to load handoffs, reconcile pending records, and establish ownership before creating, claiming, or moving request cards. Binding/setup itself does not seed task cards.

## Board charter template

```markdown
Tracking agreement for <project>.
Coordination: parent owns lifecycle and acceptance; workers report execution on child cards.
-cut-

## Scope

- Repository/project: <canonical URL or identity>
- Tracks: <outcomes included>
- Specs/plans: <links or repo-relative paths>

## Working agreement

- Workflow: <actual column-to-lifecycle mapping; Done is sole native done column for new boards>
- Ownership: one coordinator/card-body writer per work group; one executor per task; session-qualified identities
- Execution reporting: <verified append-only comments or coordinator-recorded checkpoints; reporting channel and check-in points>
- Shared structure writer: <bootstrap coordinator identity or existing authorized identity>
- Claims/handoffs: reread, confirm unassigned or explicitly released, write claim, reread to verify; card checkpoints carry releases and handoffs
- WIP: one executable card per worker
- Review: <concrete policy initialized from project requirements and workflow defaults>
- Integration target: <current working tree/requested artifact unless project or user specifies another target>
- Verification: <authoritative instructions or discovered project commands; explicit check plan if none exists>
- Priority/deadlines: high urgent/critical-path unblocking, medium requested, low optional; deadlines only for established constraints

## Decisions

- <timestamp with timezone> — <policy decision and reason>
```
