# Runtime and UI adapters

Load for a nondefault runtime/UI or interrupted dispatch startup. The default sandboxed procedure is in [SKILL.md](SKILL.md); uncertain state belongs in [recovery.md](recovery.md).

## Container adapters

Launch accepts `--runtime docker|podman|apple-container`. Override only for the actual installed runtime; the default is Apple `container` on macOS and Docker on Linux. `--config <path>` selects a genuine Workmux config override. Container configs must enable sandboxing. The config chooses the agent; launch records the observed type rather than overriding it. Local execution requires the approval procedure in [local-worker.md](local-worker.md).

Launch observes the exact container ID, host mount, guest worktree, and UI pane. When Workmux returns a null agent kind, it probes processes only inside that exact container; one live recognized process in the exact guest worktree supplies the agent type. This fallback needs Python 3 inside the container. Ambiguous identity fails closed. Host and guest paths are not interchangeable.

Keep the selected config and canonical repository/prompt paths stable on reopen. Run lifecycle operations in the target repository. Use project-qualified Workmux handles when cross-project names collide. No Lima or Windows adapter is supported.

## UI adapters

Herdr is selected by `HERDR_ENV=1`; otherwise use the active tmux session. Launch retains the original context and exact pane identity. In Herdr omit `--parent-session`; in tmux, use the dispatcher's actual session when placement matters. Ask when ambiguous rather than deriving it from the repository name. For unsupported backend behavior, read [capability troubleshooting](troubleshooting.md#capabilities) before mutation.

Finish can close only an exactly matched tmux pane on the saved server `socket_path`. Records without server identity leave UI housekeeping pending. Other backends require best-effort dispatcher closure in the original context; no unsupported command is guessed. UI closure never proves writer exit.

## Dispatch startup and Aven tab

Run `python3 <skill-directory>/scripts/dispatch.py startup <designated-task-ref>` in the original dispatcher host terminal after dispatch is requested, before launching workers. Task intake never invokes startup. A repository subdirectory is supported: routing resolves there first, while the Aven terminal starts at `git rev-parse --show-toplevel`. This is the target repository root, not `/` or a worker worktree. [open-tasks-tab.sh](scripts/open-tasks-tab.sh) delegates to this same adapter.

Startup uses read-only `aven doctor --json` to find the existing database, then task context to pin workspace/project keys. It executes `aven tui --db <absolute-db> --workspace <key> --project <key>` explicitly: changing directory must not infer a different database or project. Diagnosed overrides use `--db` and `--workspace`; missing Aven, database, UI identity, or unsupported UI protocol fails with a diagnostic. No database is initialized by the startup probe.

The stable run ID defaults to the designated task ref; `--run-id <id>` distinguishes separate runs. Reuse the same ID on resume. Records under `<common-git-dir>/dispatch-ui/<run-id>.json` save routing, dispatcher/server identity, creation intent, and Aven pane/tab identity. Herdr uses ancestry to select the current workspace, protocol 22 `layout.apply` with a new tab only (no `tab_id`), and the root command argv. tmux uses the exact socket/session and a detached new window. Labels are display data, never recovery selectors.

Repeated startup verifies the saved identity without creating a replacement or restarting Aven. Missing/moved panes, changed server/dispatcher identity, or interrupted creation stop for reconciliation. Creation intent is saved before mutation; even an interruption before the returned ID is saved never automatically repeats creation. Inspect `creation_attempted`, `created_tab_id` when present, and the original UI inventory. Preserve uncertain resources and reconcile the record manually; a label match alone is not ownership proof.

Aven and dispatcher tabs are run-owned, never worker cleanup targets. Keep them open across worker cleanup and resume. The legacy [close-tasks-tab.sh](scripts/close-tasks-tab.sh) now refuses ID-only closure; close a run-owned tab manually only after verifying its full saved identity in the original UI. Closure remains separate housekeeping.

### Host end-to-end check

Run in the actual dispatcher Workmux/Herdr host terminal, using the owning repository and known routing for this task (not a worker terminal):

```sh
cd /Users/kenbanks/Software/Public/skills/dispatch
python3 scripts/dispatch.py startup DSP-AR8K --run-id dsp-ar8k-host-check \
  --db /Users/kenbanks/Software/Public/skills/dispatch/.aven/tasks.db --workspace default
python3 scripts/dispatch.py startup DSP-AR8K --run-id dsp-ar8k-host-check
herdr session snapshot
aven context DSP-AR8K --db /Users/kenbanks/Software/Public/skills/dispatch/.aven/tasks.db --workspace default
```

Record both JSON results and the UI snapshot in Git metadata. Confirm one new Aven tab in the dispatcher's workspace, unchanged Aven identity on repeat, dispatcher label `dispatcher`, Aven cwd `/Users/kenbanks/Software/Public/skills`, and task DSP-AR8K visible in project dispatch. Confirm no root `.aven/tasks.db` was created and existing worker/demo tabs remain unchanged. After normal worker cleanup, confirm Aven and dispatcher identities still exist. This check requires host access; worker tests with a controlled socket are not end-to-end UI evidence.
