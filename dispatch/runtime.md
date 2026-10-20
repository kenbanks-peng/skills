# Runtime and UI adapters

Load for a nondefault runtime/UI or interrupted dispatch startup. The default sandboxed procedure is in [SKILL.md](SKILL.md); uncertain state belongs in [recovery.md](recovery.md).

## Container adapters

Launch accepts `--runtime docker|podman|apple-container`. Override only for the actual installed runtime; the default is Apple `container` on macOS and Docker on Linux. `--config <path>` selects a genuine Workmux config override. Container configs must enable sandboxing. The config chooses the agent; launch records the observed type rather than overriding it. Select native macOS with `--platform darwin`; this requires a macOS host and uses the local runtime. The default `--platform linux` uses sandboxed Linux workers. Launch creates missing platform configs with agent `pi` and the matching sandbox setting, preserving existing files. Local configs must disable sandboxing, and the observed UI workdir must match the local worktree. Automatic finish cannot prove local writer exit: retain resources and obtain independent exact process evidence rather than inferring exit from UI closure.

Launch observes the exact container ID, host mount, guest worktree, and UI pane. When Workmux returns a null agent kind, it probes processes only inside that exact container; one live recognized process in the exact guest worktree supplies the agent type. This fallback needs Python 3 inside the container. Ambiguous identity fails closed. Host and guest paths are not interchangeable.

Keep the selected config and canonical repository/prompt paths stable on reopen. Run lifecycle operations in the target repository. Use project-qualified Workmux handles when cross-project names collide. No Lima or Windows adapter is supported.

## UI adapters

Herdr is selected by `HERDR_ENV=1`; otherwise use the active tmux session. Launch retains the original context and exact pane identity. In Herdr omit `--parent-session`; in tmux, use the dispatcher's actual session when placement matters. Ask when ambiguous rather than deriving it from the repository name. For unsupported backend behavior, read [capability troubleshooting](troubleshooting.md#capabilities) before mutation.

Finish can close only an exactly matched tmux pane on the saved server `socket_path`. Records without server identity leave UI housekeeping pending. Other backends require best-effort dispatcher closure in the original context; no unsupported command is guessed. UI closure never proves writer exit.

## Dispatch startup and Aven tab

Run `python3 <skill-directory>/scripts/dispatch.py startup <designated-task-ref>` in the original dispatcher host terminal after dispatch is requested, before launching workers. Task intake never invokes startup. A repository subdirectory is supported; startup and the Aven terminal run from the repository root (`git rev-parse --show-toplevel`). This is the target repository root, not `/` or a worker worktree. [open-tasks-tab.sh](scripts/open-tasks-tab.sh) delegates to this same adapter.

Startup uses read-only `aven doctor --json` to check the existing database, then reads task context and saves the project. It executes `aven tui --project <saved-project>` from the target repository root. Missing Aven, database, task context, UI identity, or unsupported UI protocol fails with a diagnostic. No database is initialized by the startup probe.

The stable run ID defaults to each command's task ref. For multiple worker tasks, pass the same `--run-id <id>` to startup and every launch. Resume uses the saved worker run ID and rejects a different override. Launch verifies completed startup and the exact open tab before starting or resuming a worker. It registers worker refs in the run record before creation. Records under `<common-git-dir>/dispatch-ui/<run-id>.json` save the project, dispatcher/server identity, creation intent, Aven pane/tab identity, startup confirmation, and worker refs. Herdr uses ancestry to select the current workspace, protocol 22 `layout.apply` with a new tab only (no `tab_id`), and the root command argv. tmux uses the exact socket/session and a detached new window. Labels are display data, never recovery selectors.

Repeated startup verifies the saved identity without creating a replacement or restarting Aven. Missing/moved panes, changed server/dispatcher identity, or interrupted creation stop for reconciliation. Creation intent is saved before mutation; even an interruption before the returned ID is saved never automatically repeats creation. Inspect `creation_attempted`, `created_tab_id` when present, and the original UI inventory. Preserve uncertain resources and reconcile the record manually; a label match alone is not ownership proof.

Aven and dispatcher tabs are run-owned, never worker cleanup targets. Keep them open across worker cleanup and resume. When all run work, cleanup, and final SUMMARY reporting are finished, close the run's Aven tab. Closure checks every indexed worker and matching saved record, including done tasks. It requires confirmed delivery, live done status, absent worker resources, completed cleanup/housekeeping, and a SUMMARY added since startup. A missing indexed record blocks closure. Authorization confirms SUMMARY content and work outside the saved records:


```sh
python3 <skill-directory>/scripts/dispatch.py close-run <designated-task-ref> --authorize-close
```

Use the same `--run-id <id>` as startup, if set. [close-tasks-tab.sh](scripts/close-tasks-tab.sh) accepts the same task/run/authorization arguments; labels and pane IDs are not accepted. Closure uses the saved socket and exact pane/tab identity, refuses changed identities or extra panes, and confirms removal. The dispatcher and unrelated tabs stay open. Interrupted closure can be retried with the same command; saved intent permits reconciliation without a second close when the target is already absent. Do not close on a blocked or partial handoff. Report any closure failure as pending housekeeping. A closed run cannot be restarted; use a new run ID for new work.

### Host end-to-end check

Run in the actual dispatcher Workmux/Herdr host terminal, in the owning repository (not a worker terminal):

```sh
cd /Users/kenbanks/Software/Public/skills/dispatch
python3 scripts/dispatch.py startup DSP-AR8K --run-id dsp-ar8k-host-check
python3 scripts/dispatch.py startup DSP-AR8K --run-id dsp-ar8k-host-check
herdr session snapshot
aven context DSP-AR8K
```

Record both JSON results and the UI snapshot in Git metadata. Confirm one new Aven tab in the dispatcher's workspace, unchanged Aven identity on repeat, dispatcher label `dispatcher`, Aven cwd matching `git rev-parse --show-toplevel`, and task DSP-AR8K visible in project dispatch. Confirm no root `.aven/tasks.db` was created and existing worker/demo tabs remain unchanged. After normal worker cleanup, confirm Aven and dispatcher identities still exist. After all work and reporting finish, run `python3 scripts/dispatch.py close-run DSP-AR8K --run-id dsp-ar8k-host-check --authorize-close`. Confirm only the saved Aven tab is removed and the dispatcher remains. This check requires host access; worker tests with a controlled socket are not end-to-end UI evidence.
