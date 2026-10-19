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

1. Run `python3 <skill-directory>/scripts/worker_prompt.py --help` for initial-brief parameters and usage. Write its JSON input with the file-write tool, then generate the prompt after capturing the launch SHA in step 2. Generate merge authorizations with `merge_prompt.py` only after review and preflight; write corrections directly with the file-write tool. Keep prompt content as data, never interpolated into shell source. After generation or the final write, read back the complete prompt and verify its content, including literal shell expressions, Markdown backticks, and actual newlines, before launching or sending it. Send the merge procedure inline later, only with authorization.
2. Before each new worker launch, resolve `refs/heads/<base>` with `git rev-parse --verify refs/heads/<base>^{commit}` and record the full SHA in the prompt file as the launch base revision. Then use `workmux add <branch> --base <base> --name <handle> -b -P <prompt-file> --config <config-file>`, with the applicable multiplexer options. Resolve every placeholder before execution. Retain the branch name as `--base` so Workmux records the intended merge target.
3. Serialize `add` and `open` per repository; parallel work begins after startup. For retained workers, send a follow-up to the live session or use `workmux open <handle> --continue -P <prompt-file> --config <config-file>`.
4. Confirm startup with `workmux wait <handle> --status working --timeout 120`. For a new worker, verify the captured launch SHA is an ancestor of its branch; its tip may already include worker commits. Use the pre-launch SHA in the dispatch record, not a post-startup HEAD read. On failure inspect status/capture rather than blindly relaunching; follow [recovery.md](recovery.md).
5. Monitor with bounded waits, such as `workmux wait <handles> --any --timeout 120`. Set any enclosing tool timeout longer than the CLI timeout. A wait timeout prompts inspection, not cancellation of the worker or completion of the run.

## Mechanical gates and evidence

Run the Python helpers on the dispatcher with `python3 <skill-directory>/scripts/<script> --help`; CLI help owns arguments and schemas. Write JSON inputs with the file-write tool. Keep prompts, parameters, and evidence outside worker worktrees so they do not affect cleanliness checks. Use the same canonical repository root throughout verification and cleanup. Persist JSON stdout even on nonzero exit; failures can contain retained-resource paths needed for recovery.

- Before authorization: `git_preflight.py` checks the worker's Git preconditions; it does not replace diff review or the worker's just-in-time confirmations.
- After merge and at run closure: `verify_base.py` runs the supplied checks in a temporary checkout of a pinned base. Checks are trusted executable commands, not sandboxed; supply repository-relative argv and arrange any environment/dependencies they need. Failed or dirty checkouts are retained; reconcile them before retrying. Passing checks alone do not authorize cleanup.
- After successful verification: stop worker writers using the installed Workmux lifecycle commands, then review `cleanup_worker.py`'s dry run before explicit execution. Reconcile Workmux sessions separately; the helper removes Git resources only. Serialization remains necessary because inspection and deletion are not atomic. On partial cleanup, use recovery rather than forcing a rerun.
- For uncertain state: `recovery_snapshot.py` gathers read-only observations. Missing or failed observations are not proof of absence.
- For notes: `render_note.py` uses the templates and measured evidence. Closure notes require matching successful verification and executed cleanup results for the exact resources. Posting and task-status decisions remain with dispatch.

Helpers require Python 3 and Git; verification and recovery process isolation require POSIX. Do not assume dispatcher-local scripts or templates are accessible inside worker sandboxes: prompts inline worker procedures instead.

## Dispatch and tasks tabs

During preparation, rename the dispatcher's current tab/window to `dispatch`, then run [scripts/open-tasks-tab.sh](scripts/open-tasks-tab.sh) to open Aven. Consult each script's `--help` for arguments. Record its returned resource ID and original multiplexer session/workspace in the run's Aven notes, including any ID emitted before a startup failure. On recovery, reuse that resource if it still exists; reconcile failed startup before retrying. After successful run completion, use [scripts/close-tasks-tab.sh](scripts/close-tasks-tab.sh) with the recorded ID in the original multiplexer. Retain it on handoff; never select a resource for closure by label.

## Maintenance

These files are owned instructions, not installer output. Review upstream changes in a scratch location and selectively adopt them. Use `workmux <command> --help` for unfamiliar flags; generated Workmux skills and `aven skill` output are not runtime dependencies. Existing skills can remain installed during evaluation; explicitly invoke `dispatch` to select this workflow.
