# Dispatch validation (DSP-C766)

## Scope and baseline

The task has two phases: consolidate the public CLI, then optimize the resulting inputs and outputs. [SKILL.md](SKILL.md) gives the normal workflow. [recovery.md](recovery.md) gives recovery actions. [io-inventory.md](io-inventory.md) records all reviewed inputs/outputs, changes, evidence retrieval, and exceptions.

Before changes, the supplied suite ran 190 tests with 57 failures and 4 skips. Many failures were consumers already expecting startup through the consolidated CLI.

After consolidation, a controlled launch supplied the checked-in baseline fixture. Full output measured 6,962 bytes with one event, 41,036 with ten, and 381,776 with one hundred. The compact output is 550 bytes for all three. The baseline is the consolidated interface, not removed wrappers. The inventory gives the measurement method and additional budgets.

## Reproducible checks

From this directory:

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
ruff check --no-cache scripts tests
git diff --check
```

The suite uses temporary Git repositories, controlled Aven/Workmux/container commands, and controlled UI sockets. It does not require live workers or change live task status. Platform-specific checks can skip.

Coverage includes:

- Public routing, phase help, invalid inputs, separate inspect/resume, and internal imports.
- Repository locks, saved identities, revision checks, active/done readback, and closure authorization.
- Full worker requirements, duplicate-note removal, one assignment-context fetch, and literal check argv.
- Bounded default output, large reports/logs, multi-event history, complete verbose evidence, and evidence-write failure.
- Integration/reconciliation and independent pinned verification.
- Confirmed exit, strict prompt archive, safe cleanup, pending resources, and separate housekeeping.
- Full lifecycle consumers and evidence retrieval after worker cleanup.

A successful one-worker path now keeps ten files under its worker evidence directory: worker record, assignment, complete task-context snapshot, config snapshot, generated-prompt hash copy, three integration/check records, prompt archive, and completion report. Separate shared run records, content-addressed Aven sources, complete check streams, and immutable phase/error evidence are also retained. File count is not an optimization target; no safety evidence is deleted to reduce it.

## Latest result

The final full run completed **212 tests: 208 passed, 4 skipped**. Ruff and `git diff --check` passed. Validation logs are retained under `<common-git-dir>/dispatch-validation/DSP-C766/`.

The four skips are platform/host-specific tests. No live worker, destructive container cleanup, or live UI closure was run for this task.

## Limits

Controlled tests do not prove live host UI or container removal. This task does not introduce a new lifecycle policy, local-process stop adapter, automatic stale-lock removal, or evidence garbage collection. It does not exclude Git writers that ignore the shared lock.

Historical design/counts in [design.md](design.md#before-counts) describe an earlier interface study, not the DSP-C766 measurement baseline.
