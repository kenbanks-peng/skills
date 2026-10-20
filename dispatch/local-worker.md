# Explicitly approved local workers

Load only after the user approves unsandboxed execution. A missing sandbox setup is a blocker, not implicit approval. Follow the normal [dispatch workflow](SKILL.md) with these launch overrides:

```sh
python3 <skill-directory>/scripts/dispatch.py launch APP-1234 \
  --base main --scope src/ --check '["python3", "-m", "unittest"]' \
  --runtime local --allow-local
```

On macOS this selects `~/.config/workmux/agents.macos.yaml`; on Linux supply an explicit `--config <local-config>` too. The config must disable sandboxing, and the observed UI workdir must equal the actual local worktree. A macOS config also requires `--allow-local` when explicitly selected with another runtime.

Record the user's approval and actual execution environment as a consequential ACTIVITY decision. Preserve canonical paths and the original UI context on reopen (see [runtime.md](runtime.md#ui-adapters)).

Automatic finish does not support local/Lima writer-exit proof. Retain resources and obtain independent exact process evidence for review; closing a pane is not proof. Use [recovery.md](recovery.md) for this handoff. Do not substitute a fabricated container identity or claim automatic cleanup/completion passed.
