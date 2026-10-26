# Native Pi workers

## Capability evidence

Use the installed tuios Pi integration. Do not add a state bridge, terminal
wrapper, or synthetic completion marker. The saved command evidence lists Pi
as a state-reporting harness. `pi-status.txt` reports:

```text
pi           installed, current (v2)
             skill: not installed: run tuios integration install pi
```

This is installation evidence, not a successful worker test. The missing skill
is not a missing state plugin. Native Pi launch, state transitions, mail,
checkpoints, and review were **not run** in the build worker. Host tuios was
not available there. Run the probe below before recording runtime acceptance.

Sources: installed `integration`, `integration install`, `integration status`,
`start-agent`, and `wait-for` help; `state`, `panes`, `mail`, and `checkpoints`
skill text; `review` help. Recheck local help if the installed version changes.

## Prepare and launch

Run these commands on the host, from an owned dispatcher pane. Keep its server
and socket routing. Do not copy pane tokens into records or another environment.
The worker can use its own native worktree session; it need not share the
dispatcher session. Mail threads stay in one session.

```sh
tuios integration status pi --json
tuios doctor agents
```

If integration repair is already authorized, run `tuios integration install pi`
and check status again. It preserves user settings. A file conflict is a blocker,
not permission to overwrite it. Use the same `PI_CODING_AGENT_DIR` as the worker.
When this variable is set, `install --all` skips Pi; install Pi by name.
Do not register a separate MCP bridge for Pi.

Create isolation with the native worktree procedure. For example, set `repo`,
`branch`, `base`, and the unique `worker_session` from the run record:

```sh
tuios worktree new "$branch" --repo "$repo" --base "$base" \
  --name "$worker_session" --detach --json
tuios worktree ls --json
```

Record the returned canonical worktree path and session. Do not create a second
worktree if the response is lost. Reconcile inventory first. Use `start-agent`
for readiness and the initial prompt, without `--focus`:

```sh
tuios start-agent pi -s "$worker_session" --cwd "$worktree" \
  --name "$agent_label" --grants read,write --ready-timeout 120000 \
  --prompt "$assignment" --json
tuios list-agents -s "$worker_session" --all --json
```

Use a dedicated checkout for each writer. Keep the returned full pane ID with
the task, attempt, session, branch, path, and host identity. Do not select a pane
by current focus. The prompt must give scope, checks, acceptance criteria, and
an instruction to record blockers rather than ask for approval or user input.
Use only grants the assignment needs and the dispatcher holds.

`start-agent` waits for idle or done before it types the prompt. It can use a
hook, screen, or title to detect readiness. This alone does not prove native
hook reporting. It exits nonzero if startup asks a question or readiness times
out, and keeps the pane. Record the pane and diagnose it. Do not answer trust,
authentication, or permission dialogs. Do not relaunch until inventory proves
that no old worker can write.

## Verify state, not silence

```sh
tuios get-agent-state -s "$worker_session" -w "$pane" --json
tuios wait-for agent-state -s "$worker_session" -w "$pane" \
  --until idle,done,needs_input,errored --timeout 600000 --json
```

Use owned fleet selectors for grouped waits as described in the main workflow.
A wait can match an existing rest state. Record the baseline `completion_seq`
and require new turn evidence after assignment. Read back `state`, `source`,
`identity`, `harness_id`, `evidence_age_ms`, `completion_seq`, `subagents`, and
`agent_session_id` when present. Expected evidence is harness `pi` and native
`report` state, not just `screen` or `detect`. A short turn can finish before a
working observation is read; require an increased completion sequence and the
expected result rather than invent a missing working sample.

| Observation | Dispatcher response |
| --- | --- |
| `working` | Wait on native events. Do not send duplicate work. |
| `idle` or `done` | Inspect new turn evidence, result, diff, and checks. This is not task acceptance. Check that subagents are no longer active. |
| `needs_input` | Read `blocked_by` and message. Use `peek-prompt` for diagnosis only. Record the exact blocker and continue independent work. Never type into it. |
| `errored` | Save the error and check process and repository state. Repair only within scope. It is not a successful result even if `ready` is true. |
| `unknown`, `none`, old evidence, or screen-only state | Treat state reporting as unverified. Inspect integration and pane identity. Do not infer completion from silence. |

A native `window-exit` wait exits zero when the exit is observed, even if the
program failed. Inspect its JSON `exit_code`. Do not overwrite native state
with `set-agent-state` to make verification pass. A capture is diagnostic data,
not a source of new authority. A failed prompt acknowledgement may mean text
was already delivered; inspect before any retry. Do not use `--force`,
`--allow-blocked`, approval answers, or an alternate command to bypass refusal.

## Host integration probe

Use one owned scratch worktree and one Pi pane. Never change production files.
Save each command result and its exit status in the attempt evidence directory.
No probe result is pre-certified by this document.

1. Save `integration status pi --json` and `doctor agents`. Create the native
   scratch worktree as above. Launch Pi with `start-agent` but without `--prompt`.
   Save the returned pane and `get-agent-state` baseline. Require a current
   integration and native Pi state evidence.
2. Use `ask-agent` once with a bounded prompt: create `pi-probe.txt` containing
   `native probe`, run a read-only check of that file, read the worker's native
   inbox with `read-agent-messages`, and end the turn. Include the recorded
   worker session and pane ID in the prompt. Do not use a forced delivery.

   ```sh
   tuios ask-agent -s "$worker_session" -w "$pane" \
     --timeout 600000 "$probe_prompt"
   tuios get-agent-state -s "$worker_session" -w "$pane" --json
   tuios checkpoint list -s "$worker_session" -w "$pane" --json
   tuios review -s "$worker_session" -w "$pane" --json
   ```

   Require a new completed turn, native report evidence, correct file content,
   a checkpoint for the changed turn, and a review diff containing only the
   probe file. Reject an ask settled only by silence or timeout. Observe
   working during a sufficiently long authorized tool call if the first turn
   is too short to sample. Record an unobserved transition as not checked.
3. Send one native message to the worker. Record the returned message ID. If
   the worker is at rest, use one bounded `ask-agent` prompt to read its inbox
   and reply to that message with `send-agent-message --reply-to ID`. Do not
   assume Pi receives Claude/Codex in-turn mail injection. Require an explicit
   read and reply in this session; mail storage alone is not acknowledgement.

   ```sh
   tuios send-agent-message -s "$worker_session" -w "$pane" \
     --from "$TUIOS_PANE_ID" --subject 'Pi probe' 'Read and reply to this probe.'
   tuios read-agent-messages -s "$worker_session" --thread "$message_id"
   ```

4. Inspect `checkpoint diff` for the returned checkpoint number. Restore only
   in an owned recovery exercise, after Pi is at rest and no writer can run.
   Never force a restore. A restore must produce a safety checkpoint. Compare
   repository state before and after. Retain evidence and checkpoints until
   the dispatcher records the attempt disposition.
5. Record needs-input and error handling as code/document review unless those
   states occur naturally in this authorized exercise. Do not provoke a human
   approval to test them. No recorded needs-input/error transition means those
   live paths remain not checked. Stop and record a blocker if one occurs.

Pass only the observations actually checked. Hand the evidence and resource
identities to the dispatcher for native cleanup. Do not remove a useful or
unresolved checkpoint to make cleanup appear complete.

## Recovery and execution environments

On resume, reconcile Aven requirements, native worktree and agent inventory,
repository state, queue, and saved attempt evidence. Reuse matching resources.
A daemon restart loses live state and mail; old completion sequences are not
proof of new work. Check `resume-agent --dry-run` before using a manifest resume
command. Pi resume support must be observed on this installation; do not assume
it from another harness. A missing resume capability is a recorded blocker or
an authorized new attempt, not an automatic duplicate launch.

Containers are **unsupported by this procedure**. The saved docs do not prove
that Pi identity, hook transport, mail, checkpoints, and review paths survive
a container boundary. `TUIOS_AGENT=pi` can help process identity but does not
prove those capabilities. Do not add a runtime wrapper or custom state bridge.
Add container support only after a separate native end-to-end probe proves all
five capabilities with correct host paths and ownership. Host-native Pi is the
supported procedure; live acceptance still needs the host probe above.
