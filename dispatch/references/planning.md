# Planning

## Preflight

Read repository instructions. Run workspace.py init before creating resources;
its run.json records the branch, HEAD, content identity, and existing windows.
On resume, use status with that same run directory. Keep unrelated changes intact. Resolve the objective from repository context;
do not demand a questionnaire or an exhaustive authorization manifest.

```sh
tuios --skill recipes
tuios pane-grants --json
tuios ls --all-hosts --json
tuios hosts --json
tuios integration status pi --json
```

Read feature help when selecting a workflow. Check actual daemon responses.
An old daemon can advertise fewer verbs than the installed CLI. A help page
alone does not prove support. Inventory existing windows and record ownership.
Check visibility effects before each launch, including implicit starter, merge,
fan verify, and pulled-worktree windows. Only dispatch, Aven, and active Linux
workers may be visible. Require windowless or verified hidden auxiliary work;
--no-focus and --detach do not establish invisibility. If unavailable, record
a blocker rather than open a visible fallback. Do not restart a shared daemon.
A separate named test server is suitable for release tests, but passing there
does not prove the user's running daemon works.

Select the requested host/runtime before launch. For Linux, verify the configured
host link, repository, harness, and native state integration there. See
[execution](pi.md). Do not install new remote infrastructure as an implicit
fallback. Missing setup blocks the affected path, not independent tasks.

## Durable records

Read the tasks skill for Aven. Search before creating tasks. Store only:

- Objective, task refs, scope, dependencies, acceptance checks.
- Target branch, base, merge policy, concurrency.
- Attempt → host/session/pane/worktree/branch.
- Pending follow-up IDs, final checks, review, source/target commits.
- Blockers and retained resources.

Use a short note for a meaningful decision or outcome, not a note before every
read or tool call. tuios owns live state, queues, mail, and checkpoints.
Keep check logs outside disposable worktrees and link them from outcomes.

## Defaults

Use the current target branch and its HEAD unless context specifies another
base. Use squash integration for distinct independent branches unless the
repository specifies another policy. Keep one integration owner.
Choose concurrency from task independence and available capacity; a small
coding objective normally needs two workers, not a fleet of reviewers.
Create separate review tasks only when review is independently tracked work.

Missing information is a blocker only when it changes scope, correctness, or
authority. Do not invent permission problems for ordinary task operations.
