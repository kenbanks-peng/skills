# Guarded dispatch integration

Dispatch reviews the latest RESULT note, actual commits, diff, and acceptance
criteria. Workers implement changes and repair ambiguous conflicts. They do not
perform normal Git integration.

## Integrate after review

Run from a checkout of the target repository:

```sh
python3 <skill-directory>/scripts/integrate.py APP-1234 \
  --reviewed-commit <full-reviewed-worker-SHA> --result-id <reviewed-RESULT-note-ID>
```

This is the single integration operation. It uses the saved worker record for
the worker identity, explicit local base, required argv checks, and Aven routing.
The caller supplies review evidence, not another assignment.

The command locks the same common-directory `dispatch.lock` as launch. All
dispatch lifecycle operations must honor this lock. It rejects a stale RESULT
ID or reviewed commit, a changed Workmux identity, missing or mismatched explicit
Workmux base metadata, dirty state, hidden index flags, and unfinished Git
operations. Required checks run on the dispatcher; unavailable dependencies fail.

It rebases onto the captured explicit base. It checks the resulting exact commit
in an isolated detached worktree, then checks identity and base movement again.
It runs `workmux merge --into <base> --keep` from the worker with hooks enabled.
It does not ask Workmux to rebase again. Installed Workmux
`0.1.276+herdr.1` supports these flags; `workmux merge --help` confirms that
`--keep` retains the worktree, window, and branch. Do not use hook bypass flags.

After integration, it observes actual worker/base commits and requires ancestry.
If Workmux rewrites the worker commit, it requires the same content tree and
checks the new commit rather than reusing the old check result. A content change
requires review; it cannot receive automatic approval. It independently tests the pinned integrated base
in another detached worktree. Base movement rejects success.

## Evidence and closure

Require `ok: true`. The saved worker record contains the integration event,
reviewed RESULT, exact revisions, Git preflight observations, command outcomes,
and evidence paths. Check JSON files retain argv, status, return code, stdout,
stderr, and exact revisions. Failure checkouts remain available for diagnosis.
Evidence is under the saved record directory, outside worker worktrees.

The command never stops workers, removes their worktrees, or changes Aven status.
Continue with stop, archive, and cleanup using `integrated_worker_sha`,
`verified_base_sha`, and `verification_evidence` from this event.
After cleanup, before the completion note and status change, run:

```sh
python3 <skill-directory>/scripts/integrate.py APP-1234 --closure
```

This read-only gate rejects base movement. Keep repository serialization through
closure; the gate is a snapshot, not a lock that survives command exit.
Uncoordinated Git writers must be stopped or otherwise excluded.

## Failure and interruption

Any conflict or failed check stops the operation. Preserve the worker and any
unfinished Git operation. Dispatch sends ambiguous conflicts or check failures
to the worker for repair; there is no automatic conflict resolution.

After a failure before the merge attempt, repair, review the new RESULT and
commit, then use `--new-attempt` to authorize another attempt explicitly.
Earlier events and evidence remain in the record.

Once a merge was attempted, never repeat it blindly. Use the original review
arguments with `--reconcile`. This mode never rebases or merges. It verifies
current identity, actual ancestry, the current worker commit, and the integrated
base with fresh checks. Thus a merge that succeeded before interruption can be
recovered without a second merge. If ancestry or identity is uncertain, retain
all resources and follow [recovery.md](recovery.md). Do not delete or edit intent
fields to force another merge.

Append a concise BLOCKED note with the error, evidence directory, repair owner,
and next action. A failed Aven write remains a blocker; keep the report locally.
