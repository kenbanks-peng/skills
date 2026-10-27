# Linux launcher and Pi

## Standard execution

Use `linux container -- pi "$ASSIGNMENT"` from the task checkout.
Use tuios new-window to give each Linux worker a visible pane.
The [worker procedure](workers.md) gives the complete launch command.

The launcher selects its configured image, mounts cwd, supplies the configured
Pi profile, and starts the command inside Linux. Container mode removes the
temporary container on exit. The mounted checkout and profile remain on disk.

## Launcher tools

Use these commands to inspect configuration or diagnose a launch failure:

```sh
linux --help
linux config show
linux config validate
linux container --dry-run -- pi
```

Dry-run prints the resolved runtime arguments. Use it to inspect image, mounts,
environment, and command. Start workers with the normal launch command.
Read the actual error for a failed launch and repair that specific dependency.
Use the configured image and profile as the starting point.

## Integration

The launcher can provide a tuios dock feed for container context. Agent state,
mail, queues, and checkpoints depend on the installed harness integration.
Inspect actual native reports before using state-dependent operations.
Use captured worker output and saved check evidence to confirm task results.

## Checks

Run project checks inside the launched Linux environment. Make checks.py and
its plan available there, then run it with --require-system Linux.
Save logs outside disposable checkouts. Record the tested candidate revision.
The dispatcher can review mounted files locally and run local integration
checks as an additional delivery step.

## Optional remote execution

Use configured tuios hosts when a task selects remote execution. Read
`tuios --skill hosts` for that workflow. A remote candidate can be copied into
a local native worktree for review and delivery:

```sh
tuios worktree pull "$REMOTE_SESSION" --repo "$REPO" --branch "$LOCAL_BRANCH" --name "$LOCAL_SESSION" --detach --json
tuios list-agents --all-hosts --json
```

Keep remote source identity and check evidence linked to the pulled candidate.
For the standard launcher workflow, work is already in the mounted checkout.
