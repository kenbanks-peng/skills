# Pi and Linux execution

## Native integration

Use the installed tuios integration, not a wrapper that reports only launch
and exit. Check `tuios integration status pi --json` and
`tuios doctor agents` at the execution location. Repair with
`tuios integration install pi` when installation is part of the task.
Use the worker's actual Pi configuration directory.

Validate the selected HARNESS command from the native worktree directory, not
only the original repository. A launcher with project-relative configuration
can fail outside that repository. Use its supported explicit configuration or
the configured harness executable; do not change global settings.

Launch with `start-agent`. Check native state, harness identity, and completed
turn sequence. A ready screen is startup evidence, not proof that a task
finished. Use `peek-prompt` for blocked-prompt diagnosis only. Do not write
synthetic state over an integrated worker's reports.

## Linux workers through native hosts

A configured Linux tuios host is a first-class execution target. It provides
native agents, worktrees, state, mail, and fleet monitoring. Do not replace a
requested Linux worker with a local worker because local launch is easier.

```sh
tuios hosts --json
tuios hosts test "$HOST"
tuios worktree new "$BRANCH" --host "$HOST" --base "$BASE" --name "$SESSION_NAME" --detach --json
tuios worktree ls --host "$HOST" --json
tuios start-agent "$HARNESS" -s "$REMOTE_SESSION" --cwd "$REMOTE_WORKTREE" --name "$WORKER" --grants read,write --prompt "$ASSIGNMENT" --json
tuios list-agents --all-hosts --select "$OWNED_SELECTOR" --json
```

Run worktree new from the local repository. REMOTE_SESSION is HOST:SESSION from
the returned host/session identities; REMOTE_WORKTREE is the returned remote
path. Remote repository lookup uses its origin and configured repos_root.
Use `--clone` only when cloning that repository is needed and within scope.
Confirm that the requested base exists remotely; do not substitute another base.
Remote start-agent uses remote PATH; do not pass local `--env`.

Show these workers with [native pane views](workers.md#visibility), and include
host-qualified addresses in the dashboard. Monitor all hosts with
`subscribe --hosts` and bounded native waits for each owned host/group.
A link failure means stale/unknown state, not a new launch.

Native remote worktree sessions retain their integration context. A hosted
process pane (`new-window --host`) is another native option when a shared
local workspace is useful and a remote checkout already exists. Its cwd is
remote, and its integration must support hosted-pane identity. Do not confuse
a hosted process with a local shell running opaque SSH commands.

## Review and delivery from Linux

Run Linux acceptance checks on the source Linux checkout. Stop its writes, then
pull the candidate for local native review and delivery:

```sh
tuios worktree pull "$REMOTE_SESSION" --repo "$REPO" --branch "$LOCAL_BRANCH" --name "$LOCAL_SESSION" --detach --json
```

Pull copies commits and uncommitted files, without changing the source. Record
both identities and the tested revision. Use local review/checkpoints/ship on
the returned local candidate. A corrected remote candidate needs a new pull
identity; do not review or merge a stale copy. Close the pulled session's
shell after native delivery no longer needs its identity. Keep the pulled
session and its shell hidden from creation; --detach alone does not prove
invisibility. Review, ship, and integrated checks must not open visible windows.

## Containers

Containers can be execution targets, not a reason to hide workers. Prefer a
configured native Linux host for orchestration. If the objective specifically
requires containers, show only the Linux worker in its permitted worker
window. Run container setup, checks, and teardown windowlessly or hidden.
Check state, mail, worktree paths, and review at that boundary before relying
on them. Native host support does not certify arbitrary container
transport. Do not invent a custom bridge or silently drop container isolation.
Report the exact missing integration if the supplied container path cannot
provide it; keep supported independent work moving.
