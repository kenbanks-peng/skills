# Runtime and UI adapters

Load only for a nondefault runtime/UI or an optional tasks view. The default
sandboxed procedure is in [SKILL.md](SKILL.md); uncertain state belongs in
[recovery.md](recovery.md).

## Container adapters

Launch accepts `--runtime docker|podman|apple-container`. Override only for the
actual installed runtime; the default is Apple `container` on macOS and Docker
on Linux. `--config <path>` selects a genuine Workmux config override. Container
configs must enable sandboxing. The config chooses the agent; launch records the
observed type rather than overriding it. Local execution requires the approval
procedure in [local-worker.md](local-worker.md).

Launch observes the exact container ID, host mount, guest worktree, and UI pane.
When Workmux returns a null agent kind, it probes processes only inside that exact
container; one live recognized process in the exact guest worktree supplies the
agent type. This fallback needs Python 3 inside the container. Ambiguous identity
fails closed. Host and guest paths are not interchangeable.

Keep the selected config and canonical repository/prompt paths stable on reopen.
Run lifecycle operations in the target repository. Use project-qualified Workmux
handles when cross-project names collide. No Lima or Windows adapter is supported.

## UI adapters

Herdr is selected by `HERDR_ENV=1`; otherwise use the active tmux session. Launch
retains the original context and exact pane identity. In Herdr omit
`--parent-session`; in tmux, use the dispatcher's actual session when placement
matters. Ask when ambiguous rather than deriving it from the repository name.
For unsupported backend behavior, read
[capability troubleshooting](troubleshooting.md#capabilities) before mutation.

Finish can close only an exactly matched tmux pane on the saved server
`socket_path`. Records without server identity leave UI housekeeping pending.
Other backends require best-effort dispatcher closure in the original context;
no unsupported command is guessed. UI closure never proves writer exit.

## Optional tasks views

Open a view only when requested or useful. [open-tasks-tab.sh](scripts/open-tasks-tab.sh)
is a convenience, not a workflow gate. Save its exact returned ID and original
multiplexer session/workspace, including IDs emitted before a startup failure.
Reuse that resource on recovery.

[close-tasks-tab.sh](scripts/close-tasks-tab.sh) accepts the recorded ID in the
original context. Preserve unrelated UI. Closure failure stays visible as
housekeeping, separate from delivery and resource cleanup.
