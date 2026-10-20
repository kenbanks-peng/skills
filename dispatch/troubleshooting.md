# Exceptional CLI diagnostics

## Routing

Load after diagnostics establish that Aven selects the wrong database or workspace. Inspect the actual error/context: an inaccessible or read-only correct database needs access repair, not a different task database.

From the target repository root, check the existing database and task context:

```sh
aven doctor --json
aven context APP-1234 --json
```

Repair Aven configuration or access and confirm the intended task context before retrying. Already-saved conflicting identity requires [recovery](recovery.md); do not edit a record to force continuation. Preserve report text locally on a failed Aven write and restore it to the correct durable record before the corresponding merge or completion gate.

## Capabilities

Load after an unsupported command, flag, response schema, or diagnosed tool change. Normal runs do not require discovery, a capability cache, or help rehearsal.

```sh
python3 <skill-directory>/scripts/dispatch_cli.py discover \
  --cache <evidence-directory>/cli.json --refresh
workmux <affected-subcommand> --help
```

Use targeted help to resolve the mismatch before another mutation. Keep errors, JSON stdout (including failures), and evidence paths. The guarded integration requires Workmux merge support for `--into <base> --keep`, hooks enabled, and no second rebase; installed `0.1.276+herdr.1` supplied these semantics during validation. If behavior differs, preserve resources rather than bypassing the guards.

Python helper `--help` owns the current argument syntax. Legacy preflight, stop, archive, cleanup, and verification helpers are diagnostics, not a caller-wired substitute for launch/integrate/finish. JSON inputs are literal data; write them with file tools rather than interpolating task content into shell source.
