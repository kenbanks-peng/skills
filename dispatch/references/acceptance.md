# Live release checks

Documentation and helper tests do not prove orchestration. Run these exercises
in a scratch repository with configured harnesses, not the user's working tree.
Keep logs outside disposable worktrees. Record command exits, resource IDs,
candidate/target commits, and before/after pane inventories (including hidden
windows and all owned hosts). Observe visibility during commands as well as
after them; closing a stray window later does not pass the workspace check.

## Required exercises

| Exercise | Required observations |
| --- | --- |
| Native lifecycle | Two distinct workers in native worktrees; independent review; project checks; ship commit/merge; integrated checks; native cleanup |
| Linux execution | Real Linux worker, host-qualified native state, visible live pane view, Linux checks, local worktree pull and delivery |
| Busy worker | One queued follow-up delivered once; explicit result and new turn |
| Agent communication | ask-agent answer; mail send, explicit inbox read/reply, thread wait/read |
| Competing attempts | fan launch, grouped wait, compare/diff/verify, selection, selected delivery, sibling disposition |
| Recovery | Checkpoint inspect/restore with safety checkpoint; interrupted-run reconciliation without duplicate work |
| Dashboard | One opened TML surface; same ID after patches; actual capture before/after; readable 80-column overview |
| Workspace | Throughout the run, only dispatch, Aven, and active Linux workers visible; no transient shell/merge/review/check/integration windows; final owned inventory contains dispatch only, including after failure |
| No human input | No question, form, approval request, or approval answer in the full run |

Use the commands in the relevant guide; installed help remains the contract.
Exercise needs_input/error handling only when naturally encountered or with a
non-approval fixture. Do not provoke an approval merely to test refusal.

## Test layers

- Unit tests: schema, escaping, patches, helper CLI, compact dashboard structure.
- Documentation checks: links, executable examples, native workflow requirements.
- Native smoke: actual daemon show/get/patch/capture, native worktrees, command
  execution with exit/log cleanup, and ship delivery in an isolated repository.
- Live agents: actual native harness state, asks/queue/mail/checkpoints/fan.
- User setup: real Linux host and visible attached-client layout.

Report each layer separately. A new named server can test the installed binary
without restarting the shared server, but it cannot certify the shared server
or an unconfigured Linux host.

## Current verification

No previous prose-only acceptance claim carries forward. Save the current
verification results in the [verification report](verification.md).
Any exercise without a recorded live result remains not checked.
