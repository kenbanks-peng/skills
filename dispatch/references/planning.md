# Planning and capability discovery

## Preflight

1. Resolve the authorized repository and target. Read its instructions. Inspect existing changes before any write:

   ```sh
   git rev-parse --show-toplevel
   git status --porcelain=v1 --untracked-files=all
   git branch --show-current
   git rev-parse HEAD
   git worktree list --porcelain
   git var GIT_AUTHOR_IDENT
   git var GIT_COMMITTER_IDENT
   ```

   The last worktree command is a read-only identity check, not a second worktree manager. Record the root, original changes, branch, and base SHA. If identity is absent, a path is outside scope, or a target is ambiguous, block the affected step. Do not set a substitute identity. Preserve a dirty user checkout; independent work may use a new native worktree from the agreed base, but merge must wait for a clean target.
2. Check tools and installed contracts:

   ```sh
   command -v tuios
   command -v aven
   command -v git
   tuios --help
   tuios --skill recipes
   tuios --skill fleet
   tuios --skill grants
   tuios pane-grants --json
   tuios list-verbs --json
   tuios worktree ls --json
   tuios list-agents --all-sessions --json
   ```

   A call outside a pane may have no pane grants. Record that context; never create it by leaving a restricted pane. A cross-session inventory refusal is a capability blocker. Do not treat an empty or refused inventory as proof that no resources exist.
3. Read the selected feature topics: `tuios --skill mail`, `events`, `checkpoints`, `ship`, `state`, and `tml`. Read command `--help` for selected flags. Use `tuios list-verbs VERB` for exact parameters and error/result shapes. `tuios call VERB 'JSON'` is supported for non-streaming verbs only. Do not invent wrapper syntax from a verb name.
4. Check the runtime at its real execution location. Validate harness availability, authentication, trusted-folder setup, noninteractive checks, disk, and memory within existing authority. Do not run a login, trust, permission, or approval flow. Follow [pi](pi.md) before selecting pi. A missing state integration blocks that worker type; terminal silence is not a substitute.
5. Read [dashboard](dashboard.md), validate TML support, and create or reuse one owned status surface. If a required feature is missing, record the exact command/error and the affected acceptance criterion. Continue independent supported work, not an invented equivalent.

Use documentation snapshots supplied by the caller as command evidence. Revalidate against installed help if the runtime differs. Documentation is not authorization to run its human-input recipes.

## Durable records

Run Aven in the target repository. Read the tasks skill when available. Otherwise inspect `aven --help` and command help. Search before adding tasks:

```sh
aven list --ready
aven context TASK
aven show TASK --full
aven add 'Objective' --epic
aven add 'Implement isolated change' --status todo
aven epic add CHILD EPIC
aven dep add BLOCKED_TASK BLOCKER_TASK
aven note TASK --file /absolute/evidence/decision.md
```

Names in capital letters are values from the run, not literal refs. Obtain refs from Aven output; never guess them. Read full existing context and repository records before making a new task. Epic membership does not create a dependency. Record requirements, allowed paths, forbidden actions, checks, and rationale in the task description using installed Aven edit help. Create separate review/verification tasks when they have independent acceptance or dependencies.

Minimum durable data, stored in task descriptions and concise outcome notes:

```text
Run: run ID; objective/epic ref; repository root; authorized paths/actions
Policy: target branch; base SHA; merge policy; concurrency bound; check commands
Task: ref; scope; acceptance; dependencies; assigned role; current blocker/outcome
Attempt: ID; task ref; role; selected/disposition; initial assignment ID
Resource: daemon/server; host; session name/ID; pane ID/name; group; branch; path
Runtime: local/remote/container; runtime ID if used; identity/integration evidence
Delivery: prompt status; queue ID or message/thread ID if used; acknowledged result
Evidence: revision/diff; review decision; checks with exit status and durable log path
Integration: worker commit SHA; target before/after SHA; policy; status evidence
Cleanup: owned resources removed; retained paths/branches/stashes and reasons
```

Use only fields that apply. Link shared run policy once. Do not copy tuios queues, event history, or agent state into a control database. A local evidence directory may hold logs and reports, but Aven must link the durable decisions. Use a stable directory outside disposable worker trees.

Before a side effect, note its intended attempt/resource identity. After it, note the observed identity and evidence. This small handoff record supports reconciliation; it is not a scheduler. If a note write fails, retain the note locally and report the failure. Do not claim a durable handoff until it is saved.

If authorized to manage task status:

```sh
aven edit TASK --status active
aven edit TASK --status done
```

Check dependencies before activation. Mark done only after acceptance passes and delivery evidence is recorded. The Aven agent field denotes a type, not a pane; clear it when leaving active status using installed edit help. Respect an assignment that reserves status changes for another owner.

## Select work and concurrency

1. Separate independent scopes. Start only dependency-ready tasks. Do not assign one distinct task to two writers. Competing attempts are explicit fan attempts in different checkouts.
2. Set a positive concurrency bound from the objective and measured capacity. Count implementation, review, verification, test commands, and containers. Start with one if capacity is unknown. Record the decision; do not install a scheduling service.
3. Use disjoint branches and native worktree sessions per task/attempt. Shared caches and external services can still conflict; serialize their checks or use authorized isolated instances.
4. Require one integration owner and one merge at a time. Rebase or integration corrections must be explicit authorized follow-up work, followed by new review/check evidence.
5. If a dependency blocks, record the precise missing fact or authority and continue other ready tasks. Do not ask a person for it.
