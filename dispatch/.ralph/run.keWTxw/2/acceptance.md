# SKL-WY57 acceptance evidence

Required checks: `checks.log` (30 tests pass; changed-code Ruff lint and format pass; CLI help and Git whitespace pass).
The command seam uses real temporary Git repositories and controlled Aven, Workmux, and container responses. No live worker/container was launched.

1. Assignment-only inputs and configured Aven defaults: `test_literal_prompt_default_routing_and_saved_identity`, `test_routing_override_is_saved_and_reused`. Context includes durable notes. Only task/base/scope/checks are required.
2. Captured SHA, literal prompt, serialized creation, automatic identities/config/agent: literal/default test, serialization test, base movement tests. Record writes use atomic replace and fsync in the common Git directory. Config contents and hash are retained.
3. External prompt/evidence and partial failure: partial-launch tests check retained prompt copies, launch stdout/stderr, UI/container observations, and saved record. Intent is saved before Workmux add.
4. Repeated launch/resume: partial, missing/ambiguous, changed-identity, existing-branch, and stale-launch tests require at most one add; inspect leaves the saved record unchanged. No open/delete/replacement path exists.
5. Runtime safety: default sandbox flag/config, missing-config blocker, local/macOS approval, and exact mount mapping tests. Local workdir must be observed; guest paths use exact mounts only.
6. Discovery: no help/version calls in ordinary launch tests. Unsupported wait errors retain observations and direct explicit troubleshooting. Runtime docs remove routine discovery/cache.
7. Required new tests: fast done during startup, partial launch, pre-add and during-add base movement, ambiguous UI/container, literal expressions/newlines, and default/override Aven routing all pass.
8. Old public interfaces removed: launch_worker.py deleted; worker_prompt.py is internal rendering only. SKILL.md/runtime.md use dispatch.py and no caller prompt/receipt JSON.

Scope: launch and inspection only. Dispatch retains review and Aven status ownership. Integration and finish are later tasks.

Extra diagnostic: repository-wide Ruff lint/format still fail in unchanged baseline files (git_preflight.py, merge_prompt.py, recovery_snapshot.py, render_note.py, verify_base.py). Changed code passes. See optional-lint.log; git diff confirms those five files match HEAD. These are not acceptance-required checks and were not changed.
