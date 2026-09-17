# Tracking recovery

Read for access/persistence failures, uncertain operations, incomplete duplicate lookup, or pending-record reconciliation. Workers/reviewers report failures to their coordinator instead.

Use the [effective binding](binding.md); reconcile only matching project/server/board records. Keep temporary overrides separate. Recovery authorizes neither rebinding nor replacement boards.

## Recover

1. Inspect the connection and error. Retry transient reads once. Verify uncertain writes directly before retrying; uncertain board creation follows [board setup](board-setup.md). Card lookup within the specified board is allowed. Do not install servers, alter credentials, or expose secrets to bypass access failures. Request only access actions unavailable through authorized tools.
2. Inspect existing pending files, then create `.taskboard/pending/<session-label>.md` with a unique filesystem-safe label. Use one file per writer/binding; preserve others’ records and clarify unresolved identities. Include the identity header below, [task record](card-writing.md), and [handoff](reporting.md): remote or explicitly local-only IDs, scope, owner, intended status, evidence, next action, and uncertain operations. Save offline checkpoints here. Use the project’s local-ignore mechanism where available; records may be sensitive.
3. Continue only independent authorized work with known ownership and no execution overlap. Local records cannot claim remote cards, release owners, or prove transitions. Pause affected work otherwise. Report local-only tracking explicitly.
4. When Doska returns, open the specified board, reread affected cards, and reconcile ownership/human edits. Complete the coordinator’s duplicate lookup before creating missing cards; retain pending tasks if lookup remains incomplete. Apply evidence-backed transitions with original timestamps. Verify writes and record board/card mappings locally. Mark records reconciled only when every pending change is accounted for; retain them without replaying.
5. If local writes fail, retain the record in conversation and report the missing durable handoff. Writable Doska permits remote-only tracking on an existing specified board. Defer creation until setup intent can be persisted. If neither store is writable, leave a conversation-only blocked handoff and pause tracked execution.

Keep unavailable-board bindings intact. Even confirmed deletion requires an explicit replacement decision. Never fabricate IDs or successful writes.

Finish with verified reconciliation, or a handoff naming unsynchronized state, persistence limits, and the responsible next actor.

## Identity record

Use this header for temporary overrides and degraded tracking, outside unrelated default settings. Conversation-only records are not durable.

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
- Unsynchronized changes: <intended writes and uncertain results, or none>
```
