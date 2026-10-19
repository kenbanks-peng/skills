# Retrospective: two-worker dispatch demo

Scope: current session; tasks SND-ZVHA and SND-RES6. Both completed, merged into `main` at `ef123988b4ad1b61d57a573cb1766311df76fdd0`, and cleaned up. These are proposed environment improvements, not implemented fixes.

Sources: session tool results; `aven show SND-ZVHA --full`; `aven show SND-RES6 --full`; installed dispatch runtime, worker, merge, and recovery procedures; Workmux/Aven help; repository files and Git hook configuration.

## 1. High — regression-test sandbox post-merge ref visibility

- Evidence: both workers ran `workmux merge --into main --keep` successfully, then immediately failed their ancestry assertion with `fatal: Not a valid object name refs/heads/main` (exit 128). Subsequent worker diagnostics found the ref; host verification confirmed ancestry at `e7a7b68` and `ef12398`. The cause is unknown; this session does not establish a specific synchronization defect.
- Candidate: add an integration test in the Workmux sandbox/runtime layer that creates two worktrees, merges from the Linux sandbox, and immediately resolves the base ref and checks ancestry from both sandbox and host. Capture timestamps, Git/common-directory paths, mount mappings, and ref-storage configuration on failure. Also cover a peer worktree that appears prunable only inside another worker's sandbox; host registrations were valid here.
- Acceptance: repeated runs preserve immediate ref visibility and valid host worktree registrations. Until diagnosed, retain host reconciliation as the safety gate; a verification failure must not trigger a second merge or pruning of peer worktrees.

## 2. Medium — make demo acceptance a reusable executable check

- Evidence: the repository has no build/check script or CI workflow. Global Git pre-commit hooks do run large-file and secret checks; those are real guardrails, but do not check demo content. Comment counts, pending-marker removal, and exact-content preservation were checked with inline shell/Python commands instead.
- Candidate: add a small deterministic checker with worker-slot and final-integration modes, invoked by the dispatch acceptance commands and a pre-merge hook or CI job. Worker mode must allow the other slot to remain pending; final mode must require both identifying comments exactly once and no pending markers. Test rejection of duplicate comments, missing comments, and unrelated content changes.
- Acceptance: one documented executable command supplies the content gate for workers and dispatch. Keep these mechanical checks out of coding-standards prose.

## 3. Medium — preflight Aven routing across host and sandbox

- Evidence: initial `aven doctor` reported the local database missing, while global configuration already contained a Sandbox path mapping. The newly created local database initially listed no projects. Workers needed explicit `/home/dev/.aven/tasks.db` routing to share the host's `/Users/kenbanks/Software/Sandbox/.aven/tasks.db` rather than infer a worktree-local database.
- Candidate: provide a dispatch preflight that checks database availability separately from configured path mappings, verifies the project exists in the selected database, and emits host/guest routing for worker prompts. Confirm shared task visibility before implementation starts.
- Acceptance: host and worker read the same task IDs; missing database/project state yields a specific setup action rather than an ambiguous routing error. Keep runtime paths generated from configuration, not copied into permanent instructions.

## 4. Low — capture immutable launch evidence and trim discovery output

- Evidence: starting SHAs were read from worker HEAD after startup. They were correct in this run, but a faster worker could commit before that read. Broad Workmux help and the complete global config also introduced mostly unused output.
- Candidate: record the Git-resolved base SHA before launch and verify the created branch against that launch record. Inspect targeted help and relevant configuration fields during routine preflight; reserve full dumps for diagnosis.
- Acceptance: launch evidence remains accurate even if a worker commits immediately, and routine preflight reports only execution mode, agent, sandbox config, routing, and base revision.
