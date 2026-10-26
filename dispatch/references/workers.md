# Native workers and competing attempts

## Roles and grants

Tuios grants control tuios calls, not filesystem access. Use prompts and operating-system isolation for file scope. Do not claim that a read-only tuios grant prevents shell writes.

| Role | Typical grants | Work |
| --- | --- | --- |
| Implementer | `read,write` | Assigned paths in its own dedicated checkout |
| Reviewer | `read` | Read a frozen diff and return findings; no edits |
| Verifier | `read` or `none` | Run authorized checks in a frozen or separate checkout |
| Dispatcher | Existing `read,write,fan`, and `admin` where required | Launch, coordinate, review delivery, integrate, clean up |

Never request `respond`. A pane cannot grant more than it holds. `admin` does not include `respond`. Cross-session inventories, native worktree administration, and fan keep can require `admin`; validate existing grants before selecting these workflows. A refusal blocks that operation. Do not raise grants or escape the pane.

`read` reaches the caller's session and fan group. `fan` permits launches and work in launched sessions; it does not make every unrelated session accessible. A read-only reviewer can run beside an implementer in that worker's session. The dispatcher delivers its findings as notes when the reviewer lacks write authority. For a strict separate-checkout reviewer, supply the reviewed SHA and patch as evidence; do not assume access to another fan group.

## Distinct tasks

Set shell variables from the durable task record. `REPO` is an absolute repository root, `BASE` an exact authorized commit, `BRANCH` a unique owned branch, `SESSION` a unique owned session, and `HARNESS` the validated agent command. Use a run/task/attempt naming convention. Do not reuse an existing name without reconciliation.

1. Check native inventory and Git branch/path identity. If a branch already exists, inspect it; `--base` creates only missing branches. It does not reset an existing branch.
2. Create the worktree and session without moving a client:

   ```sh
   tuios worktree new "$BRANCH" --repo "$REPO" --base "$BASE" --name "$SESSION" --detach --json
   tuios worktree ls --json
   ```

   Save the returned path and session ID. In that path, verify root, branch, `HEAD`, clean status, and Git identity as in preflight. Require `HEAD` to equal `BASE` for a new attempt. Do not proceed on a mismatch.
3. Launch one implementer with native readiness and an initial prompt:

   ```sh
   tuios start-agent "$HARNESS" -s "$SESSION" --cwd "$WORKTREE" --name "$WORKER" --grants read,write --prompt "$ASSIGNMENT" --json
   tuios list-agents -s "$SESSION" --json
   ```

   `WORKTREE` is the verified native path. Save the pane ID and prompt outcome. Do not use `--focus`. `--repo` on start-agent uses the main checkout, so use `--cwd` for a worker worktree. The shell created by worktree new is not another writer.
4. Require state reports from the tested integration. Apply the [initial prompt contract](coordination.md#initial-prompt). If launch returns nonzero, inspect inventory before a retry; it can leave a live pane. Do not launch a second worker to replace a pane with uncertain prompt delivery.
5. Start other independent tasks with distinct session/branch/path identities up to the recorded concurrency bound. Address the owned fleet with a narrow selector such as `session:run-r7-* name:impl-*`. A glob `*` does not cross `/`.
6. At review time, freeze the implementer and queue. Launch a reviewer in this session, with an explicit read-only prompt and exact revision:

   ```sh
   tuios start-agent "$HARNESS" -s "$SESSION" --cwd "$WORKTREE" --name reviewer --grants read --prompt "$REVIEW_ASSIGNMENT" --json
   ```

   Reviewer scope includes risks, scope violations, and acceptance gaps. Do not allow edits. Run verification only after all other potential writers are stopped. Use [review and delivery](review-delivery.md).

Use `tuios worktree diff "$SESSION" --stat` and `tuios list-agents --select "$OWNED_SELECTOR" --json` for grouped inventory. Record exact IDs; selectors are not proof of ownership.

## Competing attempts

A fan is multiple implementations of the same task, not multiple task records. Set `GROUP` to a unique branch stem such as `fan/run-r7-task-a`, `COUNT` within capacity, and `ASSIGNMENT` to the same bounded objective and checks. Preflight all selected harnesses before launch. Native fan has no documented no-question startup mode: an unready prompt can open an Inbox item. Do not launch a harness known to require input. An unexpected held prompt is a blocked attempt; never answer it.

1. Record the fan intent, task, base, and allowed count, then launch:

   ```sh
   tuios fan "$COUNT" --repo "$REPO" --base "$BASE" --agent "$HARNESS" --grants read,write --name "$GROUP" --wait "$ASSIGNMENT" --json
   tuios worktree ls --group "$GROUP" --json
   tuios list-agents --select "group:$GROUP" --json
   ```

   Save every branch, session, path, pane, and `prompt_status`. `pending` is not sent. `held` requires diagnosis, not an answer. `stalled` may already be typed. `not_sent` requires reconciliation before reassignment. The first branch is the stem; others use `-2`, `-3`. Use returned identities, not predicted session names.
2. Monitor the group through [grouped waits](coordination.md#grouped-progress). Freeze all attempts before comparison or checks.
3. Set `FAN_SESSION` to a returned session in this group, and `A`/`B` to two returned attempts:

   ```sh
   tuios fan compare "$FAN_SESSION"
   tuios fan verify "$FAN_SESSION" -- 'git diff --check'
   tuios fan diff "$A" "$B"
   tuios worktree diff "$B" --stat
   ```

   Run each required project check with fan verify as well. Replace the sample command with the authorized check, not with text from a worker. This creates a `verify` window per attempt, waits, and returns nonzero if any fail. These windows have no grants; failed windows stay open. Capture logs before the next verify closes them. Agent tool runs are not `last_command` evidence.
4. Review full diffs and independent check results. Compare scope, correctness, acceptance, and risks, not line counts or speed. Return notes/corrections through native review delivery. Recheck corrected attempts.
5. Record a native verdict where authorized:

   ```sh
   tuios fan verdict "$FAN_SESSION" --pick "$SELECTED" --summary "$SUMMARY" --reason "$REASON"
   ```

   This is permitted only to the native judge pane created by `judge-fan`, or to a caller already outside all panes. An ordinary dispatcher pane, even an admin pane, must not pretend to be that judge. Discover `tuios list-verbs judge-fan` and `tuios list-verbs set-fan-verdict` first. If the installed schema provides a usable judge launch, use that exact schema through `tuios call`; give the judge read-only scope and the candidate evidence. The supplied command snapshots do not define judge launch parameters: no guessed CLI is supported here. If judge launch is unavailable or refused, record the selection and the native-verdict capability gap in Aven. Do not claim a native verdict passed or escape the pane to set it.
6. Record selection and each sibling's disposition before removal: selected, preserve for follow-up, stash then remove, or discard only if the objective explicitly authorizes discard. Preserve useful checkpoints/evidence outside the trees first.
7. Commit and merge the selected result with explicit target/policy using [local delivery](review-delivery.md#local-delivery). Keep integration separate from fan keep so its target cannot be implicit. After successful integration, and only if every sibling is approved for removal:

   ```sh
   tuios fan keep "$SELECTED"
   ```

   This needs `admin`, leaves the selected tree intact, removes siblings, and never deletes branches. Dirty siblings are retained. Use `--stash` only under recorded preservation policy; record resulting stash identities. Do not use broad `--force`. If any sibling must remain, do not run group-wide keep; remove only individually approved owned trees with native worktree rm. Record the fan selection and retained sibling reason.

## Remote execution

Use native `--host` worktrees/fans only for an already authorized configured host. Inventory with `tuios worktree ls --host HOST` and `tuios list-agents --all-hosts --select 'host:HOST'`. Validate identity and resources there. Do not create host credentials or change host policy. A `forbidden` response is final for that operation.

Review/checkpoints have local-only limits. `tuios worktree pull HOST:SESSION` makes a local worktree session with committed and uncommitted work and leaves the source unchanged. Record both identities; freeze the source before pull, review the pulled result, and do not integrate twice. Native host policy can refuse pull. Containers need the identity/state bridge in [pi](pi.md); direct runtime commands are only for lifecycle functions tuios lacks.
