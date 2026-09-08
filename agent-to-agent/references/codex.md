# Codex

## Inspect the installed runtime

Run `codex-a2a --help`, then `codex-a2a call --help` or `codex-a2a serve --help` for the operation. Installed help and source take precedence over examples here. Check `codex --version` and provider readiness before serving. The adapter does not provision model credentials.

If `codex-a2a` is absent from PATH, locate an existing installation first. Otherwise install using the environment's existing manager: `uv tool install codex-a2a` or `mise use -g pipx:codex-a2a`.

## Discover and call

Follow [connection.md](connection.md) to resolve the peer URL and credential. Codex can read Pi's existing local registry; it does not need Pi to announce its endpoint in a conversation file.

For compatible peers, use `codex-a2a call <agent-card-url> <task-text>`. Pass both arguments as safely quoted data. Supply the selected peer's credential through `A2A_CLIENT_BEARER_TOKEN` or `A2A_CLIENT_BASIC_AUTH`, without printing it. Set `A2A_CLIENT_ALLOWED_HOSTS` to the intended host; use `A2A_CLIENT_ALLOW_PRIVATE_HOSTS=true` when the installed client's private-address policy requires it. Host allowlisting does not bypass the execution environment's network sandbox.

For Pi, use the synchronous `SendMessage` recipe in [connection.md](connection.md) when the installed streaming client is incompatible. In the tested codex-a2a 1.3.2 installation, the CLI hardcoded streaming and exposed no non-streaming switch. A direct authenticated JSON-RPC request is the fallback; do not invent a CLI flag.

Record task/context IDs and final reply. An accepted task is unfinished; a timeout or parser failure does not prove it stopped. Check task status before retrying work that changes state. Treat separate calls as separate tasks unless the interface supports continuation.

## Start inbound access

Apply the authorization and lifecycle rules in [SKILL.md](../SKILL.md) and [connection.md](connection.md). Use an absolute workspace path, a free port, and an explicit loopback bind. Configure the following through a process environment, loading the token from a private credential source:

| Setting | Purpose |
|---|---|
| `A2A_HOST=127.0.0.1` | Localhost bind |
| `A2A_PORT=<free-port>` | Actual selected port |
| `A2A_PUBLIC_URL=http://127.0.0.1:<free-port>` | Advertised base URL |
| `CODEX_WORKSPACE_ROOT=<absolute-workspace>` | Tool execution workspace |
| `A2A_STATIC_AUTH_CREDENTIALS` | JSON array containing an enabled bearer credential: `id`, `scheme: bearer`, `token`, `principal` |
| `CODEX_APPROVAL_POLICY`, `CODEX_SANDBOX_MODE` | Enforced execution restrictions; `never` plus `read-only` was used for the connection probe |

Run `codex-a2a serve`. Verify the listener and authenticated Agent Card at `/.well-known/agent-card.json` before advertising readiness. `A2A_EXECUTION_*` discovery metadata does not enforce the subprocess execution policy.

The default database is under `<workspace>/.codex-a2a/`. In the tested 1.3.2 installation, startup failed with `No module named 'greenlet'`. If this exact failure occurs, install `greenlet` into the adapter's Python environment using its package manager, or into a private temporary target loaded through `PYTHONPATH` with the same Python ABI. Repair the dependency before retrying; deleting the database does not address this error.

If `codex app-server` fails to initialize, inspect the underlying startup error and provider configuration. An environment sandbox may block runtime state writes, child startup, or localhost networking. Use the host's required escalation flow for a demonstrated permission failure rather than weakening inbound task restrictions.

The inbound service executes separate Codex sessions; it does not share the current interactive conversation. Pass task context explicitly. Publish the endpoint through an existing peer configuration or an established A2A connection, with credentials supplied privately as described in [connection.md](connection.md).

Sources: installed `--help`/source and [codex-a2a upstream](https://github.com/liujuanjuan1984/codex-a2a).
