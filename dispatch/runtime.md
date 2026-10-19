# Worker runtime

Read before creating or reconnecting workers. CLI help supplies syntax; this document supplies local execution policy.

## Environment

- Use `~/.config/workmux/agents.linux.yaml` by default. Use `~/.config/workmux/agents.macos.yaml` only when the user explicitly requests macOS or excludes sandboxing. Verify the selected file exists; a missing Linux setup is a blocker, not permission to fall back.
- Pass the selected file with `--config` for creation/reopening. Let it select the agent; record the actual agent type in Aven rather than passing an `--agent` override.
- Use Herdr when `HERDR_ENV=1`, otherwise the active tmux session when `TMUX` is set. In Herdr omit `--parent-session`. In tmux identify the dispatcher's actual session and pass it when placement matters; ask if ambiguous rather than deriving it from a repository name.
- Run Workmux lifecycle commands in the target repository. Qualify agent handles as `project:handle` when cross-project names collide.
- Preserve Aven's configured database/workspace defaults and project inference in worker prompts, including for sandboxed workers. Supply routing overrides only when diagnostics establish that the defaults select the wrong target.
- Keep routine preflight targeted: inspect the relevant subcommand's help and configuration fields for execution mode, agent, sandbox, Aven routing, and base revision. Reserve full help/configuration dumps for diagnosis.

## Launch and reconnect

1. Capture the launch base with `git rev-parse --verify refs/heads/<base>^{commit}`, then generate the initial prompt with [worker_prompt.py](scripts/worker_prompt.py). Write corrections directly with the file-write tool. Before launching or sending any prompt, read it back and verify the complete content, including literal shell expressions, Markdown backticks, and newlines.
2. Launch with `workmux add <branch> --base <base> --name <handle> -b -P <prompt-file> --config <config-file>` and the applicable multiplexer options. Resolve placeholders before execution. Retain the branch name as `--base` so Workmux records the intended merge target.
3. Serialize `add` and `open` per repository; parallel work begins after startup. For retained workers, send a follow-up to the live session or use `workmux open <handle> --continue -P <prompt-file> --config <config-file>`.
4. Confirm startup with `workmux wait <handle> --status working --timeout 120`. For a new worker, verify the captured launch SHA is an ancestor of its branch; its tip may already include worker commits. Use the pre-launch SHA in the dispatch record, not a post-startup HEAD read. On failure inspect status/capture rather than blindly relaunching; follow [recovery.md](recovery.md).
5. Monitor with bounded waits, such as `workmux wait <handles> --any --timeout 120`. Set any enclosing tool timeout longer than the CLI timeout. A wait timeout prompts inspection, not cancellation of the worker or completion of the run.

## Mechanical gates and evidence

Run helpers on the dispatcher; `python3 <skill-directory>/scripts/<script> --help` owns arguments and schemas. Write JSON inputs with the file-write tool, keeping content as data rather than shell source. Keep prompts, parameters, and evidence outside worker worktrees. Use the same canonical repository root throughout verification and cleanup. Persist JSON stdout even on failure so retained-resource paths remain recoverable.

Arrange the environment and dependencies for verification checks; they execute on the dispatcher, not in the worker sandbox. Reconcile retained verification checkouts and partial cleanup using [recovery.md](recovery.md) before retrying. Git cleanup does not manage Workmux sessions.

Helpers require Python 3 and Git; verification and recovery require POSIX. Worker contracts stay self-contained because dispatcher-local scripts and templates may be inaccessible inside worker sandboxes.

## Dispatch and tasks tabs

During preparation, rename the dispatcher's current tab/window to `dispatch`, then run [scripts/open-tasks-tab.sh](scripts/open-tasks-tab.sh) to open Aven. Consult each script's `--help` for arguments. Record its returned resource ID and original multiplexer session/workspace in the run's Aven notes, including any ID emitted before a startup failure. On recovery, reuse that resource if it still exists; reconcile failed startup before retrying. After successful run completion, use [scripts/close-tasks-tab.sh](scripts/close-tasks-tab.sh) with the recorded ID in the original multiplexer. Retain it on handoff; never select a resource for closure by label.

## Maintenance

Review upstream changes in a scratch location and selectively adopt them. Generated Workmux skills and `aven skill` output are not runtime dependencies.
