# Native workers

## Distinct tasks

Set REPO, BASE, BRANCH, SESSION, WORKER, HARNESS, and ASSIGNMENT from the plan. Use unique
run/task names. Read returned identities rather than predicting paths or IDs.
Before these commands, verify that starter shells and local task sessions stay
hidden from creation. `--detach` is not proof of hidden windows. If native
launch cannot meet the window rule, use a supported windowless path or block
that launch. Only Linux worker windows may be visible, besides dispatch/Aven.

```sh
tuios worktree new "$BRANCH" --repo "$REPO" --base "$BASE" --name "$SESSION" --detach --json
tuios worktree ls --json
tuios list-windows -s "$SESSION" --json
tuios set-session-space -s "$SESSION" "$RUN"
tuios start-agent "$HARNESS" -s "$SESSION" --cwd "$WORKTREE" --name "$WORKER" --grants read,write --prompt "$ASSIGNMENT" --json
tuios list-agents -s "$SESSION" --json
```

WORKTREE is the returned native path. Register every returned window through
workspace.py, then audit. Register the worker as linux-worker only after host
preflight confirms Linux. Record the starter shell ID from pre-launch inventory.
After readiness, use workspace.py close for the owned unused starter, with
--evidence-saved. It must stay hidden until closure; otherwise block launch.
Keep the worker only while the run is active. See [scripts](automation.md).
Use the same naming/space policy for the orchestration session where appropriate.

Launch dependency-ready tasks up to the concurrency bound, each with its own
checkout. Names should identify task and role, for example impl-parser-linux.
Use [Linux execution](pi.md) when the environment requires it.

ASSIGNMENT contains task/attempt, goal, scope, checks, dependencies, and result
format. Tell the worker to report blockers without human questions, stop after
the turn, and leave commit/integration to the dispatcher. Require windowless
checks and no visible helper windows. Keep prompts short.
Use the installed harness integration for accurate state and checkpoints.

Do not spawn a reviewer for a trivial file solely to fill a role. The dispatcher
can independently review. For substantial changes, start a read-only reviewer
against the exact candidate without a window or in a verified hidden window;
close it after its findings are saved. A reviewer is not a visible worker slot.

## Competing attempts

Use fan for different solutions to one task, not for unrelated tasks.
Confirm that fan launch, verify, and judge create no visible auxiliary windows.
If verify cannot run hidden, run the same checks windowlessly per checkout
instead. Do not run the verify example below until this condition is met.

```sh
tuios fan "$COUNT" --repo "$REPO" --base "$BASE" --agent "$HARNESS" --grants read,write --name "$GROUP" --wait "$ASSIGNMENT" --json
tuios list-agents --select "group:$GROUP" --json
tuios wait-for agent-state --select "group:$GROUP" --until idle,done,errored,needs_input --every --timeout 3600000 --json
tuios fan compare "$FAN_SESSION"
tuios fan verify "$FAN_SESSION" -- 'git --no-pager diff --check'
tuios fan diff "$A" "$B"
```

Prefer checks.py on each candidate checkout for windowless project checks.
Use fan verify only on a separately verified hidden path. Compare scope and tests;
record the selected attempt and the disposition of the others.
Use the native judge/verdict when available to this caller. Discover
`judge-fan` through installed verb help; do not invent its parameters or
impersonate a judge. If verdict is unavailable, record the selection in Aven
and report that limitation.

Send corrections with native review notes or queue. Commit and integrate the
selected attempt with ship. Then use `tuios fan keep "$SELECTED"` when the
other attempts can be removed. Preserve useful dirty alternatives with native
stash/removal policy. Save verify logs and close hidden verify windows after
each check, pass or fail. Never expose verify windows.

## Visibility

All owned workers must appear in the dashboard with host, state, and a usable
session/pane address. Native inventories must include every selected host.
Keep worktree sessions intact; moving an agent can change its coordination
context. A dashboard row alone is not a live worker view.

Only active Linux workers may have visible worker windows. Keep local workers
hidden. Do not add a view when the Linux worker already has a visible window.
For Linux workers in other sessions, use a bounded set of native
pane-view panes in a named workers workspace:

```sh
tuios new-window -s "$DISPATCH_SESSION" "view-$WORKER" --workspace "$WORKERS_WORKSPACE" --no-focus -- tuios pane-view -s "$SESSION" -w "$PANE" --size pane
```

SESSION may be HOST:SESSION. These are views, not new workers. Keep their IDs,
do not type into them. Register each view as linux-worker and use workspace.py
close when the source worker finishes. Use one visible view per Linux worker.
At run end, close the source worker windows too, after saving their results.
Use at most the active concurrency count; do not duplicate a view already open.
Name workspaces, keep the dashboard in the dispatcher's visible workspace, and
use native tiling/equalize only on the run's own attached workspace.
Do not switch the person's client or rearrange unrelated workspaces.
