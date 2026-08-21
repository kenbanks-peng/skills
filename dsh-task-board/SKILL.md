---
name: dsh-task-board
description: Operate the DSH task-board plugin (任务看板 / 看板 / 定时任务, Task Board). Use when the user asks to complete, run, create, move, archive, delete, inspect, or schedule tasks on the task board. All writes go through the Host API — never edit the ledger file directly.
---

# DSH Task Board

The board is a kanban of tasks, each carrying a prompt. The Host executes a task by launching a real dsh session with that prompt (pinned workspace/agent preset), then settles the task when the session's turn ends. The ledger is Host-authoritative: the running Host owns the file, holds a lock, and rewrites it atomically on every commit. The API is the only sanctioned write path — an external file edit gets clobbered or corrupts revision tracking.

## Ground rules

- **Host-authoritative**: never write `$DSH_HOME/task-board/ledger-v2.json` (or the `.lock` / `scheduler-v2.json` sidecar) yourself. Read it only to double-check the API.
- **`run` costs API quota** and executes on the Host, surviving browser close.
- **Runner-owned statuses**: manual `move` only targets `backlog`/`todo`, and never from `running`. Only the runner settles `running` → `done`/`failed` (or `cancelled` → `todo`).
- **Idempotent requests**: each `requestId` is cached with its action's fingerprint; reusing an id with a different action is rejected. Generate a fresh UUID per request.

## Process

### 1. Confirm the base URL

The API lives on the DSH Web GUI origin — this session: `http://127.0.0.1:43120`. Every request must carry a browser same-origin marker; a bare curl gets `403 forbidden`:

```sh
BASE=http://127.0.0.1:43120
curl -s -H "Origin: $BASE" -H "Sec-Fetch-Site: same-origin" $BASE/api/task-board/state
```

**Done when:** `/state` returns JSON (`schemaVersion`, `revision`, `tasks`, `scheduler`, `power`).

### 2. Read the board

`GET /api/task-board/state` returns the full snapshot. Open work = `status` not in (`done`, `failed`) and no `archivedAt`. Track `revision` — it increments on every commit.

### 3. Mutate the board

`POST /api/task-board/action` with envelope `{"requestId": "<uuid>", "action": {...}}` and `Content-Type: application/json`; the response is the new snapshot. Actions: see the reference table. After any mutation, confirm the task's `status`/`updatedAt` changed in the response.

### 4. Execute a task

To complete a task, run it — never fake it:

```sh
curl -s -X POST -H "Origin: $BASE" -H "Sec-Fetch-Site: same-origin" \
  -H "Content-Type: application/json" \
  -d "{\"requestId\":\"$(uuidgen)\",\"action\":{\"kind\":\"run\",\"taskId\":\"<task-id>\"}}" \
  $BASE/api/task-board/action
```

`rerun` does the same for a settled task (moves it back to `todo` first). **Done when:** the response shows the task `running` with a new execution (`startedAt` set, `endedAt` absent).

### 5. Wait for settlement

The Host polls sessions every ~5 s and settles on turn end: `succeeded` → `done`, `failed` → `failed` (with `error`), session gone → `cancelled` → `todo`. LLM turns take minutes. Poll `/state` every 20–30 s until every open execution has an `endedAt`. For evidence, inspect the session log: `$DSH_HOME/sessions/<workspace-dir>/<sessionId>/session.jsonl.zstd` (`zstd -dc`).

**Done when:** every task the user asked to complete is `done` — or `failed` with a concrete reason (workspace/preset missing, prompt rejection) to report back.

## Reference

**Statuses** (kanban columns): `backlog`, `todo`, `running`, `done`, `failed`.

**Execution record**: `{id, sessionId?, startedAt, endedAt?, result?: succeeded|failed|cancelled, error?}` — appended per run, most recent last.

**Task fields**: `id`, `title`, `description`, `prompt`, `status`, `createdAt`, `updatedAt`, `executions[]`, `schedule?`, `workspaceId?`, `mode?` (agent preset), `permission?` (`read-only` | `workspace-write` | `danger-full-access`), `archivedAt?`.

**Actions** (`kind`, payload, notes):

| kind | payload | notes |
|---|---|---|
| `create` | `id`, `input{title, description, prompt, workspaceId?, mode?, permission?, schedule?}` | new task starts in `todo` |
| `update` | `taskId`, `patch` (same fields minus schedule) | archived tasks are read-only |
| `move` | `taskId`, `status` | only to `backlog`/`todo`, never from `running` |
| `run` / `rerun` | `taskId` | opens an execution, Host launches the session |
| `archive` / `restore` | `taskId` | only from `done`/`failed`; archived tasks can't run |
| `delete` | `taskId` | refused while running |
| `set-schedule` | `taskId`, `patch{enabled?, cron?}` | 5-field cron `分 时 日 月 周`, host-local timezone; invalid cron rejected |
| `import` | `sourceId`, `tasks[]` | one-shot migration, deduped by `sourceId` |

**Ledger files** (read-only for the agent): `$DSH_HOME/task-board/ledger-v2.json`, `ledger-v2.lock` (Host pid/token), `scheduler-v2.json` (lastTickAt sidecar). `$DSH_HOME` resolves through a symlink; use `realpath` if needed.

**Failure modes**: `403 forbidden` → missing browser-marker headers; `400 invalid-action` → malformed envelope; `413 body-too-large` (>64 KB, >2 MB for import); `task board is disabled` → board off; pinned `workspaceId`/`mode` missing → launch fails, task settles `failed`.

**Authoritative schema** (for deep questions): plugin source at `$DSH_HOME/profiles/desktop/node_modules/@linxin666/dsh-client-ui-task-board/src/` — `protocol.ts` (actions), `core/tasks.ts` (statuses/records), `host-ledger.ts` (apply/commit rules), `host-routes.ts` (auth guard), `host-service.ts` (poll/settle loop). The web bundle is also served at `/plugins/@linxin666/dsh-client-ui-task-board/client.js` on the GUI origin.
