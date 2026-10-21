# Dispatch interface design

Task: SKL-641J. Baseline: `41298fe3db351c6c2a7aa4b0688740b426e141c1`. The task-start revision, `876664bc395a3320e334029e2353815cb5bb348c`, has the same tracked code and instructions. This brief records the original refactor target and baseline, not a run procedure. Launch, inspection, integration, and finish are implemented. [SKILL.md](SKILL.md) owns current usage; [validation.md](validation.md) records the final interface counts and validation limits.

## Ownership and target interface

Dispatch owns review, integration authorization, Git integration, independent base verification, Aven status/assignment, closure, and recovery decisions. Workers own implementation, commits, checks, and RESULT/BLOCKED reports. Workmux owns execution and sessions; its `done` state never closes an Aven task. Aven owns durable task context and handoffs.

Use one deep lifecycle module with four verbs:

- `launch <record>`: validate the reviewed assignment, capture the explicit base, generate the prompt, and start/observe one worker. Save partial observations on failure. An existing or uncertain launch requires reconciliation, not another add.
- `integrate <record> --reviewed <sha>`: dispatch supplies its review decision. Validate exact identity and clean Git state; rebase onto the explicit local base, run checks, integrate serially, then independently verify the pinned base. A changed worker SHA requires a new review; never merge a moving branch unseen.
- `finish <record>`: confirm writer exit, archive known prompts, attempt strict cleanup, and save a completion report before closing the task. Dispatcher acceptance and integration precede finish. Finish needs confirmed exit and durable reporting; it does not repeat acceptance or require an unchanged base. Retained resources are explicit pending cleanup, not false completion.
- `inspect <record>` (read-only), or `inspect <record> --resume`: reconcile actual Git, process, report, and resource state; continue only the justified next action. Use the observed-state/action table in recovery.md. Never repeat an uncertain mutation or replace a worker merely because its window is missing.

Keep review and conflict decisions with dispatch. Do not add an autonomous scheduler, daemon, database, generic engine, or compatibility wrappers. Serialize launch, integration, and cleanup per repository; parallel implementation requires disjoint write scopes. Evidence is a snapshot, not a lock.

### Minimum saved worker record

Store one versioned record outside all worker worktrees. Save updates atomically. It must retain:

- Task ref, canonical repository/common Git directory, explicit local base and launch SHA; worker branch/handle; required argv checks.
- Selected config, actual agent/runtime; observed host and worker-visible roots; exact container ID/mount identity; exact pane/tab IDs and multiplexer context.
- Prompt location/hash and generated prompt paths/hashes; review SHA/decision; integrated worker SHA, verified base SHA, and check results/evidence paths.
- Last attempted action and outcome, partial resources, exit proof, archive and cleanup results, durable note references, and next action.

Derive repeated identity and evidence arguments from this record. Keep failure evidence. Do not treat a saved phase, success report, or missing resource as proof of current state.

## Before counts

Counting rule: one task, one successful sandboxed worker, one wait per phase, one generated prompt, no retries, one final run verification, no special manifest. Count dispatcher commands, not worker implementation/check commands or read/write tool calls. Counts below describe the current documented recipe, not a universal lower bound. Dry run and execution are separate calls.

| Helper calls (normal path)                           |  Calls | Named value slots |
| ---------------------------------------------------- | -----: | ----------------: |
| discover; initial prompt; launch                     |      3 |        1 + 10 + 8 |
| render DISPATCH; select RESULT                       |      2 |            13 + 2 |
| preflight; merge prompt; select MERGE                |      3 |         4 + 9 + 3 |
| verify task base; verify final run base              |      2 |             4 + 4 |
| stop dry/execute; archive dry/execute                |      4 |             2 + 6 |
| cleanup dry/execute; render VERIFIED; render SUMMARY |      4 |       16 + 11 + 7 |
| **Total**                                            | **18** |           **100** |

A value slot is a required named value supplied to a helper, including output paths, kind selectors, and container receipt/stop inputs. Expand JSON parameters instead of counting the `--params` wrapper; count checks lists as one value. Exclude boolean switches, optional overrides, and shell redirections. Repeated calls count repeated inputs. These are mechanical input occurrences, not 100 independent decisions.

Add 17 surrounding commands: ready query/context (2), rename/open UI (2), capture base (1), Aven active/note DISPATCH (2), monitor wait (1), send merge/wait (2), append VERIFIED/mark done (2), ready query (1), empty-parent removal/close UI (2), append SUMMARY (1), and final base recheck (1). Total recipe: **35 dispatcher commands**. Extra polling, Git inspection, prompt review, and conflict repair increase this count.

Mandatory saved file instances for that recipe: **23**, plus **5 Aven events** (DISPATCH, worker RESULT, worker MERGE, VERIFIED, SUMMARY). Files are: capability cache (1); initial parameters/prompt/receipt (3); DISPATCH parameters/note (2); preflight JSON (1); merge parameters/prompt (2); checks input (1); task/final verification JSON (2); stop/archive/cleanup dry/execute JSON (6); VERIFIED and SUMMARY parameters/notes (4); archived generated prompt (1). Source prompt copies, UI ID text, and optional retained full report snapshots are excluded. Each extra generated prompt adds one archive.

Target: three lifecycle mutations (launch, integrate, finish), with inspect only when needed. The implemented launch accepts assignment fields directly and derives the record under the common Git directory. Later verbs can locate it by full task reference. Integration also needs one reviewed SHA. The record replaces repeated fields; artifacts are managed evidence, not manual plumbing. Measure final after-counts in [validation.md](validation.md) (SKL-H99C).

## Runtime and local checks

Production assumes Python 3.10+, modern Git with `init -b` and `rev-parse --path-format=absolute`, POSIX process groups, Aven, and Workmux. Default worker config is `~/.config/workmux/agents.linux.yaml`. `--platform linux|darwin` defaults to Linux workers. Launch creates missing platform configs and preserves existing files. Supported container commands are Apple `container`, Docker, and Podman; no Lima or Windows adapter is planned. Use Herdr when `HERDR_ENV=1`, otherwise an active tmux session. Record the original context and exact IDs; never select a resource for deletion by label. A closed UI is not proof of writer exit. Checks are trusted local executables; process groups do not contain descendants that deliberately escape them.

Run from this repository:

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The suite needs only Python 3.10+, Git, and POSIX. It uses temporary repositories, controlled CLI responses, and no live Aven server, worker, multiplexer, or container. The stable safety seams are command exit/JSON results and actual retained Git/files: preflight identity/state, pinned verification, guarded cleanup, report selection, launch revision checks, and confirmed stop. These tests must move to the lifecycle interface as it replaces those commands; helper names and note schemas are not compatibility requirements. They do not prove live Workmux integration, UI behavior, conflict semantics, or serialization. Those need the later lifecycle tests.

The normal finish interface joins exact writer exit, archive, removal, and durable completion reporting under the repository lock. Dispatcher acceptance is final for this operation; finish does not read acceptance evidence or require the base to stay unchanged. A single command executes finish without separate authorization. Tests exercise repeated finish, partial archive/removal, retained content, and separate delivery/cleanup/housekeeping outcomes. Unknown exit blocks completion. Local/Lima process evidence still requires review; it is not inferred from UI state. Herdr UI closure remains explicit best-effort housekeeping. Standalone Git/runtime helpers remain for diagnostics, not as substitutes for finish. Closure evidence validation lives in the lifecycle implementation, independently of note presentation. Agents write notes directly under the tasks selective-note policy; UI and project-specific checks are opt-in. No command can exclude Git writers that do not honor the common repository lock.
