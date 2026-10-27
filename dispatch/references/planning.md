# Planning

## Prepare

Read repository instructions and the coding objective. Use the current branch
and HEAD as the target and base unless the task specifies another.
Read `tuios --skill recipes` and the help for the operations you select.
Initialize workspace.py with a fresh run directory outside task checkouts.
On resume, use status with the saved run directory.

## Execution

Launch workers with `linux container --` through the execution tool.
Follow [workers](workers.md) for the tuios pane and worktree commands.
The launcher selects Linux and uses its configured runtime, image, and profile.
Use its actual error output to diagnose a failed launch.

## Task records

Search Aven before creating tasks. Record objective, scope, dependencies,
acceptance checks, target branch, base, merge policy, and concurrency.
Link each attempt to its session, pane, worktree, branch, and saved evidence.
Keep records short and update them after meaningful outcomes.

## Defaults

Use squash integration for independent task branches and one integration owner.
Choose concurrency from task independence and available capacity.
Give each writing task its own checkout. Use separate reviewers for substantial
changes and dispatcher review for small changes.
Resolve ordinary task decisions from repository context. Record unresolved
scope or authority and continue independent work.
