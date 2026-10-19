# Worker runtime

Read before creating or reconnecting workers.

## Environment

- Use `~/.config/workmux/agents.linux.yaml` by default. Use `~/.config/workmux/agents.macos.yaml` only when the user explicitly requests macOS or excludes sandboxing. Verify the selected file exists; a missing Linux setup is a blocker, not permission to fall back.
- Pass the selected file with `--config` for creation/reopening. Repository and prompt paths must remain canonical. Let it select the agent; record the actual agent type in Aven rather than passing an `--agent` override.
- Use Herdr when `HERDR_ENV=1`, otherwise the active tmux session when `TMUX` is set. In Herdr omit `--parent-session`. In tmux identify the dispatcher's actual session and pass it when placement matters; ask if ambiguous rather than deriving it from a repository name.
- Run Workmux lifecycle commands in the target repository. Qualify agent handles as `project:handle` when cross-project names collide.
- Preserve Aven's configured database/workspace defaults and project inference in worker prompts, including for sandboxed workers. Supply routing overrides only when diagnostics establish that the defaults select the wrong target.
- Do not run capability discovery or create a capability cache on a normal run. After an unsupported command, flag, or response schema, or a diagnosed tool change, use `dispatch_cli.py discover --cache <evidence>/cli.json --refresh` and targeted subcommand help. Resolve the incompatibility before another mutation.

## Launch and reconcile

Run from the target repository in the original multiplexer:

```sh
python3 <skill-directory>/scripts/dispatch.py launch APP-1234 \
  --base main --scope src/ --scope tests/ \
  --check '["python3", "-m", "unittest"]'
```

Supply the full task reference, explicit local base, repository-relative write scopes,
and required checks as argv arrays. Repeat `--scope` and `--check` as needed.
Do not supply prompt JSON, a project, a launch SHA, a branch, a handle, or receipt
paths. The command reads `aven context <ref> --json` with configured defaults.
Use `--db` or `--workspace` only for diagnosed routing overrides. Saved overrides
are reused when the same full reference is supplied.

The command derives the canonical repository and common Git directory. It locks
`<common-git-dir>/dispatch.lock` across linked worktrees, captures the explicit
base SHA, renders the assignment as literal JSON data plus the worker contract,
and saves launch intent before calling Workmux. Workmux receives the pinned SHA;
the record retains the explicit local integration base. This prevents a moving
base from changing the launch revision.

The default config is `~/.config/workmux/agents.linux.yaml`, with sandboxing
explicitly enabled. The default container CLI is Apple `container` on macOS and
Docker on Linux. Use `--runtime docker|podman|apple-container` for an actual runtime
override. Use `--config` only for a genuine config override. Local execution
(`--runtime local`) and a macOS config require explicit user approval through
`--allow-local`. Approved local execution on macOS defaults to
`~/.config/workmux/agents.macos.yaml`. Local execution on Linux requires an explicit
config override. The local config must disable sandboxing, and the UI must report
the actual local worktree root. A missing Linux
config is a blocker, not permission to fall back.
The selected config chooses the agent; the observed agent type is saved.

The saved record is `<common-git-dir>/dispatch-workers/<full-ref>/worker.json`.
The assignment, config snapshot, generated prompt copies, hashes, command errors,
and operation observations are retained beside it, outside worker worktrees.
Workmux also writes its own prompt copy inside the worktree; the command copies
it to evidence without deleting it. Follow the stop/archive guards before deleting
that source. Keep the common Git directory and its evidence on handoff.

Require `ok: true` before treating a launch as confirmed. The record contains
host and worker-visible worktree paths, the exact container ID and mount mapping,
the branch, actual agent type, and exact UI pane and multiplexer context. It does
not infer guest paths from host paths. A fast `done` status can confirm startup
even when the bounded `working` wait missed it; this is not task completion.
Missing or ambiguous identity remains an error with partial observations retained.

Read current resources without changing the saved record:

```sh
python3 <skill-directory>/scripts/dispatch.py inspect APP-1234
```

Save reconciled observations with `inspect APP-1234 --resume`. The first confirmed
observation also saves the explicit local base in Workmux branch metadata.
Repeating `launch APP-1234` reconciles the existing assignment. Neither action
creates, opens, replaces, or deletes a worker. Changed assignment inputs or saved
identities block continuation. A missing UI, container, or branch is not permission
to launch again. Keep the record and follow [recovery.md](recovery.md); do not delete
it to force a retry. Legacy launches without a saved record need explicit recovery,
not automatic adoption. Integration and closure still use the guarded procedures
below and the saved-record finish operation.

After confirmed launch, set Aven active/agent from the observed agent type, and
append the DISPATCH note using the saved record. Dispatch retains task-status
ownership. Monitor with bounded waits, such as
`workmux wait <handles> --any --timeout 120`. Set enclosing tool timeouts longer
than CLI timeouts. A timeout prompts inspection, not cancellation or completion.

## Stop, archive, and clean up

After successful integration, review one plan and authorize it once:

```sh
python3 <skill-directory>/scripts/finish_worker.py APP-1234
python3 <skill-directory>/scripts/finish_worker.py APP-1234 --authorize-finish
```

Authorization covers stop, prompt archive, strict worktree and branch removal,
best-effort housekeeping, a durable Aven report, and task completion. The command
uses the saved assignment and integration evidence. It holds the common Git
directory lock. Exclude writers that do not use this lock through completion.

The operation requires matching successful independent checks and the current
verified base. It confirms the exact recorded container and mount identity before
archive, removal, and completion. UI closure is never exit evidence. A container
missing before a confirmed stop is uncertain. A successful stop followed by an
independent listing can confirm auto-removal. Local/Lima writer exit is not
supported: preserve resources and obtain independent process evidence for review.

Only receipt-listed, unchanged, untracked, non-ignored generated prompts are
archived. Unknown, changed, tracked, ignored, dirty, or unsafe content remains.
Every mutation has saved intent and completion state. Archives, stop evidence,
the completion report, and the worker record remain in the common Git directory.

Retry with the same reference and no new authorization:

```sh
python3 <skill-directory>/scripts/finish_worker.py APP-1234 --inspect
python3 <skill-directory>/scripts/finish_worker.py APP-1234
```

Inspection does not change the record. Retry checks actual resources and performs
only remaining actions. A verified archive can account for a source removed
before interruption. A saved removal attempt can account for an absent worktree
or branch. Never recreate a deleted resource to rerun cleanup. Changed identity,
an unexpected absence, a changed plan, base movement, or uncertain exit requires
judgment; do not edit the record to force success.

Completion requires integration, independent checks, confirmed exit, and a saved
Aven report. Cleanup is not an extra completion gate. Safe retained resources
are listed in `pending_cleanup` with exact identity, evidence, owner, and next
action; they are not called complete. A failed Aven note or status command blocks
completion. Keep `completion.md` on write failure.

Housekeeping is separate. Exact tmux panes are checked before closure. Other UI
backends remain explicit housekeeping for the dispatcher to inspect in the
original context; no unsupported closure command is guessed. An optional saved
`cleanup_parent` permits only the exact immediate parent to be removed with
`rmdir`. UI or empty-parent failure does not block delivery. Report
`delivered`, `task_complete`, `pending_cleanup`, and `housekeeping` separately.
Retain container inspection access while cleanup remains pending.

## Compact reports

Use `dispatch_cli.py report --task <full-ref> --kind RESULT` for normal review. After review, use [guarded integration](merge.md); read its saved event and check evidence instead of polling for a worker merge response. Use `--after <ISO-timestamp>` when a fresh event is required. No matching note is a failure, not completion. Use `--save <new-file>` to retain the full response, and `--input <file>` to select another report without another Aven call. Explicit `--db` and `--workspace` are available only for diagnosed routing overrides.

## Persistent identifying-note checks

Use [check_identifying_notes.py](scripts/check_identifying_notes.py) with a JSON manifest containing `file` (relative to the manifest) and `notes` (at least two distinct exact strings). Each note must occur exactly once. Add the manifest and check command to the target repository's CI before closing a dispatch that must preserve identifying notes; one-time verification is not persistent protection.

Set the target manifest to the actual file and note text.

## Mechanical gates and evidence

Run helpers on the dispatcher; `python3 <skill-directory>/scripts/<script> --help` owns arguments and schemas. Write JSON inputs with the file-write tool, keeping content as data rather than shell source. Keep prompts, parameters, and evidence outside worker worktrees. Use the same canonical repository root throughout verification and cleanup. Persist JSON stdout even on failure so retained-resource paths remain recoverable.

Arrange the environment and dependencies for verification checks; they execute on the dispatcher, not in the worker sandbox. Reconcile retained verification checkouts and partial cleanup using [recovery.md](recovery.md) before retrying. Git cleanup does not manage Workmux sessions.

Helpers require Python 3 and Git; verification and recovery require POSIX.

## Dispatch and tasks tabs

During preparation, rename the dispatcher's current tab/window to `dispatch`, then run [scripts/open-tasks-tab.sh](scripts/open-tasks-tab.sh) to open Aven. Consult each script's `--help` for arguments. Record its returned resource ID and original multiplexer session/workspace in the run's Aven notes, including any ID emitted before a startup failure. On recovery, reuse that resource if it still exists; reconcile failed startup before retrying. After successful run completion, use [scripts/close-tasks-tab.sh](scripts/close-tasks-tab.sh) with the recorded ID in the original multiplexer. Retain it on handoff; never select a resource for closure by label.
