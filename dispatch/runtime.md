# Worker runtime

Read before creating or reconnecting workers. CLI help supplies syntax; this document supplies local execution policy.

## Environment

- Use `~/.config/workmux/agents.linux.yaml` by default. Use `~/.config/workmux/agents.macos.yaml` only when the user explicitly requests macOS or excludes sandboxing. Verify the selected file exists; a missing Linux setup is a blocker, not permission to fall back.
- Pass the selected file with `--config` for creation/reopening. The launch helper resolves the config path, including symbolic links, and records and uses the resolved path. Repository and prompt paths must remain canonical. Let it select the agent; record the actual agent type in Aven rather than passing an `--agent` override.
- Use Herdr when `HERDR_ENV=1`, otherwise the active tmux session when `TMUX` is set. In Herdr omit `--parent-session`. In tmux identify the dispatcher's actual session and pass it when placement matters; ask if ambiguous rather than deriving it from a repository name.
- Run Workmux lifecycle commands in the target repository. Qualify agent handles as `project:handle` when cross-project names collide.
- Preserve Aven's configured database/workspace defaults and project inference in worker prompts, including for sandboxed workers. Supply routing overrides only when diagnostics establish that the defaults select the wrong target.
- Run [dispatch_cli.py](scripts/dispatch_cli.py) `discover --cache <run-evidence>/cli.json` once per run. Reuse its compact capability output; it refreshes when executable identity changes. Use `--refresh` after a configuration/tool change. Inspect subcommand help only for missing capabilities or diagnosis; inspect configuration for execution mode, agent, sandbox, Aven routing, and base revision.

## Launch and reconnect

1. Capture the launch base with `git rev-parse --verify refs/heads/<base>^{commit}`, then generate the initial prompt with [worker_prompt.py](scripts/worker_prompt.py). Write corrections directly with the file-write tool. Before launching or sending any prompt, read it back and verify the complete content, including literal shell expressions, Markdown backticks, and newlines.
2. Launch with [launch_worker.py](scripts/launch_worker.py), using its `--help`. Supply the canonical repository root, branch, local base branch, `--launch-base` SHA used in the reviewed prompt, handle, config, prompt, and actual container runtime (`apple-container`, `docker`, or `podman`); use `local` only for explicitly approved unsandboxed workers. Pass `--parent-session` only in tmux. The adapter calls `workmux add` with the base branch name and emits a JSON receipt. Persist stdout outside the worktree, including on failure. Lima is not supported by this adapter; establish explicit process-stop evidence before using a separate Lima launch procedure.
3. Serialize `add` and `open` per repository; parallel work begins after startup. For retained workers, send a follow-up to the live session or use `workmux open <handle> --continue -P <prompt-file> --config <config-file>`.
4. Require `ok: true` in the receipt. The adapter waits for `working` and checks launch ancestry. Use its pre-launch SHA, observed host worktree, `worker_worktree`, container identity, and `ui` pane IDs/context. Paths in worker instructions come from worker-visible coordinates, not host-path guesses. An unavailable or ambiguous identity blocks confirmed dispatch. On failure retain the receipt and inspect status/capture before retrying; follow [recovery.md](recovery.md). After reopening a retained worker, refresh these observations with `launch_worker.py --observe-only --previous <original-receipt>` and the same launch arguments before further lifecycle operations.
5. Monitor with bounded waits, such as `workmux wait <handles> --any --timeout 120`. Set any enclosing tool timeout longer than the CLI timeout. A wait timeout prompts inspection, not cancellation of the worker or completion of the run.

## Stop, archive, and clean up

After base verification, perform these steps in order. Serialize lifecycle operations and prevent replacement writers throughout the sequence.

1. Review [stop_worker.py](scripts/stop_worker.py)'s dry run against the launch receipt. Run it with `--execute` and retain JSON stdout. Require `ok: true` and `stopped: true`. The helper checks the exact container identity and worktree mount, requests stop, and verifies exit. Workmux uses auto-removal: a successful stop plus an independent container listing can confirm removal. A missing container before a confirmed stop is uncertain, not success. Use `--previous` with retained stop evidence to recheck an auto-removed container.
2. Reconcile the recorded Workmux session/UI in the original multiplexer context. Closing a Herdr tab is not a container stop. For local workers, independently establish that all writers have exited; the container-stop helper refuses to certify local or Lima processes.
3. Review [archive_prompts.py](scripts/archive_prompts.py)'s dry run, supplying the receipt, stop evidence, and an archive directory outside the worktree. Then run with `--execute` and retain stdout. It copies only receipt-listed, untracked `.workmux/PROMPT-*.md` files, verifies content hashes, and removes originals after all copies pass. Unknown files remain. Refresh observations before stopping if a follow-up generated new prompts. On partial failure, use the retained archive and source paths to reconcile before retrying.
4. Run the existing cleanup dry run, then authorize execution. For container workers supply both `--receipt` and `--stop-evidence`; cleanup rechecks exit before removal. Keep strict dirty/untracked/ignored-file checks. Archive or resolve other artifacts explicitly instead of ignoring all of `.workmux/`.

These JSON files are trusted local evidence, not security attestations. Retain container inspection access until cleanup finishes.

## Compact reports

Use `dispatch_cli.py report --task <full-ref> --kind RESULT` for normal review. For merge responses use `--kind MERGE --authorization <id>`; check BLOCKED separately with the same ID if a merge fails. Use `--after <ISO-timestamp>` when a fresh event is required. No matching note is a failure, not completion. Use `--save <new-file>` to retain the full response, and `--input <file>` to select another report without another Aven call. Explicit `--db` and `--workspace` are available only for diagnosed routing overrides.

The installed Aven CLI has no filtered-note endpoint. This adapter fetches full JSON once, but emits only the selected note. Full history remains available for recovery; neither compact output nor Workmux status establishes task completion.

## Persistent identifying-note checks

Use [check_identifying_notes.py](scripts/check_identifying_notes.py) with a JSON manifest containing `file` (relative to the manifest) and `notes` (at least two distinct exact strings). Each note must occur exactly once. Add the manifest and check command to the target repository's CI before closing a dispatch that must preserve identifying notes; one-time verification is not persistent protection.

The local test suite checks `tests/fixtures/identifying-notes.json`. This fixture covers the two-worker smoke test, not an unspecified external target. Set the target manifest to the actual file and note text.

## Mechanical gates and evidence

Run helpers on the dispatcher; `python3 <skill-directory>/scripts/<script> --help` owns arguments and schemas. Write JSON inputs with the file-write tool, keeping content as data rather than shell source. Keep prompts, parameters, and evidence outside worker worktrees. Use the same canonical repository root throughout verification and cleanup. Persist JSON stdout even on failure so retained-resource paths remain recoverable.

Arrange the environment and dependencies for verification checks; they execute on the dispatcher, not in the worker sandbox. Reconcile retained verification checkouts and partial cleanup using [recovery.md](recovery.md) before retrying. Git cleanup does not manage Workmux sessions.

Helpers require Python 3 and Git; verification and recovery require POSIX. Worker contracts stay self-contained because dispatcher-local scripts and templates may be inaccessible inside worker sandboxes.

## Dispatch and tasks tabs

During preparation, rename the dispatcher's current tab/window to `dispatch`, then run [scripts/open-tasks-tab.sh](scripts/open-tasks-tab.sh) to open Aven. Consult each script's `--help` for arguments. Record its returned resource ID and original multiplexer session/workspace in the run's Aven notes, including any ID emitted before a startup failure. On recovery, reuse that resource if it still exists; reconcile failed startup before retrying. After successful run completion, use [scripts/close-tasks-tab.sh](scripts/close-tasks-tab.sh) with the recorded ID in the original multiplexer. Retain it on handoff; never select a resource for closure by label.

## Maintenance

Review upstream changes in a scratch location and selectively adopt them. Generated Workmux skills and `aven skill` output are not runtime dependencies.
