# tuios-dispatch

A pi skill that dispatches Aven tasks to pi workers in isolated tuios worktrees. The dispatcher reviews, merges, verifies, and completes each task.

It uses native tuios orchestration. No Workmux, Herdr adapter, dispatch daemon, or helper scripts are required.

## Install

Requires Git, Aven, pi, and tuios with pi integration and the fleet/ship features.

```sh
ln -s /absolute/path/to/tuios-dispatch ~/.agents/skills/tuios-dispatch
tuios integration install pi
```

Restart pi after installing its integration. Configure Aven for the target repository and start pi inside tuios. Existing pi integration can be checked with `tuios integration status pi`.

## Use

In pi, from the target repository:

```text
/skill:tuios-dispatch Dispatch the ready tasks in this epic, at most two workers. Integrate into main.
```

To resume:

```text
/skill:tuios-dispatch Resume the run recorded on APP-7KQ9.
```

Aven notes retain assignments and results. Task completion requires dispatcher review and checks on the integrated revision. Pushes and pull requests are outside the default local workflow.
