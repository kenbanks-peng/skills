# Verification

## Tested in this revision

- 21 local tests pass: links, examples, helper CLI, snapshot validation, guarded
  patches, read-only tabs, compact overview, and pane/Linux procedures.
- Opt-in native smoke passes on a new isolated tuios 0.11.1 server:
  dashboard validate/render/show/get/patch/capture; stale patch rejection;
  native worktree create/remove; passing and failing check exit/log capture
  followed by pane closure; live pane-view capture and closure without closing
  its source; ship commit/squash merge; clean target; empty final inventory.
- Live Pi probe on a separate server: native report identity, idle/working/done,
  command result, busy-worker queue q1, and explicit follow-up output observed.
  The queued prompt was initially visible before execution; only the later
  tool result and final response established completion.

## Reproduce native smoke

```sh
DISPATCH_NATIVE_TEST=1 python3 -m unittest discover -s tests -p test_native.py -v
```

The test creates a random named server and scratch repository. It shuts down
only that server. It does not restart the shared daemon or alter demo sessions.

## Remaining limits

- Shared daemon rejects list-verbs/new TML operations; isolated-server success
  does not certify that daemon. No shared restart was performed.
- No Linux hosts are configured here. Linux execution/pull and attached-client
  layout remain not checked. Native local pane-view was tested.
- Default local pi launcher fails in /tmp because fnox has no project config.
  The live probe used the installed Pi executable directly, without changing
  the launcher or global configuration.
- ask-agent returned success with an empty reply. The worker's result was
  confirmed by capture, not by the empty answer.
- Same-session mail send succeeded, but the worker reported inbox permission
  refusal and did not reply. Explicit reply/wait acceptance did not pass.
- Live fan, checkpoint restore, interruption recovery, and full two-worker
  acceptance remain not checked.

All probe panes/sessions were removed and both probe servers stopped.
This is not full live end-to-end acceptance.
