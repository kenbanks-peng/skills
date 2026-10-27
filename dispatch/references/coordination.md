# Coordination

## Select the owned fleet

Use a run-specific session/group and worker-name selector. Check its match set
once after launch and after inventory changes. Include all selected hosts.

```sh
tuios list-agents --all-hosts --select "$OWNED_SELECTOR" --json
tuios wait-for agent-state --select "$OWNED_SELECTOR" --until idle,done,needs_input,errored --every --timeout 3600000 --json
```

Use host-scoped waits where the installed version does not aggregate hosts.
Select workers by stable identity and put awaited states in --until. A rest state ends a turn,
not acceptance. For each assignment require a new completed turn and its result;
an already idle worker is not a completed assignment.

## Ask now, queue next, mail asynchronously

```sh
tuios ask-agent -s "$SESSION" -w "$PANE" --timeout 600000 'Return the current task result, checks, and blocker.'
python3 "$skill/scripts/workspace.py" --run-dir "$run_dir" queue --session "$SESSION" --window "$PANE" --id TASK/repair-1 --prompt-file "$PROMPT_FILE"
tuios queue ls -s "$SESSION" -w "$PANE" --json
```

Use ask-agent for an immediate answer from a ready worker. Check its reply:
a success with empty reply is not an answer. Read the worker result through
native capture or an explicit reply, retaining the original assignment. Use queue for
authorized next work while busy. This can be a correction or a dependency-ready
next task in the same bounded scope. A task needing a separate checkout gets a
separate assignment/worktree. Use one delivery channel per instruction.

Write the authorized follow-up once in PROMPT_FILE. Reuse its stable --id for
the same work. The script submits through native queue and records the receipt.
A repeated identical request returns the saved receipt without requeueing.
Changed text/target for that ID, blocked state, and uncertain submissions fail.
Reconcile pending requests against native state, keeping their original IDs.
A submitted receipt is not completion, even after a daemon restart.
Save the returned queue ID. Wait for its result, not just queue disappearance.
Prompt text visible in the input box is delivery in progress, not execution.
Use `queue rm` for a known obsolete entry. After uncertain send/launch output,
inspect the native inventory and result before retrying.

Use mail when no immediate turn is needed:

```sh
tuios send-agent-message -s "$SESSION" -w "$PANE" --subject 'dependency ready' 'The dependency is integrated; use the recorded target SHA.'
```

The worker explicitly reads its inbox and replies with `--reply-to MESSAGE_ID`.
For a same-session reply to the dispatcher:

```sh
tuios wait-for agent-message -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" --thread "$MESSAGE" --timeout 600000 --json
tuios read-agent-messages -s "$TUIOS_SESSION" -w "$TUIOS_PANE_ID" --thread "$MESSAGE" --unread --json
```

Mail threads are session-scoped. Use ask/queue for direct cross-session work.
For remote mail, read the thread in HOST:SESSION as documented in the hosts
topic. Use your own sender identity. A read is not an outcome;
require an explicit result when the assignment needs a reply.

## Events and exceptions

Use native events to update the dashboard while workers run:

```sh
tuios list-attention --select "$OWNED_SELECTOR" --json
tuios subscribe --hosts --types agent-state,attention,agent-message,command-finished,window-exit
```

Use a bounded stream read, not a background event service. Filter events by owned
IDs. Save boot/sequence cursors for reconnect if needed. On a gap, inventory
again. Use bounded grouped waits for a stage and refresh the dashboard between waits.

- needs_input: inspect with peek-prompt, record the blocker, continue other work.
- errored/timeout: inspect state and one bounded capture; repair the cause.
- prompt stalled: inspect delivery state and reconcile the original prompt.
- host down: retain the worker identity; wait for its existing link.
- permission error: record the operation and required authority; continue independent work.

Use capture for diagnosis and view verification, not polling for completion.
Keep important replies/results in Aven; native mail and queues are volatile.
