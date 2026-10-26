# Read-only live dashboard

## Role and ownership

`assets/dashboard.tml` is a native TML document. It is also the render template.
With no snapshot it shows an empty board, not invented worker results.
`scripts/dashboard.py` uses only Python's standard library. It validates a
snapshot, renders this document, or writes a guarded JSON Patch. It does not
call tuios, launch workers, assign work, poll, select tasks, or store task state.
It is not a scheduler or another database.

Aven owns durable task requirements and outcomes. tuios owns live agent, queue,
review, and surface state. The dispatcher supplies a bounded display snapshot
from these sources. It updates the board when it handles native events or task
changes. This helper does not watch files or create a background service.

Open one surface from the dispatcher pane. Keep its server/socket, owner pane
ID, session, surface ID, and last applied snapshot revision in the run evidence.
Only that owner pane can patch, replace, or close the surface. It needs the
native `write` grant. Do not copy pane tokens. The worker does not own this
surface. Workers can use separate sessions; label each session and full pane ID
in the snapshot.

## Snapshot contract

Copy `assets/dashboard-example.json` to the run evidence directory as a shape
example. It is not live evidence. Supply all fields; do not omit unknown facts.
Use `unknown`, `not run`, or `none` as appropriate. Do not use an empty string
for a required field. The helper rejects extra keys, missing keys, duplicate
JSON keys, invalid types, control characters, and duplicate task/attempt pairs.
It accepts an empty task list. External dependencies need not have a board row.

Top-level fields:

| Field | Type and source |
| --- | --- |
| `run` | Non-empty text; stable run identity. |
| `revision` | Non-negative integer; increase for each applied update. |
| `observed_at` | Non-empty text; dispatcher observation time, preferably UTC. |
| `tasks` | List of attempt rows. Include pending tasks with attempt `not assigned`, and retained attempts when useful. |

Each row has these non-empty text fields:

- `task`, `task_state`: Aven ref and durable task state. Never derive acceptance
  from an idle agent.
- `attempt`: stable attempt identity. Competing attempts use distinct rows.
- `agent`, `session`, `pane`: native labels and full pane identity.
- `branch`, `worktree`, `environment`: native resource identity and host name.
- `queue`: queued assignment IDs, delivery states, and evidence reference. Use
  native `queue ls`, not an internal helper queue.
- `review`: verdict and review evidence reference.
- `checks`: command/result summary and evidence reference. Say `not run` when
  there is no result. Keep full logs outside the board.
- `delivery`: reviewed and delivered commit IDs or explicit pending state.
- `blockers`: blocker, owner, and next safe action, or `none`.
- `cleanup`: retained/removed resources, reason, owner, and next action.

Each row also has `dependencies`, a list of non-empty ref/status strings, and
`native`, an object with exactly these fields:

| Field | Type |
| --- | --- |
| `state` | One of `none`, `working`, `needs_input`, `idle`, `done`, `errored`, `unknown`. |
| `source`, `identity` | Non-empty text copied from native state evidence; `unknown` if absent. |
| `evidence_age_ms`, `completion_seq`, `subagents` | Non-negative integer, or JSON null if not observed. |

The dispatcher maps the installed `get-agent-state --json` response into
`native`. Do not pass the response envelope as the whole snapshot. Save its raw
evidence outside the view. If observation fails or a pane disappears, use
`unknown` and a blocker; do not preserve a stale `done` as a new observation.
Evidence age is the value at `observed_at`, not a running clock. Include
`blocked_by` and diagnostic context in `blockers` when relevant. A snapshot is
a display projection, not authority to retry, approve, or deliver work.

## Exact CLI usage

Set `skill` to the absolute path of `dispatch/` and `run_dir` to the owned run
evidence directory. All commands below run from the same dispatcher owner pane,
with the same server routing. Set `dashboard_session` to the orchestrator/status
session. Do not target a worker session or the focused pane by accident.

```sh
python3 "$skill/scripts/dashboard.py" render "$run_dir/snapshot-1.json" \
  > "$run_dir/dashboard.tml"
tuios tml validate "$run_dir/dashboard.tml"
tuios tml show "$run_dir/dashboard.tml" --pane \
  -s "$dashboard_session" --name "dispatch status"
```

Save the returned surface ID as `surface`. Do not use `--wait`, an input form,
a popup approval, `--focus`, client attach, or a workspace switch. Native show
opens the surface without taking focus. It also validates the document. The
person can read the pane without any action required from them.

After the dispatcher supplies `snapshot-2.json` with a larger revision:

```sh
python3 "$skill/scripts/dashboard.py" patch \
  "$run_dir/snapshot-1.json" "$run_dir/snapshot-2.json" \
  > "$run_dir/dashboard.patch.json"
tuios tml patch "$surface" - < "$run_dir/dashboard.patch.json"
tuios tml get "$surface"
```

Only patch after helper exit zero. Do not pipe a failed helper directly into a
mutation. The patch tests the previous revision and run identity, replaces the
board state, and advances the revision. It does not replace the component tree
or open another pane. Tables read the same `state.board.tasks` path after each
update. Native patch redraws only consumers of changed paths. Save the current
snapshot as last applied only after patch success and readback. Serialize view
updates from this owner.

`render` writes TML to stdout. `patch PREVIOUS CURRENT` writes RFC 6902 JSON to
stdout. Invalid input exits 2, prints a diagnostic on stderr, and writes no
result. No external Python packages are required. The renderer limits documents
to the native 256 KiB bound and patches to 64 KiB. Use concise summaries and log
references. If the board exceeds the patch limit, reduce the supplied view;
do not flood the UI with new surfaces. Detailed logs stay in evidence files.

## Read-only design and recovery

The document uses headings, text, scroll layout, and tables with `select="none"`.
It has no actions, key handlers, editable fields, links, buttons, forms, pane
commands, approval controls, or input requests. Untrusted values stay in JSON
state and table cells. They are not inserted into TML expressions or attributes.
JSON is XML-escaped when embedded in the state element.

If a patch `test` fails, nothing is applied. Read `tuios tml get "$surface"`,
check its run and revision, reconcile with the last successful snapshot, and
regenerate a patch from that state. Do not remove the guard or repeat a mutation
blindly. `tml get` returns native surface data; inspect its actual state envelope
rather than assuming it is an input snapshot.

After interruption, first check the saved surface with `tml get` from its owner.
Reuse it if it still belongs to this run. If the owner changed, do not impersonate
it. If the surface is gone, reconcile inventory before opening one replacement.
Record a new surface ID only after successful show. Lost command output alone
is not proof the surface is absent. A forbidden patch is an ownership blocker,
not a reason to bypass grants. On close, use only the confirmed owned ID:

```sh
tuios tml close "$surface" '"dispatch closed"'
```

Do not close worker or unrelated surfaces. A closed dashboard does not mean
worker cleanup is complete. Record retained resources separately.

## Verification and limits

Local checks:

```sh
python3 -m unittest discover -s dispatch/tests -p test_dashboard.py -v
git diff --check
```

The tests cover XML/JSON escaping, schema errors, duplicate JSON keys, required
columns, read-only components, competing attempts, patch guards and updates,
CLI failure, and native size bounds. They are not a native tuios validator.

Host acceptance probe (not run in the build worker):

1. Render the example and run native `tml validate`. Require exit zero and no
   binding errors. Open it once with `tml show --pane` from the owner.
2. Read the returned surface with `tml get`. Check every section, including
   dependencies, native state/evidence, resource labels, queue, review, checks,
   delivery, blockers, and cleanup. Scroll to inspect long boards.
3. Change these fields in the next snapshot and increase its revision. Generate
   and apply the patch above. Confirm the same surface ID and changed values
   with `tml get` and visual inspection. Confirm no client focus change.
4. Apply the old patch again. Require a failed revision test and unchanged
   state. Save command exits and native evidence. Close only the owned surface.

This probe is required before claiming native TML validation, live updates,
visual layout, or focus behavior has passed. No host tuios command was run in
the build worker. Narrow terminal layout and remote-client rendering need host
inspection. The saved docs say clients on another machine show a placeholder,
not the surface; do not claim remote dashboard rendering support.
