# Linux workers

## Launch a task

Use the execution tool to run the following commands. Set REPO, BASE, BRANCH,
SESSION, WORKER, and ASSIGNMENT from the plan.

```sh
tuios worktree new "$BRANCH" --repo "$REPO" --base "$BASE" --name "$SESSION" --detach --json
tuios list-windows -s "$SESSION" --json
tuios new-window -s "$SESSION" "$WORKER" --keep-open --print-id --cwd "$WORKTREE" -- linux container -- pi "$ASSIGNMENT"
tuios list-windows -s "$SESSION" --json
```

Set WORKTREE to the path returned by worktree new. Save the returned full pane
IDs. The tool for Linux execution is `linux`: container mode mounts cwd at the
same path and runs the supplied command inside Linux. Pi receives ASSIGNMENT
as its initial prompt. Use the installed harness command in place of pi when
the task selects another harness.

Register the worker with workspace.py as linux-worker and --system Linux.
This records the launcher's execution contract. Register the starter shell
as auxiliary and close it after the worker is ready. See [scripts](automation.md).

Launch dependency-ready tasks up to the concurrency bound, each in its own
worktree. Include the goal, scope, checks, dependencies, and result format in
ASSIGNMENT. Ask the worker to save results and finish its turn for review.
Use a read-only assignment for a separate Linux reviewer when useful.

## Git worktree mounts

A linked worktree's .git file points to metadata in the original repository.
Make that directory available at the same path inside the container. Use
`git -C "$REPO" rev-parse --path-format=absolute --git-common-dir` to find it.
Add a mount for its parent repository when it is outside WORKTREE:

```sh
tuios new-window -s "$SESSION" "$WORKER" --keep-open --print-id --cwd "$WORKTREE" -- linux container --mount "$REPO:$REPO:rw" -- pi "$ASSIGNMENT"
```

Give each worker its own task checkout and use one integration owner.

## Observe and coordinate

Show active Linux workers in their tuios panes. Record each worker's
session/pane address and native state in the dashboard. Use native state,
queue, mail, and checkpoints where the installed harness integration supports
them. The launcher's dock feed provides container context; verify agent-state
integration separately when using state-dependent operations.

Capture actual worker output and project check results to establish completion.
Use the precise launch error to repair runtime, image, profile, or mount setup.
The standard launcher works independently of configured tuios remote hosts.

## Competing attempts

Create a separate Linux worker and checkout for each alternative. Compare
scope, diffs, and check results, then record the selected attempt in Aven.
Native fan can use a Linux-launcher harness when its installed readiness
integration supports that command. Use the direct launch procedure above
for other cases. Preserve useful alternatives on disk after pane cleanup.

## Visibility

Keep active worker panes visible and refresh the dashboard after meaningful
events. For workers in another session, use a native pane-view:

```sh
tuios new-window -s "$DISPATCH_SESSION" "view-$WORKER" --workspace "$WORKERS_WORKSPACE" --no-focus -- tuios pane-view -s "$SESSION" -w "$PANE" --size pane
```

Register each view and save its source address. Close the view when its source
finishes. Close the source worker after results and logs are saved.
Use one live view per worker and keep layout changes within the run's workspace.
