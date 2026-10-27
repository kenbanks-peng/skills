# Dispatch

A concise multi-agent coding workflow built on tuios. It uses native worktrees,
fleet monitoring, agent queues and mail, review, checkpoints, and ship delivery.
Aven stores durable tasks. Scripts run checks, record evidence, deliver reviewed
changes, and close owned windows. Status stays in the existing dispatch pane.
Only dispatch, Aven, and Linux workers may have visible windows. Cleanup leaves
only dispatch.

## Install

Copy this directory to `~/.agents/skills/dispatch/` or your agent's skill
directory. Keep assets, references, and scripts beside SKILL.md.
Requires tuios, Aven, Git, Python 3.10+, and a configured agent harness on Linux
or macOS. No Python packages are needed.
Linux execution requires a configured reachable tuios host and harness there.

## Use

Load [SKILL.md](SKILL.md) and supply a coding objective and repository.
Specify Linux/container execution when required. Dispatch uses repository
defaults, runs independent work in parallel, reviews and checks changes,
delivers locally, and cleans up its temporary panes. It asks no human questions
and starts no approval workflow. Follow [script procedures](references/automation.md)
for startup, check plans, status, delivery, and cleanup.

## Validate

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

Static tests are not live acceptance. See [release checks](references/acceptance.md)
for native execution evidence and environment limits.
