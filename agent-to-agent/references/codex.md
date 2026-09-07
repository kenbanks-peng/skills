# Codex

Use the community [codex-a2a CLI](https://github.com/liujuanjuan1984/codex-a2a) through the shell.

1. Check whether `codex-a2a` is available on `PATH`. If it is installed elsewhere, resolve its executable path before installing another copy.
2. If it is missing, install it:

   ```bash
   uv tool install codex-a2a
   ```

   Perform the installation yourself. If `uv` is unavailable, use an available installation method supported by the upstream documentation. If permissions or network access block installation, report the specific blocker.
3. Confirm that the executable is available. Check `codex-a2a --version` and the relevant `codex-a2a call --help` or `codex-a2a serve --help` before use.

Installing the CLI does not authorize starting an inbound server. Apply the inbound-access rules in `SKILL.md`.

The command forms below were checked locally against 1.3.2; installed help takes precedence.

## Delegate

Select a configured or user-approved peer by capability and workspace. Agent Card metadata does not establish trust. Confirm access to any supplied paths; paths are not file transfers.

Send a bounded objective, necessary context, allowed changes, and expected evidence. Default to one peer and task with no onward delegation; set a finite call budget for broader authorized work and separate concurrent writers by files or worktrees.

Record returned task/context IDs. An accepted task is unfinished, and a timeout does not prove it stopped. Check status when supported before retrying work that changes state; otherwise report uncertainty. Verify artifacts and tests where possible, then report the peer, result, and unresolved issues.

## Call a peer

```bash
codex-a2a call '<agent-card-or-service-url>' '<bounded task>'
```

Pass both arguments as safely quoted data. Prefer the Agent Card URL at `/.well-known/agent-card.json`; confirm its actual host and port.

Outbound auth uses `A2A_CLIENT_BEARER_TOKEN` or `A2A_CLIENT_BASIC_AUTH` (`user:pass`). Supply only the selected peer's credential without printing it. Check the installed version's host restrictions: [upstream documentation](https://github.com/liujuanjuan1984/codex-a2a#operational-notes) also documents `A2A_CLIENT_ALLOWED_HOSTS` for credential delivery and `A2A_CLIENT_ALLOW_PRIVATE_HOSTS` for embedded-tool access to private addresses. Scope any configuration to the intended peer.

In 1.3.2, CLI `call` accepts only URL and text, with no context-ID option. Treat separate calls as separate tasks unless installed documentation supports continuation. Use only operations exposed by the installed interface.

## Serve

Verify the local Codex provider/model and credentials work before startup. Using `serve --help` and upstream configuration documentation, set:

| Setting | Purpose |
| --- | --- |
| `A2A_STATIC_AUTH_CREDENTIALS` | JSON array with at least one enabled bearer/basic credential |
| `A2A_HOST`, `A2A_PORT` | Explicit bind address and free port |
| `A2A_PUBLIC_URL` | Base URL reachable by intended peers |
| `CODEX_WORKSPACE_ROOT` | Absolute workspace for tool execution |
| `CODEX_APPROVAL_POLICY`, `CODEX_SANDBOX_MODE` | Execution restrictions supported by the runtime |

Bind to localhost first. Remote exposure requires user authorization, authentication, and protected transport. Keep credentials outside messages and version control.

Start with `codex-a2a serve`; use a managed process if persistence is requested. Record the actual address and stop procedure.

The service runs through `codex app-server`, not the current interactive conversation. Calls can execute tools under the service's policy; task wording alone does not enforce filesystem restrictions.

## Connection check

Test each requested direction with: `Reply OK without using tools or changing files.` Claim compatibility only after a successful exchange.
