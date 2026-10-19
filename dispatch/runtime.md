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

1. Write each prompt file with the file-write tool, passing its content directly as data; this applies to initial briefs, corrections, and merge authorizations. Never interpolate prompt content into shell source or use JSON serialization as shell escaping. After the final write, read back the file and verify the complete intended content, including literal shell expressions, Markdown backticks, and actual newlines, before launching or sending it. Inline the worker contract so sandboxed workers need not access dispatcher-local skill paths. Send the merge procedure inline later, only with authorization.
2. Before each new worker launch, resolve `refs/heads/<base>` with `git rev-parse --verify refs/heads/<base>^{commit}` and record the full SHA in the prompt file as the launch base revision. Then use `workmux add <branch> --base <base> --name <handle> -b -P <prompt-file> --config <config-file>`, with the applicable multiplexer options. Resolve every placeholder before execution. Retain the branch name as `--base` so Workmux records the intended merge target.
3. Serialize `add` and `open` per repository; parallel work begins after startup. For retained workers, send a follow-up to the live session or use `workmux open <handle> --continue -P <prompt-file> --config <config-file>`.
4. Confirm startup with `workmux wait <handle> --status working --timeout 120`. For a new worker, verify the captured launch SHA is an ancestor of its branch; its tip may already include worker commits. Use the pre-launch SHA in the dispatch record, not a post-startup HEAD read. On failure inspect status/capture rather than blindly relaunching; follow [recovery.md](recovery.md).
5. Monitor with bounded waits, such as `workmux wait <handles> --any --timeout 120`. Set any enclosing tool timeout longer than the CLI timeout. A wait timeout prompts inspection, not cancellation of the worker or completion of the run.

## Dispatch and tasks tabs

During preparation, use the active multiplexer to rename the dispatcher's current tab/window to `dispatch` and open a separate tab/window named `tasks` running `aven` in the project's directory. Record the exact created tasks tab/window ID in the run's Aven notes. On recovery, reuse that recorded tab/window if it still exists. Close only that ID after successful run completion; retain it on handoff. Never identify a tab to close solely by the label `tasks`.

## Maintenance

These files are owned instructions, not installer output. Review upstream changes in a scratch location and selectively adopt them. Use `workmux <command> --help` for unfamiliar flags; generated Workmux skills and `aven skill` output are not runtime dependencies. Existing skills can remain installed during evaluation; explicitly invoke `dispatch` to select this workflow.
