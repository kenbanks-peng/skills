# Behavioral regression scenarios

Use when maintaining this skill, not during ordinary taskboard work. Exercise each scenario with stubbed MCP/filesystem responses or a disposable test workspace; never create or mutate a real project board just to validate the document.

For each scenario, record the observed action trace, pass/fail, and any divergence. A document walkthrough checks consistency only; it is not an executed agent regression test. Pass requires all expected actions, no forbidden mutations, and the stated stopping condition.

## 1. Quick request without tracking

**Given:** no settings exist; the user asks a quick question, requests a trivial edit, or asks to review/update this skill. Tracking is not required by project policy or user instruction.

- **Expected:** answer or perform the requested work without board setup.
- **Forbidden:** create settings, a board, or task cards merely because the subject is the taskboard skill.
- **Stop:** the original request is satisfied. If tracking is explicitly requested, follow the coordinator path instead.

## 2. Delegated worker without local settings

**Given:** the parent supplies board/card IDs, scope, identity, dependencies, file boundary, acceptance criteria, and a reporting channel; the worktree has no `.taskboard/settings.md`.

- **Expected:** load `worker.md` and `reporting.md`, confirm the assignment, use supplied card context or read the assigned card, execute within scope, and report checkpoints/return. Repeat with a reviewer assignment. Neither role needs coordinator, setup, workflow, or card-authoring references when supplied criteria are complete.
- **Forbidden:** bootstrap settings or a board, edit the charter, replace the card body, or transition the card as a worker/reviewer.
- **Stop:** return evidence to the parent; if essential assignment context is missing, pause affected execution and request it.

## 3. Two worktrees initialize simultaneously

**Given:** linked worktrees A and B have no settings or explicit board reference; both attempt initialization.

- **Expected:** both resolve the same common Git directory; exactly one atomic bootstrap claim succeeds. The other coordinates/waits. The writer journals intent and returned IDs; the later writer rereads the journal and reuses that binding even if A’s checkout is unavailable.
- **Forbidden:** two create-board calls, takeover based only on age, or treating an existing empty claim directory as unowned.
- **Stop:** one verified binding is copied to the participating worktrees, or the non-writer records a blocker pending confirmed release.
- **Variant:** separate clones do not share this lock; require an explicit binding/initializer agreement when concurrent initialization is known.

## 4. Board creation succeeds but its response is lost

**Given:** the durable setup journal says `creating`; the server created the board, but no confirmed ID was received.

- **Expected:** seek the exact result from a saved tool response, supported operation-status endpoint, or supported idempotent retry. Otherwise ask for the ID/link or confirmation that creation failed.
- **Forbidden:** board discovery, blind create retry, reset to `planned`, or reporting successful binding without evidence.
- **Stop:** resume by the recovered ID, or record the uncertainty and block further creation.
- **Variant:** crash after journaling the returned ID but before updating checkout settings; recover that binding from the journal without another create call.

## 5. Temporary board override

**Given:** default settings bind board A and charter A; the user selects existing board B for this request only.

- **Expected:** use B directly, verify B’s charter, and record the effective identity separately. Reconcile only B’s pending records; leave A’s records untouched. If B requires authorized initialization, keep its provenance and progress in B’s record.
- **Forbidden:** change A’s server/name/ID/charter/setup state, initialize B using A’s setup authority, or replay A’s pending changes into B.
- **Stop:** work is durably tracked on B and A’s default binding fields remain unchanged; the next ordinary session selects A.

## 6. Human edits during an agent update

**Given:** the coordinator is preparing a whole-body update and a human has changed acceptance text or attachment references.

- **Expected:** reread before replacement, preserve the human changes, and reconcile conflicting edits. Use the verified checkbox operation where supported; otherwise serialize the body update. If competing writes are detected, stop mutations and agree a writer.
- **Forbidden:** overwrite human decisions, discard attachment keys, let a worker replace the body, or claim reread/write guarantees atomicity.
- **Stop:** the reconciled update is verified, or the conflict is recorded with a responsible next action.
- **Limit:** a race after the final read may be undetectable without server-side conditional writes; passing this scenario does not establish compare-and-swap safety.

## 7. Neither remote nor local persistence is writable

**Given:** Doska writes fail and local settings/pending records cannot be saved.

- **Expected:** report the actual failures, retain a conversation-only blocked handoff, and pause tracked execution until durable tracking is available.
- **Forbidden:** claim a durable save, fabricate card IDs, or continue tracked execution as though persistence succeeded.
- **Stop:** the handoff identifies blocked work, missing access, responsible actor, and next action.
- **Variants:** writable Doska permits remote-only tracking on an existing explicit board; writable local storage permits safe independent work with known ownership, not a remote claim or transition.

## 8. Large board and paginated duplicate lookup

**Given:** the requested outcome already exists on a later result page or among archived cards; unrelated work dominates the board.

- **Expected:** load charter/current work group and dependency closure for resume; exhaust relevant duplicate-search pages across statuses and archives where supported before creating a card. Load candidate bodies only as needed.
- **Forbidden:** infer absence from the first page, create a duplicate after an incomplete lookup, or read/reconcile every unrelated card on routine resume.
- **Stop:** reuse/reopen/link the matching outcome under `coordinator.md` rules, create only after a complete lookup, or follow `recovery.md` to leave a local pending record while lookup remains blocked.

## 9. Final-response-only worker

**Given:** the worker cannot append comments or send intermediate messages.

- **Expected:** establish readable per-worker checkpoint files with concrete check-in points, or dispatch bounded stages that return checkpoints. Parent reconciles evidence and performs acceptance.
- **Forbidden:** promise live reporting without a transport, simulate append-only comments using concurrent body replacement, or mark Done on dispatch/worker success alone.
- **Stop:** the worker returns actual results and execution-safety state; the parent applies verification, review, and integration gates before Done.

## 10. Routine coordinator resume without setup

**Given:** complete version-1 default settings, readable board and charter, explicit lifecycle mapping, one standalone card, no pending records, and no binding changes needed.

- **Expected:** load `coordinator.md`, `binding.md`, and `workflow.md`; read only the work group, dependency closure, and relevant handoffs. Load `card-writing.md` for body edits and `reporting.md` for checkpoints/handoffs.
- **Forbidden:** load board construction, recovery, delegation, decomposition, or authoring scenarios merely because the skill was invoked; rewrite unchanged binding fields or reinitialize the board.
- **Stop:** the existing card has verified ownership, acceptance, and a next action without setup mutations.

## 11. Conditional setup and recovery routing

**Given:** a coordinator starts with missing checkout settings, an incomplete setup state, missing charter/mapping, or a required persistent binding update. Exercise each separately.

- **Expected:** route from `binding.md` to `board-setup.md` before affected mutations. Missing checkout settings trigger main-checkout/shared-journal checks; all persistent binding writes use the shared claim/journal protocol. Charter initialization loads `workflow.md` and `card-writing.md`; a binding-only update does not need charter-authoring instructions.
- **Forbidden:** infer that missing settings authorize creation, update binding fields without the writer protocol, or treat an existing empty board as authorized initialization.
- **Stop:** setup verifies the effective binding/agreement or records an explicit blocked/degraded outcome.
- **Variants:** an access/persistence failure, uncertain write, incomplete duplicate lookup, or unreconciled pending record routes to `recovery.md`; uncertain board creation also loads `board-setup.md`. Pending records for other bindings remain untouched.

## 12. Single-card versus multi-card authoring

**Given:** a small single-owner task, then a separate request requiring parallel children or independently blocked deliverables.

- **Expected:** the small task uses the executable template in `card-writing.md` without loading parent/charter templates. The multi-card request loads `decomposition.md` before creating or coordinating parent/child cards, including on resume. Dispatch additionally loads `delegation.md` and supplies the worker entry path.
- **Forbidden:** create an epic for the small task, load all templates unconditionally, infer dependency order from hierarchy, or tick parent acceptance solely on a worker’s success report.
- **Stop:** card structure matches ownership/lifecycle boundaries and required acceptance remains explicit.

## 13. Reference integrity after authoring changes

**Given:** a proposed revision of the skill and references.

- **Expected:** check local Markdown links outside code fences; every target exists. Walk role/state routes and verify that moved rules/templates have an authoritative destination and pointers with explicit triggers. Check that references do not require loading removed root sections or the former all-purpose `templates.md`.
- **Forbidden:** orphan a required safety rule, rely on a heading link to prevent loading the rest of a file, or instruct every role to read every reference.
- **Stop:** static checks and scenario walkthrough results are recorded as such. Do not label a document walkthrough an executed agent regression test.
