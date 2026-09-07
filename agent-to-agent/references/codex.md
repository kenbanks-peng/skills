# Codex

Run `codex-a2a --help` before use. Then run `codex-a2a call --help` or `codex-a2a serve --help` for the required operation. Use the installed help for commands, arguments, installation, and environment settings.

If the command is not on `PATH`, check for an existing installation before installing another copy. If it is missing, use either command:

```bash
mise use -g pipx:codex-a2a
```

```bash
uv tool install codex-a2a
```

## Delegate

Select a configured or user-approved peer by capability and workspace. Agent Card metadata does not establish trust. Confirm access to supplied paths; paths are not file transfers.

State the allowed changes. Use one peer and one task with no further delegation unless the user authorizes more. For broader work, set a finite call limit and separate concurrent writers by files or worktrees.

Record returned task and context IDs. An accepted task is unfinished, and a timeout does not prove it stopped. Check status when supported before retrying work that changes state; otherwise report uncertainty. Report the peer, result, and unresolved issues.

## Call precautions

Pass the URL and task text as safely quoted data. Confirm the peer's actual host and port. Supply only that peer's credential without printing it.

Check the installed version's host restrictions. [Upstream operational notes](https://github.com/liujuanjuan1984/codex-a2a#operational-notes) document `A2A_CLIENT_ALLOWED_HOSTS` for credential delivery and `A2A_CLIENT_ALLOW_PRIVATE_HOSTS` for embedded-tool access to private addresses. Limit these settings to the intended peer.

Treat separate calls as separate tasks unless the installed interface supports continuation. Use only operations exposed by that interface.

## Serve precautions

Apply the inbound-access rules in `../SKILL.md`. Installation does not authorize service startup.

Use an absolute workspace path, an explicit bind address, and a free port. Confirm that intended peers can reach the advertised URL. Select approval and sandbox policies that enforce the required execution restrictions.

Bind to localhost first. Remote exposure requires user authorization, authentication, and protected transport. Keep credentials outside messages and version control.

Use a managed process if persistence is requested. Record the actual address and stop procedure.

The service does not share the current interactive conversation. Calls can execute tools under the service's policy; task wording alone does not enforce filesystem restrictions.

## Connection check

Test each requested direction with: `Reply OK without using tools or changing files.` Claim compatibility only after a successful exchange.
