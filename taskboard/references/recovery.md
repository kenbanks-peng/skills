# Tracking recovery

Coordinators read this for access/persistence failures, uncertain operations, incomplete duplicate lookup, or pending records awaiting reconciliation. Workers/reviewers report failures through their assigned channel instead of starting independent recovery.

Use the effective binding resolved by [binding](binding.md). Reconcile only records matching that project/server/board identity; temporary overrides remain separate from the default. Recovery does not authorize a new binding or replacement board.

## Recover without disguising degraded state

1. Inspect available connections and the actual error. Retry a transient read once; after an uncertain write, verify the affected object directly before retrying. For uncertain board creation, read the interrupted-creation rules in [board setup](board-setup.md); searching within the specified board for a card is not board discovery. Never install a server, alter credential configuration, or expose secrets to bypass missing access. Tell the user the specific connection/permission action needed only if it cannot be completed with available authorized tools.
2. Create `.taskboard/pending/<session-label>.md` using a filesystem-safe unique session label. Before creating, check for existing pending files. Keep one file per writer and binding; qualify the filename when a session uses multiple boards. Preserve other sessions’ records. Unresolved record identities require clarification. Include the identity header below, the [task template](card-writing.md), and [handoff](reporting.md): known card IDs or explicit local-only identifiers, scope, owner, intended status, evidence, next action, and any uncertain remote operation. Save material checkpoints here while offline. Treat records as potentially sensitive; exclude `.taskboard/pending/` through the project’s existing local-ignore mechanism when available.
3. Continue independent authorized work only when ownership is known and there is no risk of overlapping execution. A local record cannot claim a remote card, release another owner, or prove a remote transition. Otherwise record the blocker and pause only affected work. Tell the user tracking is local-only, not synchronized.
4. When Doska returns, open the specified board directly, reread affected cards, reconcile ownership and human edits, and search by outcome before creating missing cards. Exhaust relevant pages/statuses and supported archives under the coordinator’s duplicate-lookup rules; incomplete lookup requires retaining the pending task rather than creating a likely duplicate. Apply evidence-backed transitions, preserving the local record’s actual timestamps. Verify each remote write and record the resulting board/card mapping in the pending file. Mark it reconciled only when every pending change is accounted for; keep the record for traceability without replaying it next session.
5. If local writes are unavailable, retain the same record in the conversation and explicitly report that no local durable handoff was saved. If Doska is writable, an existing specified board can still hold durable cards while settings persistence is blocked: report remote-only tracking. Defer new-board creation until intent can be persisted under the setup protocol. If neither store is writable, leave a conversation-only blocked handoff and pause tracked execution until durable tracking is available. Resolve conflicts or request only missing access; never claim unavailable persistence succeeded.

Keep unavailable-board bindings intact. A confirmed deleted board requires an explicit replacement decision; not-found or permission errors do not authorize a substitute. Never fabricate IDs or successful writes.

**Recovery complete when:** pending records are reconciled and verified remote state agrees with delivered work, or the handoff explicitly identifies what remains local-only, remote-only, or blocked and who must act next.

## Binding record for temporary overrides and recovery

Keep this header in the session handoff or durable pending record, not in unrelated default settings. Include it before task/handoff content for degraded tracking. An in-memory or conversation record alone does not count as durable persistence.

```markdown
## Tracking identity

- Binding: <project default / temporary override>
- Project: <canonical repository identity>
- Server: <verified connection identity, no secrets>
- Board: <name; opaque ID, or explicitly unknown>
- Charter: <opaque ID, or unknown>
- Setup state: <if initialization is authorized; otherwise not applicable>
- Initialization authority: <creation provenance or explicit authorization, if applicable>
- Local record: <session-qualified local-only ID, if applicable>
- Unsynchronized changes: <intended writes and uncertain operation results, or none>
```
