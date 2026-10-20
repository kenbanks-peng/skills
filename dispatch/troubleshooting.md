# Exceptional CLI diagnostics

## Routing

Load after diagnostics establish that Aven defaults select the wrong database or workspace. Default runs use configured routing and project inference. Inspect the actual error/context before overriding: an inaccessible or read-only correct DB needs access repair, not a different task database.

For a new launch, add only the diagnosed overrides:

```sh
python3 <skill-directory>/scripts/dispatch.py launch APP-1234 \
  --base main --check '["python3", "-m", "unittest"]' \
  --db <correct-db> --workspace <correct-workspace>
```

Dispatcher overrides are saved and reused by task reference. Worker prompt context reads use Aven defaults in the current directory; configure those defaults to select the correct task database and workspace. Dispatcher overrides are not passed to the prompt renderer or worker. `dispatch_cli.py report` also accepts `--db`/`--workspace` when needed. Already-saved conflicting identity or routing requires [recovery](recovery.md); do not edit a record to force continuation. Preserve report text locally on a failed Aven write and restore it to the correct durable record before the corresponding merge or completion gate.

## Capabilities

Load after an unsupported command, flag, response schema, or diagnosed tool change. Normal runs do not require discovery, a capability cache, or help rehearsal.

```sh
python3 <skill-directory>/scripts/dispatch_cli.py discover \
  --cache <evidence-directory>/cli.json --refresh
workmux <affected-subcommand> --help
```

Use targeted help to resolve the mismatch before another mutation. Keep errors, JSON stdout (including failures), and evidence paths. The guarded integration requires Workmux merge support for `--into <base> --keep`, hooks enabled, and no second rebase; installed `0.1.276+herdr.1` supplied these semantics during validation. If behavior differs, preserve resources rather than bypassing the guards.

Python helper `--help` owns the current argument syntax. Legacy preflight, stop, archive, cleanup, and verification helpers are diagnostics, not a caller-wired substitute for launch/integrate/finish. JSON inputs are literal data; write them with file tools rather than interpolating task content into shell source.
