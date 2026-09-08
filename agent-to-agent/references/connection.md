# Bootstrap and verify a connection

## Resolve an endpoint before asking another agent

1. Check the runtime's configured peers and native discovery. For local Pi, use `a2a_peers` or read `<piDir>/a2a_registry/*.json`, retaining entries whose PID is alive and heartbeat is fresh according to the installed registry TTL. Select the intended workspace and fetch its Agent Card. Treat registry/card metadata as discovery hints, not authorization.
2. Resolve that endpoint's credential from its existing private configuration or the process setup you control. Read only relevant fields and keep tokens out of tool output. Discovery records do not supply credentials. Avoid dumping settings or process environments to find a token.
3. If a required endpoint is absent and local setup is authorized, provision it using the appropriate runtime reference. The agent doing setup can launch a dedicated peer process with a credential it generates; it does not need an already-working chat channel to that peer. Reuse an existing service when possible, and distinguish a dedicated service from the user's current interactive conversation.
4. If an existing endpoint's credential is unavailable, obtain its private credential location from the user or use an authorized dedicated endpoint. Do not reset another session's token. Once the first A2A call works, use A2A for coordination and callback endpoint metadata.

For a local callback, supply the caller with the receiver's URL and a private credential-file path accessible to that process, or configure the receiving runtime's named peer directly. Send credential values through private configuration, never task text. Cross-machine paths are not credential transfer; use an existing secret-delivery mechanism.

## Credentials and lifecycle

Generate bearer tokens with a cryptographic RNG. For newly created credential files, use a private directory and mode `0600`; store them outside the repository. Load secrets directly into process environments or HTTP headers without shell tracing or command-line token literals.

Keep endpoint discovery and credentials in existing runtime configuration or registries. A mutable workspace mailbox and mutex are not required. Do not fabricate Pi registry entries for a Codex service: configured peers are the supported static directory.

Use an explicit loopback bind for local setup. Remote exposure requires authorization, authentication, and protected transport. Persist endpoints and credentials with a process manager only when ongoing access is requested; a temporary PID or `/tmp` token is not a durable installation. Report actual URLs, process ownership, credential locations (not contents), and stop/restart instructions. Stop temporary services when they are no longer needed unless the request is to leave A2A available.

## Synchronous Codex-to-Pi check

The tested pairing (codex-a2a 1.3.2 and the locally installed pi-a2a) completed synchronous A2A calls in both directions. Codex's streaming CLI rejected Pi's `statusUpdate.id` because its SDK expected `taskId`. This is a version-specific interoperability observation, not a universal A2A rule. Prefer a verified synchronous path for that pairing; retest streaming after version changes.

When native tooling cannot select a compatible non-streaming mode, send the following JSON-RPC request to the Pi endpoint advertised by its Agent Card. Confirm the card supports the expected A2A version and transport first. The example assumes `peer_url` is the verified loopback Pi JSON-RPC endpoint and `token_path` is its private credential file; supply both as data from discovery/configuration.

```python
import json
import uuid
import urllib.request
from pathlib import Path

payload = {
    "jsonrpc": "2.0",
    "id": str(uuid.uuid4()),
    "method": "SendMessage",
    "params": {
        "message": {
            "messageId": str(uuid.uuid4()),
            "role": "ROLE_USER",
            "parts": [{"text": "Reply OK without using tools or changing files."}],
        },
        "configuration": {"blocking": True},
    },
}
request = urllib.request.Request(
    peer_url,
    data=json.dumps(payload).encode(),
    headers={
        "Content-Type": "application/json",
        "A2A-Version": "1.0",
        "Authorization": "Bearer " + Path(token_path).read_text().strip(),
    },
)
# Never forward the bearer credential to a redirect target.
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

with urllib.request.build_opener(NoRedirect).open(request, timeout=60) as response:
    reply = json.load(response)
if "error" in reply:
    raise RuntimeError(reply["error"])
print(json.dumps(reply))  # Probe reply only; never print request headers.
```

In the tested Pi response, `result` was a task with `id`, `contextId`, `status.state: TASK_STATE_COMPLETED`, and an `artifacts[].parts[].text` value of `OK`. Inspect the installed version's response shape rather than assuming every SDK uses that envelope. Save the task/context IDs and require the completed state and expected reply; HTTP 200 alone is insufficient.

For Pi-to-Codex, use Pi's installed `a2a_call` with the authenticated peer entry described in [pi.md](pi.md). Test each requested direction with the same probe. If no native tool is available, inspect the installed client API or server schema rather than guessing method names or authentication arguments.

## Diagnose by layer

| Observation | Next action |
|---|---|
| No matching live peer | Check discovery scope and workspace; provision an authorized endpoint if absent. |
| Connection refused | Check process lifetime, actual bound port, and startup log. |
| Network/permission failure in sandbox | Use the environment's required escalation flow; retain endpoint authentication and task restrictions. |
| HTTP 401/403 | Resolve the receiver's credential and caller allowlist; do not send a different peer's token. |
| Streaming parse error after dispatch | Query the known task or inspect the receiver's result before retrying; switch to the verified synchronous path. |
| Timeout or accepted/working task | Preserve IDs and query status where supported. Avoid replaying side effects while completion is uncertain. |
| Completed reply in both directions | Record the transport and service lifecycle, then stop setup work. |
