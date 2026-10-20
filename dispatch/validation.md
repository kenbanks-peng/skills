# Short workflow validation (SKL-H99C)

This is check evidence and a comparison, not an additional run procedure. [SKILL.md](SKILL.md) is the normal path; [design.md](design.md#before-counts) retains the pre-refactor baseline at `41298fe3db351c6c2a7aa4b0688740b426e141c1`.

## Caller cost

Use the baseline's single-task, single-worker, single-wait counting rule. Count commands invoked by dispatch, not commands inside lifecycle helpers or worker implementation. Read/write tools and actual-diff inspection are excluded on both sides; review remains mandatory. Repeated values count repeatedly, argv check lists count as one slot, and boolean authorization flags are not value slots.

| Helper calls | Calls | Named value slots |
| --- | ---: | ---: |
| launch (task, base, scopes list, checks list) | 1 | 4 |
| select RESULT (task) | 1 | 1 |
| integrate (task, reviewed SHA, RESULT ID) | 1 | 3 |
| finish plan; authorize finish (task each) | 2 | 2 |
| **Default total** | **5** | **10** |
| Explicit extra final-run verification, if assigned (repo, base, worker SHA, checks file) | 1 | 4 |
| **Baseline-equivalent with extra verification** | **6** | **14** |

The same surrounding commands are ready/context (2), active/DISPATCH note (2), wait/status (2), ready again (1), SUMMARY note (1): **8**. Thus the default is **13 dispatcher commands**, or **15** for baseline parity with extra final-run verification and its final-base recheck. Baseline: **35 commands, 18 helper calls, 100 helper value slots**. This is a recipe comparison, not a minimum: polling, repairs, project-specific checks, and optional views add commands. A separate final-run gate is not imposed by dispatch; per-task integration already checks the pinned base independently.

The baseline had **23 saved file instances**, of which **16** were caller-authored inputs or explicitly materialized helper outputs: capability cache (1), initial parameters/prompt/receipt (3), DISPATCH parameters/note (2), preflight JSON (1), merge parameters/prompt (2), checks input (1), verification JSON (2), and VERIFIED and SUMMARY parameters/notes (4). The remaining 7 were stop/archive/cleanup outputs and the archived prompt. The final normal interface requires **0 caller-managed file artifacts**; baseline-parity extra run verification requires **1 checks file** (and an optional retained output). Notes can be written directly through Aven; no note JSON/template files are required. The five baseline Aven events become **four**: DISPATCH, worker RESULT, automatic VERIFIED, SUMMARY; no MERGE report.

### Managed saved artifacts: like-for-like recipe count

Under the baseline's successful one-worker/no-retry assumption, the final normal path saves **9 managed file instances**, versus the baseline's **23**. With the baseline-parity extra final verifier's checks input and retained output, the final count is **11**. These counts include managed outputs, not just caller inputs:

| Final normal-path inventory (relative to the saved worker record directory) | Files |
| --- | ---: |
| `worker.json`, `assignment.md`, `config.yaml`, `prompt-<hash>.md` | 4 |
| `integration-<event>/checks.json`, `worker-checks.json`, `base-verification.json` | 3 |
| `archive/PROMPT-<name>.md`, `completion.md` | 2 |
| **Normal managed total** | **9** |
| Extra final verifier: checks input and retained verification output | **+2** |
| **Baseline-parity total** | **11** |

Code verification: `dispatch.py` creates the record, assignment/config snapshot, and hash-named copy of the one generated prompt; `integrate.py` saves the checks input, worker check result, and independent base result. `finish_worker.py` archives the eligible source prompt and writes the completion report. Preflight, process, stop, action-journal, and completion state are embedded in `worker.json`, not additional files. Atomic-write temporary files and removed detached verification checkouts are not retained artifacts. `test_successful_no_retry_managed_inventory` asserts the exact nine-file inventory after the public lifecycle completes.

Assumptions: one generated prompt, no Workmux commit rewrite, no retries/reconcile, no additional report snapshots or UI artifacts, and no changed, tracked, ignored, or otherwise unsafe artifacts preventing strict archival/removal. In particular, a rewrite/reconcile can add `reconciled-worker-checks.json`, retries add integration logs, and extra distinct prompts add hash copies and archives. The nine-file count is illustrative, **not a promise for live pending-cleanup runs**.

The baseline explicitly excludes source prompt copies, UI ID text, and optional retained full-report snapshots; apply those exclusions here too. The Workmux source `.workmux/PROMPT-*.md` is excluded as a source copy (and removed after safe archive in this successful case). However, the final hash-named launch-time copy **is included**, as is the separate finish archive, even though both contain the same prompt. That is a conservative asymmetry: the baseline inventory did not separately enumerate a launch-time backup of a generated source prompt. The final `assignment.md` is likewise counted, comparable to the baseline's initial rendered prompt. Git/worktree internals, the shared `dispatch.lock`, tool-owned runtime state, and Aven's database are infrastructure, not per-task evidence files in either inventory; Aven events are counted separately above.

This comparison does not claim fewer total files in every actual run. Evidence counts vary with prompts/checks/retries and retained resources; the implementation keeps safety evidence rather than deleting it to meet a count. The separate caller-owned artifact/input reduction above remains the measure of manual plumbing. For context load, the baseline SKILL/runtime/merge documents contain 2,639 whitespace-delimited words; the new default SKILL alone contains 772. Adapter and recovery documents now have explicit exceptional triggers rather than mandatory normal-path reads. Word counts are secondary to the removed caller decisions. The caller now chooses assignment fields once, reviews the actual result once, and authorizes one finish plan. Launch SHA, handle, branch, guest/host paths, container, UI identity, prompt hashes, integrated revisions, and stop/archive receipts are derived or retained rather than repeatedly copied between helper inputs.

## Reproducible local checks

```sh
env PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dispatch/tests -v
ruff check --no-cache dispatch/scripts dispatch/tests
git diff --check
```

`tests/test_documented_workflow.py` exercises the public launch → report → integrate → finish path with real Git and controlled external CLIs. It uses the record created by launch, without hand-constructing identity for later operations. It covers partial launch/resume without replacement, merge failure before delivery, interruption after a successful merge and reconcile without a second merge, completion with retained ignored prompts/unknown content, inspection after done, and cleanup retry after explicit test-owner removal of the unknown artifact and reclassification of the unchanged generated prompt as non-ignored (eligible for strict archive). Docker is selected explicitly for a portable controlled seam, not a live runtime.

The documented-path smoke also verifies uncertain exit blocks completion after successful integration. The full suite additionally verifies failed durable reporting blocks closure, changed identities/base/verification fail closed, strict archive/removal preserves unknown files, and tab/empty-parent failures do not block completion. Document checks resolve all local Markdown links/anchors and invoke help for the documented Python entry points. The controlled path asserts no normal capability discovery. No production lifecycle code or project CI policy changes are required for this documentation rewrite.

Local result: **102 tests passed**, Ruff passed, and `git diff --check` passed. Detailed command output is retained with the worker's `.workmux/h99c-tests.log` and `.workmux/h99c-checks.log` for dispatch to preserve before integration. Ruff was initially absent from the worker and installed with `uv tool install ruff`; this is an environment dependency, not a repository change.

## Live evidence and limits

Read-only host evidence inspected from the worker:

- `/Users/kenbanks/Software/Public/skills/.git/dispatch-workers/SKL-5DEM/worker.json`
- The same directory's `integration-4/base-verification.json` and `completion.md`.

The verification file records all **95 prior tests**, Ruff, and diff checking passing on the independently pinned base `84ad861c847611037ff2a493bd7db3ea4d291c1b`. The completion report confirms exact worker exit and durable reporting; it lists **30 pending cleanup entries** and **1 pending housekeeping entry**. These are retained resources, not successful resource removals. Its `cleanup: removed` verification field concerns the detached verification checkout, not the worker.

Dispatch supplied additional live observations: 5DEM's uncertain/interrupted launch resumed without replacement, independent macOS checks passed twice, finish stopped the exact container and saved reporting before marking done; BYB5 also ran live stop/finish. H99C itself launched sandboxed with exact observed pi process/container identity, without caller-built identity. External evidence `~/Software/Public/dispatch-evidence/skl-6rb3/5dem-{launch,resume,integration-retry,finish}.json` was supplied by dispatch but is not mounted at that path in this worker; these observations are attributed, not claimed as a newly executed live check here.

**Full live destructive cleanup has not passed**: ignored `.workmux` prompts and artifacts are deliberately retained. This worker has no host container CLI and must not integrate/finish itself. Dispatch can run host verification after this RESULT. Controlled cleanup/removal and retry tests pass; they do not prove live UI/backend removal or eliminate the retained cleanup work. Local/Lima automatic exit proof remains unsupported. The repository lock cannot exclude unrelated Git writers that ignore it; independent verification still needs installed check dependencies. The routed Aven database is read-only here: dispatch must post the retained RESULT/evidence before integration.
