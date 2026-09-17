# Board setup and binding changes

Read for missing/incomplete settings, persistent binding updates, unfinished/authorized initialization, or missing charter/lifecycle policy. Resolve the effective binding through [binding](binding.md) first.

For failures or uncertain writes, use [recovery](recovery.md). Read [workflow](workflow.md) for charter/column setup and [card writing](card-writing.md) for charter body edits. Binding-only updates need neither.

## 1. Establish the setup writer

If settings are missing, inspect the main checkout and shared journal before planning creation. Reuse a verified binding; reconcile conflicting copies.

Before any persistent binding mutation, acquire a repository-shared bootstrap claim:

- Git: resolve `git rev-parse --path-format=absolute --git-common-dir`; use `<common-dir>/taskboard/bootstrap.lock/` and `<common-dir>/taskboard/setup.md`.
- Non-Git: use `.taskboard/bootstrap.lock/` and `.taskboard/setup.md` at the workspace root.

1. Create the parent directory, then atomically create the claim directory using an operation that fails if it exists. Record session identity and start time inside. An existing directory—even without metadata—requires coordination, not takeover by age.
2. After acquiring the claim, reread checkout/main-checkout settings and the journal. Resume recorded bindings or uncertain operations instead of creating again.
3. Journal each intended binding/state change before updating settings or issuing its remote operation. Use atomic local file replacement. Record prior and replacement fields: after interruption, complete the copy only if settings still match the prior fields; otherwise reconcile. Journal returned IDs immediately, then copy them to settings. Record deliberate binding changes with both identities.
4. Hold the claim until initialization or a blocked outcome is durable. Release only your own claim; retain the journal. After a crash, reclaim only after confirming the prior writer stopped/released ownership and reviewing uncertain operations.

This claim covers one shared filesystem. Separate clones/machines need an explicit shared-binding/initializer agreement. Without a claim, defer board creation and persistent binding changes; an explicit existing board may remain usable through recovery. Temporary overrides leave default bootstrap state untouched, but shared-board initialization still requires an agreed writer.

## 2. Save settings

Create `.taskboard/settings.md` for a missing default; temporary overrides keep a separate [identity record](recovery.md). Preserve notes and unknown fields; repair only unambiguous invalid values.

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
```

- Infer `project` from documentation or package metadata, falling back to the directory name. If no board is specified, save that name with `setup_state: planned`. An existing specified name refers to an existing board.
- Normalize the canonical Git remote to a host/path identity shared by SSH/HTTPS forms; remove credentials, query strings, and trailing `.git`. Without a remote, use the main checkout’s absolute path. Reconcile identity changes rather than creating another board.
- `server` identifies the MCP connection/workspace, never a secret. Follow binding’s connection-selection rules.
- Quote strings with valid YAML escaping; preserve opaque IDs exactly. Unsupported versions or contradictory bindings require clarification.
- Keep settings version-control-safe under repository policy; omit tokens and task contents. Do not commit automatically. Locally ignore non-Git lock/journal files and `.taskboard/pending/` where the project provides an ignore mechanism.

Persist setup states under the journal protocol:

| State | Meaning |
| --- | --- |
| `null` | Specified existing board; no initialization authority |
| `planned` | Newly specified board; creation has not started |
| `creating` | Creation is about to run or its result is uncertain |
| `initializing` | Creation confirmed, or initialization explicitly authorized |
| `complete` | Initialization verified |

States authorize no changes to other boards. Preserve them through interruptions; reset them when deliberately changing the binding.

For a requested default change, verify the target and replace `server`, `board_name`, `board_id`, `charter_id`, and `setup_state` together. Preserve unrelated fields; discard old charter/setup authority. Record temporary initialization intent separately with board-qualified provenance.

Proceed when the intended binding is recorded and its writer established. If local writes fail, use recovery.

## 3. Open or create

- **Specified board:** open directly under [binding](binding.md); save verified IDs/name changes in its proper store.
- **No specified board:** save the chosen name as `planned`, then `creating`; create without discovery or routine approval. Immediately journal the returned ID and `initializing` state. If creation explicitly rejects a duplicate name, persist a repository-owner/path-qualified name and retry; do not adopt the other board.
- **Unavailable board:** preserve the binding and enter recovery; never silently substitute another board.
- **Interrupted creation:** `planned` may proceed. For `creating` without a confirmed result, recover the exact response, query a supported operation-status endpoint, or use a supported idempotent retry. Otherwise record uncertainty and ask for the ID/link or confirmation of failure. Never search or blindly recreate. Resume `initializing` by saved ID.

Defer creation until intent can be persisted. If settings are unwritable, recovery may use an existing specified board.

Proceed when the intended board is readable and its verified identity recorded, or recovery establishes a blocked/degraded outcome.

## 4. Establish the charter and lifecycle

Skip initialization when charter and mapping are already verified.

### New board or authorized initialization

Require creation provenance or explicit initialization authorization, persisted as `initializing`. Agree one shared-structure writer; a local claim does not coordinate remote actors. An existing empty board is not automatically authorized.

1. Reuse default columns: rename To Do to Backlog, retain In Progress/Done, and add missing Ready, Blocked, and Review. Apply [workflow order](workflow.md); make Done the sole native done column. Resume partial setup on the same board.
2. Where supported, use Backlog unset, Ready blue, In Progress amber, Blocked rose, Review violet, and Done green. Expand active columns and collapse Done. Unsupported cosmetics do not block tracking.
3. Find the charter before creating one. Place `[Board] <project> — working agreement` first in Backlog; exclude it from delivery counts. Fill the template from repository policy and workflow defaults. Link authoritative command documentation.
4. Read back the charter and save its ID. After interruption, reuse the ID or identify the charter by title and repository on this board. Reconcile intervening human edits. Set `complete` only after verifying all setup steps; existing task cards do not prevent resumption.

### Existing board

Map actual columns to lifecycle gates; preserve cards, relationships, order, native done semantics, and history. Record unambiguous mappings in the charter. Create missing policy from observed conventions, repository requirements, and otherwise workflow defaults; preserve human decisions.

Ambiguous mappings, conflicting review policy, moving others’ cards, or changing done semantics require agreement. Propose the smallest migration and its effect; continue unaffected work. A non-done Cancelled column may be added when needed if permissions and charter allow it.

Record coordinator/writer scope and checkpoint channels on work-group cards under [coordinator ownership](coordinator.md). The charter defines the protocol; each session does not appoint a new global owner.

Proceed when lifecycle, review, and integration policy are explicit and verified without silently reclassifying work.

## 5. Verify and return

Reread binding and board: server/board/charter identities match, lifecycle is usable, charter exists, and newly configured boards have one native done column. Verify temporary overrides left defaults unchanged, or persistent journal/settings agree. Release your claim after verification.

Report board reference and significant defaults briefly. Return to coordinator startup for handoffs, pending records, and ownership before creating or moving task cards.

## Charter template

```markdown
Working agreement for <project>.
-cut-

## Scope

- Repository/project: <canonical URL or identity>
- Tracks: <included outcomes>
- Specs/plans: <links or repo-relative paths>

## Working agreement

- Workflow: <actual lifecycle mapping; new boards have one native Done column>
- Ownership: one body/lifecycle writer per work group; one executor per task; session-qualified identities
- Checkpoints: <verified append-only comments or coordinator-recorded reports; channel and check-in points>
- Shared structure writer: <authorized identity>
- Claims: reread, confirm unassigned/released, write claim, reread to verify; record handoffs on cards
- WIP: one executable card per worker
- Review: <project requirements or workflow defaults>
- Integration target: <current working tree/requested artifact unless otherwise specified>
- Verification: <authoritative command instructions or explicit check plan>
- Priority/deadlines: high urgent/critical-path, medium requested, low optional; deadlines require established constraints

## Decisions

- <timestamp with timezone> — <policy decision and reason>
```
