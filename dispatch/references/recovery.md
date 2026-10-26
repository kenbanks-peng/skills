# Recovery and owned cleanup

## Resume without duplicate effects

1. Read Aven task context and the last attempt/outcome notes. Identify repository, run, daemon/server, host, session/pane IDs, branches, paths, queue/message IDs, reviewed revision, and target before/after SHAs. Preserve existing user changes.
2. Reconcile native inventories in the same execution context:

   ```sh
   tuios worktree ls --json
   tuios list-agents --select "$OWNED_SELECTOR" --json
   tuios list-attention --select "$OWNED_SELECTOR" --json
   tuios queue ls -s "$SESSION" -w "$PANE" --json
   tuios read-agent-messages -s "$SESSION" -w "$INBOX" --peek --json
   tuios checkpoint list -s "$SESSION" -w "$PANE" --json
   tuios ship status -s "$SESSION" -w "$PANE" --json
   ```

   Use the recorded session and full pane ID for `SESSION` and `PANE`, never focus or a reused name. Run pane-specific calls only for identities still present. Read Git branch, HEAD, status, worktree inventory, and target history. Check any recorded runtime/container ID through its authorized lifecycle tool. A reused name is not the same resource; compare pane/session IDs, branch, path, base, and runtime identity.
3. Classify each intended effect before a retry:

   | Uncertain effect | Reconcile | Safe next step |
   | --- | --- | --- |
   | Worktree create | Native inventory, branch/path/base | Reuse a matching owned tree; do not create another |
   | Agent launch | Pane ID, harness, cwd, state, prompt status | Reuse a live matching pane; diagnose held/stalled |
   | Initial assignment | Prompt status, activity, task/attempt ID in output | Wait or ask for read-only status only when ready; do not resend work blindly |
   | Queued correction | Queue ID/text, review notes, worker result | Keep known pending work; reissue only after proving no prior execution |
   | Mail/review send | Thread, notes' sent state, reply evidence | Wait/read explicitly; do not duplicate through queue |
   | Check | Check pane, exit code, tested revision, logs | Recover result or rerun only a known safe check |
   | Commit | Branch HEAD, log, exact diff/scope | Reuse the existing matching SHA; no empty duplicate commit |
   | Merge | Target log, source ancestry or squash patch, native merged status | Reuse observed integration; do not repeat merge |
   | Removal | Native inventory, directory, branch and evidence | Record already removed; never remove a replacement by name alone |

4. A daemon restart loses mail, queue, and agent state even if pane IDs return. Do not interpret missing in-memory data as no prior execution. Inspect repository and durable evidence. If completion cannot be proved, freeze affected work and record an uncertain-delivery blocker. Continue independent tasks.
5. Reconnect event streams using saved boot/sequence cursors when valid. On `gap`, rebuild from inventories. Do not replay actions from old events. Update the existing dashboard rather than making a duplicate surface.
6. Repair only recoverable problems inside scope: rerun a failed read, replace a stopped owned worker with a new recorded attempt, or rerun a safe check. Do not restart a shared daemon, alter shared config, impersonate a pane, or broaden grants to repair a capability mismatch.
7. Save reconciled decisions in Aven before new side effects. If Aven is unavailable, retain local evidence and report that the durable record is incomplete.

## Cleanup

Delivery and cleanup are separate outcomes. Do not remove evidence or useful checkpoints before the attempt's disposition is known.

1. Build an exact owned resource list from attempt records and current native inventory. For each tree, record selected/rejected/blocked status, commit SHAs, dirty paths, checkpoint needs, active processes, runtime, and keep/remove decision.
2. Stop only owned writers and checks. Reconcile and remove only known owned pending queue entries that could restart work. A `needs_input` pane is blocked, not permission to type. Retain it if shutdown would need a forbidden response. Ensure no background process started by this run remains unaccounted for.
3. Save reports, check logs, review notes, and important checkpoint patches outside disposable trees. Record evidence path and integrity/revision. Session mail/stash and checkpoint refs are not durable storage after removal.
4. For an integrated or explicitly rejected clean owned tree:

   ```sh
   tuios worktree rm "$SESSION" --json
   ```

   This removes the tree and kills its session; it never deletes the branch. It needs the appropriate existing authority. Do not use raw git worktree remove or prune as a fallback.
5. On `worktree_dirty`, retain by default. If the recorded disposition authorizes preservation in stash:

   ```sh
   tuios worktree rm "$SESSION" --stash --json
   ```

   Record the actual stash identity and retained branch. A stash is local and can be dropped later; it is not a remote backup. A useful unresolved checkpoint or runtime can justify retaining the whole tree instead. `--force` discards work and is not a default cleanup path. Do not remove detached unreachable commits, unrelated work, or unknown files.
6. For a fan, apply [selection/disposition](workers.md#competing-attempts). Use fan keep only when all sibling removals are authorized. It can delete ignored files in sibling trees; preserve needed artifacts first. Record any dirty siblings it leaves. Remove the selected tree separately only after integration evidence and checks are durable.
7. For a non-worktree owned session, discover `tuios kill-session --help`, then use `tuios kill-session SESSION` only after checking exact ownership and preserving its evidence. Do not kill a shared orchestration session just to remove its dashboard. Close only the owned TML surface with the documented dashboard procedure.
8. Stop/remove an owned container only with the lifecycle procedure in [pi](pi.md), after its work and evidence are safe. Do not stop a shared runtime or leave it unreported. Native worktree removal does not prove a container stopped.
9. Inventory again. Record removed and retained session IDs, worktree paths, branches, stashes, checkpoints, check panes, runtimes, dashboard, and event readers. Native cleanup retains branches by design; do not claim all resources were deleted. Avoid branch deletion unless separately authorized.

## Final handoff

Append a concise outcome note to each affected Aven task. Update the existing dashboard. Report:

- Delivered changes and task refs; selected attempt and rejected/retained dispositions.
- Reviewed source commit and target before/after SHAs; explicit merge policy.
- Check commands, exit status, evidence paths, and skipped/unavailable checks.
- Blockers, failed acceptance, uncertainty, and the next safe action.
- Cleanup completed, cleanup pending, and every retained owned resource with reason.

Use precise outcomes such as `delivered; cleanup pending`, `implemented; integration blocked`, or `blocked; independent tasks delivered`. Do not equate a worker's done state with task completion. Do not ask a person to decide. State the missing fact or authority as a blocker.

## Known capability gaps

- No unattended ship push/pr while native approval is required. Observe existing PR/CI state only.
- Native verdict is restricted to the native judge or an already external caller. The supplied snapshots do not define judge launch parameters. Discover the actual verb schema; if unavailable, preserve selection in Aven and report native verdict as unmet.
- Native TML validation passed, but `tml-open`, `list-verbs`, and `wait-for --new` failed against the older shared daemon. Validation is not evidence of a working live surface or native workflow. Do not restart the shared daemon. Use supported bounded state/message waits without `--new` and inspect current evidence. If schema discovery or surface creation is unavailable, record the affected feature as blocked rather than guessing parameters. Native live acceptance remains task **SKL-2R45**, not passed; see the [Pi host probe](pi.md#host-integration-probe) for the same-session mail prerequisite.
- Fan/start-agent can encounter first-run input and fan/queue can create diagnostic Inbox questions for held/stalled prompts. There is no documented switch that suppresses all such native items. Preflight readiness, do not deliberately launch an unready harness, never answer the items, and report unexpected input as blocked. The supported workflow has no human-response path.
- Review and checkpoints are local-only. Remote work must be pulled through authorized native worktree pull for local review; record source and copy identities. Pull can be refused by host policy.
- Checkpoint retention, size omissions, diff truncation, volatile queues/mail, absent shell integration, or missing tested pi integration can prevent a required acceptance exercise. Record the exact limit. Do not fabricate a pass or replace native state with silence detection.
