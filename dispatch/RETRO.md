# Retrospective: two-worker dispatch demo

Scope: current session; tasks SND-ZVHA and SND-RES6. Both completed, merged into `main` at `ef123988b4ad1b61d57a573cb1766311df76fdd0`, and cleaned up. These are proposed environment improvements, not implemented fixes.

Sources: session tool results; `aven show SND-ZVHA --full`; `aven show SND-RES6 --full`; installed dispatch runtime, worker, merge, and recovery procedures; Workmux/Aven help; repository files and Git hook configuration.

## 3. Medium — preflight Aven routing across host and sandbox

- Evidence: initial `aven doctor` reported the local database missing, while global configuration already contained a Sandbox path mapping. The newly created local database initially listed no projects. Workers needed explicit `/home/dev/.aven/tasks.db` routing to share the host's `/Users/kenbanks/Software/Sandbox/.aven/tasks.db` rather than infer a worktree-local database.
- Candidate: provide a dispatch preflight that checks database availability separately from configured path mappings, verifies the project exists in the selected database, and emits host/guest routing for worker prompts. Confirm shared task visibility before implementation starts.
- Acceptance: host and worker read the same task IDs; missing database/project state yields a specific setup action rather than an ambiguous routing error. Keep runtime paths generated from configuration, not copied into permanent instructions.

## 4. Low — capture immutable launch evidence and trim discovery output

- Evidence: starting SHAs were read from worker HEAD after startup. They were correct in this run, but a faster worker could commit before that read. Broad Workmux help and the complete global config also introduced mostly unused output.
- Candidate: record the Git-resolved base SHA before launch and verify the created branch against that launch record. Inspect targeted help and relevant configuration fields during routine preflight; reserve full dumps for diagnosis.
- Acceptance: launch evidence remains accurate even if a worker commits immediately, and routine preflight reports only execution mode, agent, sandbox config, routing, and base revision.
