RESULT: Defined the dispatch interface and added 15 passing local safety tests. Commit: aa09ccda33d71de9d643a94e11611d5b51083455.

- design.md records dispatch/worker/Workmux/Aven ownership, the minimum saved worker record, and launch/integrate/finish/inspect targets. It states runtime and multiplexer assumptions. Baseline code matches reviewed revision 41298fe3db351c6c2a7aa4b0688740b426e141c1. The stated normal-path recipe counts 35 dispatcher commands (18 helper calls), 100 helper value slots, 23 saved files, and 5 Aven events.
- All acceptance checks passed: tests cover wrong repository/base/worker identity, dirty/untracked/ignored files, hidden index flags, unfinished operations/locks, stale launch/base/worker revisions, unmerged work, missing/failed/stale reports, failed checks, uncertain exit, and false closure evidence. Failed guards prevent later checks, launch, removal, or success-note creation and retain relevant evidence/resources. Positive controls pass.
- Checks: python3 -m unittest discover -s tests -v (15 passed); ruff check tests; ruff format --check tests; git diff --check; staged whitespace and commit secret checks passed. Host: Python 3.15.0, Git 2.56.0, Ruff 0.17.0. Full local log: .ralph/run.keWTxw/1/checks.log.

Blockers: none. No live worker/container was used or required. Existing helper interfaces are test seams, not compatibility requirements. Current cleanup relies on caller assertions when container evidence is absent; the target record must join the completion guards. Pending cleanup is separate from task completion per the epic decision.

Next: SKL-WY57 can implement the saved worker record. Later tasks must move these safety tests to the new lifecycle interface and measure after-counts. No lifecycle refactor was included here.
