# Regression scenarios

Use for skill maintenance only, with stubbed MCP/filesystem responses or a disposable workspace—not real project boards.

Record traces, pass/fail, and divergences. Passing requires every expected action, no forbidden mutations, and the stopping condition. Label document walkthroughs as static checks, not executed agent tests.

## 1. Untracked request

**Given:** no settings; a quick question, trivial edit, or skill-maintenance request without required tracking.

- **Expected:** complete the request without setup.
- **Forbidden:** create settings, boards, or cards.
- **Stop:** request satisfied.
- **Variant:** explicitly requested tracking enters the coordinator path.

## 2. Delegated worker without settings

**Given:** a complete assignment and reporting channel; no worktree settings. Repeat for a reviewer.

- **Expected:** load worker/reporting references, confirm the assignment, read supplied/card context, execute within scope, and report checkpoints/return.
- **Forbidden:** load coordinator/setup/workflow/authoring references unnecessarily; bootstrap settings, alter charter/body, or transition cards.
- **Stop:** return evidence, or request missing context and pause affected execution.

## 3. Concurrent worktree initialization

**Given:** linked worktrees A/B lack settings and board references; both initialize.

- **Expected:** resolve the same common Git directory; one atomic claim succeeds. The other waits/coordinates, then reuses journaled identity even if A’s checkout is unavailable.
- **Forbidden:** duplicate creation, age-based takeover, or treating a metadata-free claim directory as unowned.
- **Stop:** one binding reaches participating worktrees, or the non-writer records a release blocker.
- **Variant:** separate clones require an explicit initializer agreement; local locks cannot coordinate them.

## 4. Lost creation response

**Given:** journal state `creating`; the board was created but its ID response was lost.

- **Expected:** recover the exact response, operation status, or supported idempotent result; otherwise request ID/link or confirmation of failure.
- **Forbidden:** board discovery, blind recreation, resetting to `planned`, or claiming unverified success.
- **Stop:** resume by recovered ID, or record uncertainty and block creation.
- **Variant:** an ID journaled before a settings-copy crash is recovered without another create call.

## 5. Temporary override

**Given:** default board/charter A; user selects B for this request.

- **Expected:** open B directly, verify its charter, record identity separately, and reconcile only B’s pending records. Authorized initialization retains B-specific provenance.
- **Forbidden:** change A’s binding fields, transfer A’s setup authority, or replay A’s records into B.
- **Stop:** durable tracking on B; A unchanged and selected next ordinary session.

## 6. Concurrent human edits

**Given:** a human changes acceptance text or attachments before coordinator body replacement.

- **Expected:** reread, preserve changes, and reconcile conflicts. Use verified checkbox operations or serialized replacements. Stop competing writes and agree a writer.
- **Forbidden:** overwrite decisions/attachment keys, permit worker body replacement, or claim read/write atomicity.
- **Stop:** verified update or recorded conflict with a responsible next actor.
- **Limit:** undetected races remain possible without server-side conditional writes.

## 7. No writable persistence

**Given:** Doska and local settings/pending writes fail.

- **Expected:** report failures, leave a conversation-only blocked handoff, and pause tracked execution.
- **Forbidden:** claim durable saves, fabricate IDs, or continue as though persistence succeeded.
- **Stop:** handoff names blocked work, missing access, responsible actor, and next action.
- **Variants:** writable Doska permits remote-only tracking on an existing specified board; writable local storage permits safe independent work, not remote claims/transitions.

## 8. Paginated duplicate lookup

**Given:** the matching outcome is on a later page or archived; unrelated work dominates the board.

- **Expected:** load the work group, dependencies, and charter; exhaust relevant duplicate-search pages/statuses/archives. Load candidate bodies as needed.
- **Forbidden:** infer absence from partial results, create after incomplete lookup, or reconcile unrelated cards during routine resume.
- **Stop:** reuse/reopen/link the match, create after complete lookup, or retain a pending task through recovery.

## 9. Final-response-only worker

**Given:** worker cannot append comments or send intermediate messages.

- **Expected:** arrange checkpoint files/check-ins or bounded dispatch stages; coordinator reconciles and accepts results.
- **Forbidden:** promise unavailable live reporting, simulate append-only writes with body replacements, or accept on dispatch/worker success alone.
- **Stop:** worker returns results and execution safety; coordinator applies verification, review, and integration gates.

## 10. Routine resume

**Given:** complete version-1 settings, readable charter/board, explicit lifecycle, one task, no pending records or binding changes.

- **Expected:** load coordinator/binding/workflow; inspect only the work group, dependencies, and handoffs. Load card-writing for body edits and reporting for checkpoints.
- **Forbidden:** load setup/recovery/delegation/decomposition/scenarios unnecessarily, rewrite unchanged settings, or reinitialize.
- **Stop:** verified ownership, acceptance, and next action without setup mutations.

## 11. Conditional setup/recovery

**Given:** separately test missing settings, incomplete setup, missing charter/mapping, and a persistent binding update.

- **Expected:** route through binding to setup before mutations. Check main checkout/journal for missing settings; require claim/journal for binding writes. Charter setup loads workflow/card-writing; binding-only updates do not.
- **Forbidden:** create solely because settings are missing, bypass the writer protocol, or infer initialization authority from an empty board.
- **Stop:** verified binding/agreement or explicit blocked/degraded outcome.
- **Variants:** access/persistence failure, uncertain writes, incomplete duplicate lookup, and pending records route to recovery; uncertain board creation also loads setup. Other bindings’ pending records remain untouched.

## 12. Card granularity

**Given:** a small single-owner task, then parallel or independently blocked deliverables.

- **Expected:** use the task template for the former; load decomposition for multi-card creation/resumption. Dispatch additionally loads delegation and supplies worker entry.
- **Forbidden:** small-task epics, unconditional template loading, hierarchy-implied dependencies, or parent acceptance on worker success alone.
- **Stop:** structure matches ownership/lifecycle boundaries with explicit acceptance.

## 13. Reference integrity

**Given:** revised skill documents.

- **Expected:** verify local Markdown targets outside code fences; walk role/state routes; confirm required rules have authoritative locations and conditional pointers.
- **Forbidden:** orphan rules, retain references to removed sections/templates, treat heading links as partial file loading, or require every role to read everything.
- **Stop:** static checks and walkthrough results recorded without claiming executed agent regression coverage.
