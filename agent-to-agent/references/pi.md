# Pi

## Load the extension

Use `@bacnh85/pi-a2a`. Locate the installed package through Pi's package configuration, then read its `skills/a2a/SKILL.md` and README for the installed tools, configuration schema, and protocol behavior. If missing, run `pi install npm:@bacnh85/pi-a2a` using the required environment permissions.

Activate deferred A2A tools through the host's tool-discovery mechanism. If the current interactive session needs newly installed extensions, use `/reload` when the host can invoke it; ask the user only if that session must be retained and no programmatic reload is available. A fresh dedicated process can load the extension without a TUI reload.

## Discover and call

Use `a2a_peers` for discovery, `a2a_discover` to inspect a card, and `a2a_call` to send a task. Check the installed tool schema before calling. Select by workspace and capability; a matching name alone is insufficient.

Pi merges configured peers and live local-registry entries. The registry is `<piDir>/a2a_registry/<pid>.json`; resolve the actual Pi configuration directory from the running environment (`PI_CODING_AGENT_DIR` where set), rather than assuming every installation uses `~/.pi/agent`.

For an authenticated Codex endpoint, supply an explicit peer entry with its URL and `auth: {type: "bearer", token: ...}` through the installed client configuration. Prefer an in-memory entry for a temporary check when the installed client API supports it; persist named peers in the user's private Pi settings when ongoing access is requested. Preserve unrelated configuration and use the runtime's locking/update mechanism.

Automatic attachment of Pi's shared token only works for eligible known loopback peers and matching credentials. It does not provide Codex's separate bearer token. A direct URL alone is insufficient for an authenticated peer unless the client can resolve the correct credential.

Use `context_id` for supported follow-ups and record the returned context, task state, and reply. Check `a2a_history` or task status before retrying an uncertain call.

## Start inbound access without a TUI dependency

Reuse a live endpoint for the requested workspace. When setup is authorized and none is available, `/a2a-server start` works in an interactive host that can invoke it. Otherwise start a dedicated Pi RPC process from the absolute workspace with the extension loaded:

```text
A2A_SERVER_ENABLED=true
A2A_HOST=127.0.0.1
A2A_PORT=<selected-port>
A2A_BEARER_TOKEN=<loaded-privately>
pi --mode rpc --no-session
```

These are process environment settings, not a shell command containing a literal token. Use the installed `pi --help` for flags and explicit extension loading if automatic package discovery is unavailable. Keep RPC stdin open and drain stdout/stderr with a process supervisor or a small launcher; a process that exits on stdin EOF is not a live endpoint. Verify the registry entry and Agent Card before declaring readiness. Pi may fall back to another port, so use its actual URL.

Set startup options in the process environment or trusted user configuration. Current pi-a2a ignores security-sensitive inbound options in project-local `.pi/settings.json`; editing that file will not enable the server.

Inbound tasks create isolated Pi sessions, not messages in the original interactive session. Verify the installed extension's child-session tool policy before granting write tasks; parent CLI tool restrictions must not be assumed to propagate. For an ongoing service, use the lifecycle guidance in [connection.md](connection.md).

For Codex callers, the synchronous `SendMessage` recipe in [connection.md](connection.md) is the verified fallback for incompatible streaming serialization. A successful synchronous call does not establish streaming compatibility.

Source: installed package documentation and [pi-a2a upstream](https://github.com/bacnh85/pi-extensions/tree/main/pi-a2a).
