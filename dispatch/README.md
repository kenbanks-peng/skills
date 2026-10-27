# Dispatch

Coordinate Linux coding agents in tuios panes. Dispatch uses native worktrees,
review, and delivery, with Aven for durable tasks and a dashboard in dispatch.
Scripts record ownership, run checks, save evidence, and clean up run panes.

## Install

Copy this directory to `~/.agents/skills/dispatch/` or your agent's skill
directory. Keep assets, references, and scripts beside SKILL.md.
Requires tuios, Aven, Git, Python 3.10+, and the configured `linux` launcher
with a development image and agent profile.

## Use

Load [SKILL.md](SKILL.md) and supply a coding objective and repository.
Dispatch launches workers with `linux container -- pi` in separate task
checkouts, reviews and checks their changes, delivers, and closes run panes.
See [worker launch](references/workers.md) and
[script procedures](references/automation.md).

## Validate

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

Static tests are not live acceptance. See [release checks](references/acceptance.md).
