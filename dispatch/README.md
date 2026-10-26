# Dispatch

A pi skill for multiagent coding with aven epics and tasks, tuios worktrees and
named workspaces, and pi workers in `linux` dev-containers. The dispatcher checks
and merges work, updates aven, and removes worker resources.

## Install

Place this directory at `~/.pi/agent/skills/dispatch`, or load it with:

```sh
pi --skill /absolute/path/to/dispatch
```

Requires macOS, Apple `container`, configured `linux`, pi in the dev image,
aven with an existing task database, Git, Bash, jq, Python 3, and a matching tuios
CLI/daemon. The container must have working pi credentials and Git identity.

## Use

From the target repository, ask pi:

> Use dispatch for this solution. Group the work in an aven epic, run up to two
> workers, merge into main, and close the worker resources.

Supply acceptance criteria and required checks. See [SKILL.md](SKILL.md) for the
workflow and [runtime.md](runtime.md) for exact container commands. The small
creation helper uses the existing `linux` configuration and saves container
identity before startup. It does not install or configure tools.

To resume, ask dispatch to reconcile the saved records in the common Git directory.
Workers save reports; the host writes aven notes and status. This workflow does
not use tuios mail.

## Test

```sh
python3 -m unittest discover -s tests -v
ruff check scripts tests
ruff format --check scripts tests
```
