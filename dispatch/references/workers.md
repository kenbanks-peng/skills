# Native workers

## Distinct tasks

Set REPO, BASE, BRANCH, SESSION, WORKER, HARNESS, and ASSIGNMENT from the plan. Use unique
run/task names. Read returned identities rather than predicting paths or IDs.

```sh
tuios worktree new "$BRANCH" --repo "$REPO" --base "$BASE" --name "$SESSION" --detach --json
tuios worktree ls --json
tuios list-windows -s "$SESSION" --json
tuios set-session-space -s "$SESSION" "$RUN"
tuios start-agent "$HARNESS" -s "$SESSION" --cwd "$WORKTREE" --name "$WORKER" --grants read,write --prompt "$ASSIGNMENT" --json
tuios list-agents -s "$SESSION" --json
```

WORKTREE is the returned native path. Record the starter shell ID from the
pre-launch inventory. When the worker is ready, close that unused shell by ID;
do not leave it taking most of the workspace. Do not close the worker.
Use the same naming/space policy for the orchestration session where appropriate.

Launch dependency-ready tasks up to the concurrency bound, each with its own
checkout. Names should identify task and role, for example impl-parser-linux.
Use [Linux execution](pi.md) when the environment requires it.

ASSIGNMENT contains task/attempt, goal, scope, checks, dependencies, and result
format. Tell the worker to report blockers without human questions, stop after
the turn, and leave commit/integration to the dispatcher. Keep prompts short.
Use the installed harness integration for accurate state and checkpoints.

Do not spawn a reviewer for a trivial file solely to fill a role. The dispatcher
can independently review. For substantial changes, start a read-only reviewer
against the exact candidate; close it after its findings are saved.

## Competing attempts

Use fan for different solutions to one task, not for unrelated tasks.

```sh
tuios fan "$COUNT" --repo "$REPO" --base "$BASE" --agent "$HARNESS" --grants read,write --name "$GROUP" --wait "$ASSIGNMENT" --json
tuios list-agents --select "group:$GROUP" --json
tuios wait-for agent-state --select "group:$GROUP" --until idle,done,errored,needs_input --every --timeout 3600000 --json
tuios fan compare "$FAN_SESSION"
tuios fan verify "$FAN_SESSION" -- 'git --no-pager diff --check'
tuios fan diff "$A" "$B"
```

Run project checks with fan verify too. Compare correctness, scope, and tests;
record the selected attempt and the disposition of the others.
Use the native judge/verdict when available to this caller. Discover
`judge-fan` through installed verb help; do not invent its parameters or
impersonate a judge. If verdict is unavailable, record the selection in Aven
and report that limitation.

Send corrections with native review notes or queue. Commit and integrate the
selected attempt with ship. Then use `tuios fan keep "$SELECTED"` when the
other attempts can be removed. Preserve useful dirty alternatives with native
stash/removal policy. Capture verify logs and close completed verify panes
between checks; fan verify may replace its prior verify windows.

## Visibility

All owned workers must appear in the dashboard with host, state, and a usable
session/pane address. Native inventories must include every selected host.
Keep worktree sessions intact; moving an agent can change its coordination
context. A dashboard row alone is not a live worker view.

For live views of workers in other sessions, use a bounded set of native
pane-view panes in a named workers workspace:

```sh
tuios new-window -s "$DISPATCH_SESSION" "view-$WORKER" --workspace "$WORKERS_WORKSPACE" --no-focus -- tuios pane-view -s "$SESSION" -w "$PANE" --size pane
```

SESSION may be HOST:SESSION. These are views, not new workers. Keep their IDs,
do not type into them, and close them when the source worker finishes.
Use at most the active concurrency count; do not duplicate a view already open.
Name workspaces, keep the dashboard in the dispatcher's visible workspace, and
use native tiling/equalize only on the run's own attached workspace.
Do not switch the person's client or rearrange unrelated workspaces.
