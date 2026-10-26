# Acceptance and evidence

## Evidence rules

Local tests are not live acceptance. Static checks can reject an unsafe example;
they cannot prove that a daemon or agent obeys it. Do not count words in a guide
as proof of execution. Record each live command, exit code, time, checkout,
HEAD/pending diff, native IDs, and log path. Record skipped observations as
`not checked`, and unavailable capabilities as `blocked`. Never infer a pass
from silence, an idle worker, an empty queue, or this document.

Run the exercises only with existing authority for an isolated scratch repository,
owned native sessions, agent calls, local commits/merges, and cleanup. Do not run
them in a user checkout. Do not execute all blocks as one script. Stop at failed
preconditions; save evidence and continue only independent supported exercises.
There is no scheduler or automatic retry in these procedures.

## Requirement matrix

Each row maps a PLAN section to a procedure and named evidence. All live rows
remain unrun in this worker. Local tests run separately; see the worker report
for actual commands and exits.

| PLAN | Procedure | Required evidence | Current gap |
| --- | --- | --- | --- |
| R01 Product outcome | E1, E5, E7 | task outcomes, reviewed and target SHAs, checks, retained resources | full lifecycle unrun |
| R02 Tuios-first | E0, E1, E2 | installed help, native operation logs | daemon mismatch |
| R03 Tasks and modes | E1, E2 | Aven refs/dependencies, roles, assignment and attempt IDs | two execution modes unrun |
| R04 Worktrees and fleet | E1, E2, E7 | native path/session/pane/branch map, grouped inventory, dispositions | fleet and fan unrun |
| R05 Agent integration | E0, E1 | Pi report identity, state and completion sequence, exact result | Pi live probe unrun; containers unsupported |
| R06 Assignment and mail | E1, E3 | prompt receipt, queue ID/result, same-session read/reply thread | Pi mail example defect |
| R07 Events | E1, E3, E5 | grouped waits/events with IDs and exit status | newer wait flag unsupported |
| R08 Review/checkpoints | E1, E3, E4 | diff, reviewer findings, note/send result, restore safety checkpoint | live review/restore unrun |
| R09 Delivery | E1, E5 | ship commit and explicit merge logs, source/target SHAs, integrated check | local ship unrun; approval-based push/PR unsupported |
| R10 Dashboard | E6 | same surface ID, get before/after, patch guard failure, focus evidence | native validate reported passed; open blocked |
| R11 Recovery/cleanup | E5, E7 | reconciled inventory, no duplicate effects, removed/retained identities | interruption/cleanup unrun |
| R12 No human input | E0–E7 | complete command/agent transcript, no question or approval event | live audit unrun; native held/stalled Inbox risk |

Local evidence: `LinkTests` checks all local Markdown targets and fragments.
`SafetyTests` checks executable shell examples for prohibited command paths and
checks the helper's imports/calls for process or orchestration operations.
`HelperCliTests` runs real helper subprocesses in temporary directories and checks
render/patch results and invalid-input failure. `DashboardTests` covers schema,
escaping, read-only XML, fields, guards, and size limits. These are local contract
checks only. `CoverageTests` checks this matrix for missing requirement/exercise
IDs; it does not verify the procedures were performed.

## E0: Prepare an isolated run

Use a configured host-native Pi harness. Read [planning](planning.md#preflight)
and [Pi](pi.md#host-integration-probe). No integration repair or first-run input
is implied by this exercise. From the existing dispatcher pane:

```sh
command -v tuios
command -v aven
tuios integration status pi --json
tuios doctor agents
tuios pane-grants --json
tuios list-verbs --json
tuios worktree ls --json
tuios list-agents --all-sessions --json
```

Require usable native state integration and current inventory. A refused or
unknown verb is a blocker, not an empty inventory. Do not restart the shared
daemon. Use a compatible authorized test environment for blocked native tests.
Do not launch a harness that needs login, trust, or approval.

With scratch creation authorized, use a new directory. `skill` must name the
absolute installed `dispatch/` directory. Keep evidence outside `repo`:

```sh
skill=/absolute/path/to/dispatch
root=$(mktemp -d "${TMPDIR:-/tmp}/dispatch-acceptance.XXXXXX")
repo="$root/repo"
run_dir="$root/evidence"
mkdir -p "$repo" "$run_dir"
git init -b main "$repo"
cd "$repo"
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
printf 'isolated dispatch acceptance\n' > README.md
git add README.md
git commit -m 'Initialize isolated acceptance fixture'
BASE=$(git rev-parse HEAD)
REPO="$repo"
HARNESS=pi
RUN="accept-$(date +%s)-$$"
```

The seed commit is fixture setup, not worker delivery. Missing existing Git
identity blocks setup; do not invent an identity or change shared configuration.
Search Aven before adding two distinct fixture tasks and one fan task. Use
[durable records](planning.md#durable-records) and installed Aven help. Save the
returned refs as `TASK_A`, `TASK_B`, and `TASK_F`. Add a dependent verification
task after A/B with `aven dep add BLOCKED_TASK BLOCKER_TASK`. Record concurrency
2 only if resources permit; otherwise block the parallel acceptance observation.
Record target `main`, squash policy for independent branches, allowed fixture
files, and check commands below in those tasks. Do not change production tasks.
Save command logs and exits under `run_dir`; link concise outcomes from Aven.

## E1: Distinct tasks through local delivery

Create two workers with [native worktrees](workers.md#distinct-tasks). For A set
`BRANCH="$RUN-a"`, `SESSION="$RUN-a"`; for B use suffix `b`. Run the documented
worktree new and start-agent commands once for each. Save returned IDs and paths,
not predicted names. A's initial prompt is:

```text
TASK_A/attempt-1; role implementer. Work only in this assigned scratch worktree.
Create a.txt with exactly alpha-draft and a newline. Run a foreground 15-second
sleep, then check with Python that its bytes are b'alpha-draft\n'. This is a
planned intermediate fixture; the queued correction will set final alpha.
Do not edit any other path, commit, merge, or launch an agent.
Do not ask a person a question or request approval. Report a blocker instead.
Return task/attempt ID, check command and exit, and changed paths. End the turn
with no background process. Do not write again until an authorized correction.
```

For B substitute the actual task ref, `b.txt`, and `beta`; omit the intermediate
fixture and sleep instructions. Supply each recorded
worktree and evidence path in its prompt. Use the full
[initial prompt contract](coordination.md#initial-prompt). Do not issue a second
assignment to obtain status. Record native `report` state and increased
`completion_seq`, file bytes, diff, and worker result for both tasks.

Set `OWNED_SELECTOR="session:$RUN-* name:impl-*"`, after naming implementers
`impl-a` and `impl-b`. Verify its exact match set and run the
[grouped wait](coordination.md#grouped-progress). Save working and rest evidence
where observable. A short missed transition is not checked, not invented.

Freeze both writers and reconcile queue/background jobs. Launch independent
read-only reviewers as in [review](review-delivery.md#review-and-corrections).
Require approve/reject findings for each exact diff. Run E3 on A before delivery.
Use a native check pane for each frozen candidate, then for the merged target:

```sh
python3 -c 'from pathlib import Path; assert Path("a.txt").read_bytes() == b"alpha\n"'
python3 -c 'from pathlib import Path; assert Path("b.txt").read_bytes() == b"beta\n"'
git diff --check
```

Run only the file's check in its candidate; run both after both merges. Use
[ship commit and merge](review-delivery.md#local-delivery) once per accepted
worker, explicit `--into main --squash`. Squash permits the independent branches
to integrate in order. Save source SHAs, target before/after, committed paths,
review evidence, clean status, and integrated exits. Do not substitute raw Git
commit/merge for native worker delivery. Record dependency readiness from actual
outcomes. Finish with E7.

## E2: Competing implementations

Use the fixture base and fan task, concurrency 2, and a fresh group:

```sh
GROUP="fan/$RUN-choice"
ASSIGNMENT='Implement choice.txt containing exactly selected and a newline. Only edit choice.txt in this scratch worktree. Run a byte-content check and git diff --check. Do not commit, merge, launch agents, ask human questions, or request approvals. Report the task/attempt ID, checks and blocker. Stop all writers at turn end.'
tuios fan 2 --repo "$REPO" --base "$BASE" --agent "$HARNESS" \
  --grants read,write --name "$GROUP" --wait "$ASSIGNMENT" --json
tuios worktree ls --group "$GROUP" --json
tuios list-agents --select "group:$GROUP" --json
```

Include the actual `TASK_F` and distinct returned attempt identities in the
record. Inspect every prompt delivery outcome before any retry. Follow
[fan comparison](workers.md#competing-attempts): grouped wait, freeze both,
`fan compare`, `fan diff`, and `fan verify` with this trusted check:

```sh
tuios fan verify "$FAN_SESSION" -- 'python3 -c '\''from pathlib import Path; assert Path("choice.txt").read_bytes() == b"selected\n"'\'''
```

`FAN_SESSION`, `A`, `B`, and `SELECTED` must be returned group sessions. Review
both full diffs and check outputs. Discover native judge schema before verdict;
if discovery is unavailable, record native verdict as blocked. Do not impersonate
a judge or leave a restricted pane. Record selection rationale and disposition
of every sibling. Commit/merge the selected attempt as in E1. Preserve sibling
evidence first. Use `fan keep` only if every sibling removal is authorized and
dirty work has an explicit preservation disposition. Default dirty siblings to
retained; do not force discard to pass cleanup. Record retained branches/stashes
and remove the selected tree only after integration checks. No fan result has
been executed by this task.

## E3: Busy worker queued correction and mail

Before A's first turn ends in E1, observe actual working state. If the turn is
too short, this observation is not checked: use a new authorized fixture attempt
whose prompt includes a bounded 15-second foreground sleep before its file
check. Do not send a second implementation assignment to the existing worker.
Queue a stable correction exactly once while working:

```sh
tuios queue -s "$SESSION" -w "$PANE" \
  'TASK_A/attempt-1/correction-1: Replace alpha-draft in a.txt with exactly alpha and a newline. Check its bytes. Report this correction ID exactly once with the check exit. Do not edit another path, change scope, or ask for input.'
tuios queue ls -s "$SESSION" -w "$PANE" --json
```

Replace TASK_A with its actual ref. Save returned queue ID, working baseline,
and correction text. Require an explicit correction result with increased turn
sequence and correct file bytes. Verify no second prompt/queue/mail delivered
the correction and no duplicate correction result. Require `a.txt` to change
from the draft content to `alpha\n`. Queue absence alone fails to prove execution.
On stalled/uncertain delivery stop and reconcile; never blindly resend. Also
record one real native review note and `review send` delivery for a separate,
uniquely named authorized verification follow-up: on the changed `a.txt` line,
request a byte-content check and its exact exit code before final acceptance.
Do not deliver that follow-up with `queue` too. Inspect its result, then re-review.

For mail, follow [same-session coordination](coordination.md#asynchronous-mail-and-thread-waits).
Only run the exchange from a real authorized coordinator pane inside the worker
session; record that pane as `INBOX`. Use its actual sender ID. Save message ID,
worker explicit inbox read, reply with `--reply-to`, thread-specific wait, and
coordinator explicit `-w "$INBOX" --thread "$MESSAGE" --unread` read. If no such
coordinator exists, mark mail blocked; direct ask/queue is not proof of mail.
Do not use the defective Pi probe example described below.

## E4: Controlled checkpoint restore

Use a fresh owned native worktree and Pi pane, dedicated to `restore.txt`.
Record its initial HEAD, index tree, status, and process/queue inventory.
Use one bounded ask to write `good\n`; require a completed native turn, then
list checkpoints and inspect the returned checkpoint diff. Use a second bounded
ask to write `bad\n`; save its completed turn, checkpoint list, and file bytes.
Select `GOOD_TURN` from actual list/diff content, not an assumed numbering rule.

Quiesce as in [controlled recovery](review-delivery.md#controlled-checkpoint-recovery):
explicit no-write acknowledgement, no pending owned prompt, no background writer,
and idle/done state. Do not wake the worker in the restore window. Then run:

```sh
tuios checkpoint diff -s "$SESSION" -w "$PANE" "$GOOD_TURN"
tuios checkpoint restore -s "$SESSION" -w "$PANE" "$GOOD_TURN"
tuios checkpoint list -s "$SESSION" -w "$PANE" --json
python3 -c 'from pathlib import Path; assert Path("restore.txt").read_bytes() == b"good\n"'
```

Run the Python check from that recorded worktree. Require a new safety checkpoint,
unchanged HEAD/index/branch, expected restored diff, and no omitted fixture file.
Under the same no-writer procedure restore the safety checkpoint; require
`bad\n` again. Never use force. Retain checkpoint evidence until disposition.
Missing checkpoints or an uncertain writer blocks this exercise.

## E5: Interruption and reconciliation

Use E1 resources. Save a handoff after each of three boundaries: native launch
returned, correction queued, and ship merge returned. At each boundary stop only
the orchestration activity, not the shared daemon or a worker. Resume from a
fresh reading of the saved Aven context and native inventory, not a fresh launch.
Do not repeat a side effect to simulate lost output. Inspect the evidence as if
the last success line had been lost; retain that line for independent comparison.

Run [reconciliation](recovery.md#resume-without-duplicate-effects) for worktrees,
agents, queues, checkpoint list, repository status/history, and target SHAs.
Match full IDs, paths, branches, task/attempt IDs, and prompt/correction receipts.
Require the same worker count and IDs after launch recovery; one correction ID
and outcome after queue recovery; unchanged integrated target SHA and one matching
source/squash outcome after merge recovery. Record each reuse/no-retry decision
before continuing. Unknown delivery means blocked, not a duplicate assignment.
This tests dispatcher interruption, not daemon-crash persistence. Do not claim
that volatile mail or queue survives a daemon restart.

## E6: Live dashboard updates

Use the [dashboard probe](dashboard.md#verification-and-limits) from one owned
orchestrator pane, separate from workers. Render a snapshot from E1/E2 observed
state; retain raw observations. Do not present the example JSON as live data.
Run native validate and show once, record the surface ID, then get it. Capture
client focus/session before and after without switching focus.

For successive snapshots, increase revision and change actual task/dependency,
worker state, attempt, queue, review, check, delivery, blocker, and cleanup fields
at their observed lifecycle boundaries. Use the documented helper patch command,
then `tml patch` and `tml get` for the same ID. Require exact readback of changed
values. Replay the old patch once: require guard failure and unchanged state.
Inspect layout and confirm no forms, questions, actions, or focus changes. Close
only that surface after evidence is saved. If show fails with unknown `tml-open`,
record live updates and layout as blocked; native validation alone is not a pass.

## E7: Cleanup and zero-input audit

Follow [owned cleanup](recovery.md#cleanup). Record per-attempt disposition,
preserve useful checkpoints/logs, stop owned check/event processes, and remove
only approved owned native worktrees. Re-inventory. Require no unaccounted owned
writer and no unrelated resource removed. List retained branches, trees, stashes,
checkpoints, surface IDs, and reasons. Do not delete `root` before evidence handoff.

Audit complete command logs and worker/reviewer messages for all exercises.
Require zero person-directed questions, approval forms/requests, permission
answers, or focus-switch actions. A blocker report is valid; it is not a pass
for the blocked feature. Do not provoke a permission prompt to test refusal.
If native fan/queue creates an Inbox question on held/stalled delivery, record
the event: strict zero-request acceptance is unmet even if no one answered it.
Document review covers the refusal path when it did not occur live.

## Known defects and gaps

- Pi mail probe step 3 uses `--from "$TUIOS_PANE_ID"` from the dispatcher while
  targeting a separate worker session. It does not establish a real coordinator
  inbox there, and its readback omits `-w`, so it is a session observation, not
  an explicit inbox read. This conflicts with the coordination guide. The owner
  must repair it before treating that probe as mail acceptance. No file outside
  this task's write scope was changed.
- Host evidence reports native TML validation exit zero. The validate log is
  empty; this task did not repeat that probe. `dashboard-show.log` records unknown
  `tml-open`. `capabilities/daemon-gap.txt` records unknown `list-verbs` and rejected
  `wait-for --new`. Do not restart the shared daemon. Use supported bounded waits
  with new-turn/result evidence; schema-dependent judge and live TML stay blocked.
- Evidence base supplied for this run:
  `/Users/kenbanks/Software/Public/skills/.git/dispatch/43ce94052d5c/`.
  Read `dashboard-validate.log`, `dashboard-show.log`, and
  `capabilities/daemon-gap.txt` there. These are external evidence, not portable
  install dependencies. Command snapshots are syntax evidence, not runtime passes.
- This worker has no `tuios` executable. No live agent, fan, queue, mail, checkpoint,
  ship, cleanup, or dashboard update test was run here. Live acceptance is tracked
  separately in SKL-2R45. Needs-input/error transitions, narrow layouts, remote
  rendering, and container identity/state transport remain unverified or unsupported
  as stated in their guides. Do not claim green end-to-end acceptance.
