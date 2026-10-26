# Dispatch

A concise multi-agent coding workflow built on tuios. It uses native worktrees,
fleet monitoring, agent queues and mail, review, checkpoints, and ship delivery.
Aven stores durable tasks. One live TML dashboard shows the run; named native
pane views show Linux workers. Only dispatch, Aven, and Linux workers may have
visible windows. Cleanup leaves only dispatch.

## Install

Copy this directory to `~/.agents/skills/dispatch/` or your agent's skill
directory. Keep assets, references, and scripts beside SKILL.md.
Requires tuios, Aven, Git, Python 3, and a configured agent harness.
Linux execution requires a configured reachable tuios host and harness there.

## Use

Load [SKILL.md](SKILL.md) and supply a coding objective and repository.
Specify Linux/container execution when required. Dispatch uses repository
defaults, runs independent work in parallel, reviews and checks changes,
delivers locally, and cleans up its temporary panes. It asks no human questions
and starts no approval workflow.

## Validate

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

Static tests are not live acceptance. See [release checks](references/acceptance.md)
for native execution evidence and environment limits.
