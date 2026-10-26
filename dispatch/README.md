# Dispatch

A tuios-first coding workflow. Aven stores durable tasks and outcomes. Native
tuios worktrees, agents, queue, review, checkpoints, and ship operations do the
live work. The Python helper only renders a read-only dashboard. It is not a
scheduler.

## Install

Copy this directory, with its assets, scripts, and references, to
`~/.pi/agent/skills/dispatch/`. Keep `SKILL.md` at that path. Replace an existing
installation only when replacement is authorized. Python 3 uses no extra
packages. Install and configure tuios, Aven, Git, and the selected agent harness
before use. Do not start login, trust, or approval flows during a run.

## Use

Load [SKILL.md](SKILL.md). Supply the coding objective, repository, allowed
paths/actions, acceptance checks, target branch, and merge policy. The skill
records missing authority as a blocker; it does not ask a person to decide.
Follow [preflight](references/planning.md#preflight), then choose
[distinct tasks or fan attempts](references/workers.md). For Pi, first run the
[native integration probe](references/pi.md#host-integration-probe). The target's
same-session mail fix is implemented; live verification is still pending. See
[capability gaps](references/acceptance.md#known-defects-and-gaps).

Keep evidence outside disposable worktrees. Use native ship commit and explicit
local ship merge after review and checks. Remote push/PR approval is not a
supported unattended path. Preserve unrelated resources and unresolved work.
Delivery and cleanup are separate outcomes.

## Validate

From the repository root:

```sh
git diff --check
python3 -m unittest discover -s dispatch/tests -v
python3 -m compileall -q dispatch/scripts
```

Tests check local links, static safety rules, and dashboard behavior. They do
not prove live agent behavior. See the [acceptance matrix and isolated
exercises](references/acceptance.md) for commands, evidence, and open gaps.
Live end-to-end acceptance is not yet passed. The observed host daemon rejects
TML opening and schema discovery. Do not restart a shared daemon to repair it.
