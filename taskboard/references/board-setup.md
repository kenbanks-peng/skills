# Board setup and recovery

Run binding checks at every start/resume. Bootstrap missing state yourself; user configuration is optional. Resolve tool names, schemas, pagination, and supported operations from live Doska MCP instructions before calling them.

## 1. Locate and initialize local settings

Use the repository root, not the current subdirectory or skill installation directory. For a non-Git project, use the workspace project root. In a multi-root workspace, select the root containing the requested work; ask only if the scope remains ambiguous. Branches/worktrees reuse the same settings: if absent in the current checkout, copy them from the main checkout when available. If no settings or explicit board reference exist, initialize new settings and create the specified board; repository identity is documentation, not a board-discovery mechanism.

Create `.taskboard/` and `.taskboard/settings.md` if missing. Read before updating; preserve user notes and unknown fields, fill absent fields, and repair only unambiguous invalid values. The file is Markdown with these binding keys in YAML frontmatter:

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
- Quote string values with valid YAML escaping. Store opaque IDs exactly as returned. Treat unsupported settings versions or contradictory bindings as unresolved; preserve them and ask rather than silently rewriting them.
- Keep settings suitable for version control, subject to repository policy; sanitize remote credentials and omit tokens and task contents. Do not commit files automatically. Treat local recovery records as potentially sensitive and exclude `.taskboard/pending/` through the repository’s existing local-ignore mechanism when available.

**Complete when:** settings exist with a project identity and board name, and existing bindings and notes are preserved. If local writes are unavailable, report the constraint and use the recovery rules below.

## 2. Use the specified board or create the newly specified board

Board selection comes only from the user or settings. Do not list boards, search names, compare repository identities, or inspect candidate charters to choose one.

- **Board specified:** use the explicit user reference for this request, otherwise the settings binding. Open it directly by `board_id`, or by its exact specified name if the live API supports direct name addressing. If the API requires an ID and only a name is supplied, ask for that board’s ID/link rather than searching. Persist verified IDs; refresh the display name if the board was renamed. An ad hoc user reference does not overwrite an established default unless the user changes the project binding.
- **No board specified:** choose and save `board_name` with `setup_state: planned` as above. Then set `setup_state: creating`, create that board without searching or asking approval, and immediately save the returned `board_id` and `setup_state: initializing`. If creation explicitly rejects a duplicate name, choose a qualified name from the repository owner/path, persist it, and retry creation; do not adopt the other board.
- **Specified board unavailable:** report the actual not-found, access, or connection error and enter recovery. Keep the binding; do not search for a substitute or silently create a replacement. A confirmed deleted board requires an explicit replacement decision.
- **Interrupted creation:** `planned` means creation has not started and may proceed. `creating` with no confirmed result means the outcome is unknown. Recover the exact result from the tool response, a supported operation-status endpoint, or a supported idempotent retry. If none is available, record the uncertainty and request the created board’s ID/link or confirmation that creation failed. Do not search for it or blindly repeat creation. Resume `initializing` directly by its saved ID.

Never fabricate IDs or successful writes. If local settings cannot be saved, use a specified existing board directly under the recovery rules; defer new-board creation until its intent can be persisted.

**Complete when:** exactly one intended board is readable and its verified binding is persisted. If persistence or server access is blocked, report remote-only or local-only tracking, or a conversation-only blocked handoff, as specified under Recovery.

## 3. Establish the working agreement

### Agent-created board or authorized initialization

Use this path only for a board just created by this setup or whose persisted `setup_state: initializing` and provenance authorize continuing it. A pre-existing empty board follows Existing board below unless initialization is explicitly authorized.

1. Inspect returned/default columns and reuse them. Rename initial To Do to Backlog, retain In Progress and Done, add missing Ready, Blocked, and Review, and arrange the skill’s default order. Set Done as the sole native done column. After partial failure, finish missing steps on the same board.
2. Where supported, use Backlog unset, Ready blue, In Progress amber, Blocked rose, Review violet, Done green. Leave active columns expanded and collapse Done. Cosmetic limitations do not block tracking.
3. Find an existing charter before creating one. Use the charter template in [templates.md](templates.md), titled `[Board] <project> — working agreement`, first in Backlog. Exclude this reference card from delivery counts. Fill every policy from repository instructions or the skill’s Decision defaults: scope, workflow, writer/claim protocol, review, integration, and verification. Link authoritative command documentation rather than inventing commands.
4. Persist `charter_id` after reading it back. On interrupted setup, reuse its ID or identify it by title and repository before creating anything. Verify all initialization steps, then set `setup_state: complete`; resume incomplete steps on the same board even if it now contains cards. Reread for intervening human changes and reconcile conflicts before continuing.

### Existing board

Read the charter and map actual columns onto the lifecycle gates rather than imposing names. Preserve cards, relationships, ordering, native done semantics, and completion history. If the mapping is unambiguous, record it in the charter and use it. Create a missing charter from observed conventions, repository policy, and the skill defaults for unspecified policy. Fill missing charter sections without replacing human decisions.

Ambiguous mappings, conflicting review policies, moving others’ cards, or changing done semantics require agreement. Propose the smallest migration with its effect; continue work that does not depend on that decision. Adding a non-done Cancelled column when first needed is routine if board permissions and charter permit it.

Record coordinator/card-body writer scope and the execution checkpoint channel on each work group’s cards. Apply the main skill’s Ownership and delegation protocol: workers contribute execution evidence, while the coordinator maintains bodies and lifecycle. Existing shared-structure authority prevails. The charter records the protocol, not a new global owner on every session.

**Complete when:** lifecycle gates and review/integration policy are explicit, the charter is verified, and no existing work has been silently reclassified.

## 4. Verify and return

Reread settings and the board: correct binding, usable lifecycle, one done column on a newly configured board, and charter present. Report the board name/reference and significant defaults adopted in a short update. Return to the main skill to load handoffs, reconcile pending records, and establish ownership before creating, claiming, or moving request cards. Binding/setup itself does not seed task cards.

## Recovery: Doska or local persistence unavailable

Own recovery without disguising degraded state:

1. Inspect available connections and the actual error. Retry a transient read once; after an uncertain write, verify the affected object directly before retrying. For uncertain board creation, follow Interrupted creation above; searching within the specified board for a card is not board discovery. Never install a server, alter credential configuration, or expose secrets to bypass missing access. Tell the user the specific connection/permission action needed only if it cannot be completed with available authorized tools.
2. Create `.taskboard/pending/<session-label>.md` using a filesystem-safe unique session label. Before creating, check for existing pending files. Keep one file per writer; preserve other sessions’ records. Use the task and handoff templates, including project/server/board identity, known card IDs or explicit local-only identifiers, scope, owner, intended status, evidence, next action, and any uncertain remote operation. Save material checkpoints here while offline.
3. Continue independent authorized work only when ownership is known and there is no risk of overlapping execution. A local record cannot claim a remote card, release another owner, or prove a remote transition. Otherwise record the blocker and pause only the affected work. Tell the user tracking is local-only, not synchronized.
4. When Doska returns, open the specified board directly, reread affected cards, reconcile ownership and human edits, and search by outcome before creating missing cards. Apply evidence-backed transitions, preserving the local record’s actual timestamps. Verify each remote write and record the resulting board/card mapping in the pending file. Mark it reconciled only when every pending change is accounted for; keep the record for traceability without replaying it next session.
5. If local writes are also unavailable, retain the same record in the conversation and explicitly report that no local durable handoff was saved. If Doska is writable, it can still hold durable cards while settings persistence is blocked. Resolve conflicts or request only the missing access required; never claim unavailable persistence succeeded.

**Recovery complete when:** pending records are reconciled and the verified remote state agrees with delivered work, or the handoff explicitly identifies what remains local-only and who must act next.
