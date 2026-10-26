"""Integrate reviewed work from a saved dispatch record; never clean up or close tasks."""

import contextlib
import copy
import fcntl
import io
import json
import math
import re
from pathlib import Path
from types import SimpleNamespace

from .git import (
    branch_ref,
    commit,
    git,
    git_env,
    normal_index,
    operations,
    paths,
    preflight,
    require,
    status,
)
from .launch import ERRORS, error_text, save
from .reports import worker_result
from .runtime import emit, run
from .verification import handle as verify_main


def identity(record, evidence):
    repo = record["repo"]
    rows = json.loads(
        run(["workmux", "list", "--json", record["handle"]], repo, env=git_env())
    )
    evidence["workmux_list"] = rows
    matches = [row for row in rows if row["handle"] == record["handle"]]
    require(len(matches) == 1, "Expected one current Workmux worker")
    row = matches[0]
    require(
        not row["is_main"]
        and row["branch"] == record["branch"]
        and str(Path(row["path"]).resolve()) == record["worktree"],
        "Current Workmux identity differs from saved worker",
    )
    preflight(
        SimpleNamespace(
            repo=repo,
            worker_worktree=record["worktree"],
            worker_branch=record["branch"],
            base=record["base"],
        ),
        evidence,
    )
    require(
        evidence["repo"]["common_dir"] == record["common_dir"],
        "Saved repository identity changed",
    )


def result(record, note_id, sha):
    argv = ["aven", "show", record["task_ref"], "--full", "--json"]

    data = json.loads(run(argv, record["repo"], env=git_env()))
    note = worker_result(data, record, sha)
    require(note["id"] == note_id, "Reviewed RESULT is stale")
    return note


def checked(record, sha, base, filename, timeout, worker_sha=None):
    """Use the same isolated, pinned verifier for both check gates."""
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = verify_main(
            SimpleNamespace(
                repo=record["repo"],
                base=base,
                worker_commit=worker_sha or sha,
                checks_file=[str(filename.parent / "checks.json")],
                timeout=timeout,
            )
        )
    data = json.loads(output.getvalue())
    save(filename, data)
    require(code == 0 and data["ok"], "Required checks failed; see " + str(filename))
    require(data["tested_sha"] == sha, "Checked revision changed")
    return data


def base_ready(record):
    repo = record["repo"]
    normal_index(repo)
    require(not operations(repo), "Repository has an unfinished Git operation")
    # Workmux may update a different checkout of the explicit base.
    entries = git(repo, "worktree", "list", "--porcelain").stdout.split("\n\n")
    for entry in entries:
        lines = entry.splitlines()
        if "branch refs/heads/" + record["base"] in lines:
            root = lines[0].removeprefix("worktree ")
            normal_index(root)
            require(not operations(root), "Base has an unfinished Git operation")
            require(not status(root), "Base checkout is not clean")


def execute(args):
    repo_identity = paths(Path.cwd())
    common = Path(repo_identity["common_dir"])
    require(
        re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", args.task),
        "Use the full task reference",
    )
    path = common / "dispatch-workers" / args.task / "worker.json"
    with (common / "dispatch.lock").open("r" if args.closure else "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another dispatch operation owns this repository") from exc
        record = json.loads(path.read_text())
        require(
            record["schema_version"] == 1
            and record["task_ref"] == args.task
            and record["common_dir"] == str(common)
            and paths(record["repo"])["common_dir"] == str(common),
            "Saved worker record identity mismatch",
        )
        old = record.get("integration")
        if args.closure:
            require(old and old.get("ok") is True, "No verified integration")
            require(
                commit(record["repo"], branch_ref(record["repo"], record["base"]))
                == old["verified_base_sha"],
                "Base moved; closure rejected",
            )
            return old
        require(
            args.reviewed_commit and args.result_id,
            "--reviewed-commit and --result-id are required after review",
        )
        require(
            re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", args.reviewed_commit),
            "Review requires a full commit SHA",
        )
        if args.reconcile:
            require(
                old and old.get("merge_attempted"),
                "No attempted integration to reconcile; repair and review first",
            )
            require(
                old["reviewed_commit"] == args.reviewed_commit
                and old["result_id"] == args.result_id,
                "Review identity changed",
            )
            event = copy.deepcopy(old)
            event.update(action="reconcile", ok=False)
        else:
            require(
                not old or args.new_attempt,
                "Prior attempt exists; reconcile it or explicitly review a new attempt",
            )
            require(
                not old or not old.get("merge_attempted"),
                "Integration was attempted; reconcile before any new mutation",
            )
            event = {
                "action": "integrate",
                "ok": False,
                "reviewed_commit": args.reviewed_commit,
                "result_id": args.result_id,
            }
        record["events"].append(event)
        record["integration"] = event
        record["ok"] = False
        save(path, record)
        directory = path.parent / ("integration-" + str(len(record["events"])))
        directory.mkdir(exist_ok=True)
        event.update(
            evidence_directory=str(directory),
            record_path=str(path),
            task_ref=record["task_ref"],
            handle=record["handle"],
        )
        try:
            event["result"] = result(record, args.result_id, args.reviewed_commit)
            evidence = {}
            event["preflight"] = evidence
            identity(record, evidence)
            base_ready(record)
            checks = record["acceptance_checks"]
            save(directory / "checks.json", checks)
            worker, repo = record["worktree"], record["repo"]
            base_ref = branch_ref(repo, record["base"])
            if not args.reconcile:
                require(
                    commit(worker, "HEAD") == args.reviewed_commit,
                    "Reviewed commit is stale",
                )
                event["rebase_base_sha"] = commit(repo, base_ref)
                event["rebase_attempted"] = True
                save(path, record)
                event["rebase_output"] = git(
                    worker, "rebase", event["rebase_base_sha"]
                ).stdout
                event["checked_worker_sha"] = commit(worker, "HEAD")
                save(path, record)
                sha = event["checked_worker_sha"]
                checked(
                    record,
                    sha,
                    record["branch"],
                    directory / "worker-checks.json",
                    args.timeout,
                )
                # Recheck identity, commit, and base after arbitrary check commands.
                event["before_merge"] = {}
                identity(record, event["before_merge"])
                require(commit(worker, "HEAD") == sha, "Worker moved after checks")
                require(
                    commit(repo, base_ref) == event["rebase_base_sha"],
                    "Base moved after rebase; no merge attempted",
                )
                base_ready(record)
                require(
                    result(record, args.result_id, args.reviewed_commit)
                    == event["result"],
                    "Reviewed RESULT changed during checks",
                )
                event["merge_argv"] = [
                    "workmux",
                    "merge",
                    "--into",
                    record["base"],
                    "--keep",
                ]
                event["merge_attempted"] = True
                save(path, record)
                # No --rebase here: dispatch has already rebased and checked this SHA.
                event["merge_output"] = run(
                    event["merge_argv"], worker, timeout=args.timeout, env=git_env()
                )
                save(path, record)
            # Reconcile even if Workmux rewrote commits or exited before recording success.
            event["after_merge"] = {}
            identity(record, event["after_merge"])
            actual = commit(worker, "HEAD")
            require(
                git(repo, "rev-parse", actual + "^{tree}").stdout
                == git(
                    repo, "rev-parse", event["checked_worker_sha"] + "^{tree}"
                ).stdout,
                "Integrated worker content differs from checked commit; review required",
            )
            pinned = commit(repo, base_ref)
            require(
                git(
                    repo, "merge-base", "--is-ancestor", actual, pinned, allowed=(0, 1)
                ).returncode
                == 0,
                "Worker is not integrated; do not retry blindly",
            )
            require(
                git(
                    repo,
                    "merge-base",
                    "--is-ancestor",
                    event["rebase_base_sha"],
                    pinned,
                    allowed=(0, 1),
                ).returncode
                == 0,
                "Integrated base lost the pre-integration base",
            )
            event.update(
                integrated_worker_sha=actual,
                integrated_base_sha=pinned,
                worker_rewritten=actual != event["checked_worker_sha"],
            )
            save(path, record)
            # A rewritten commit is new input: check it, never reuse the old SHA's pass.
            if event["worker_rewritten"] or args.reconcile:
                checked(
                    record,
                    actual,
                    record["branch"],
                    directory / "reconciled-worker-checks.json",
                    args.timeout,
                )
            verification = directory / "base-verification.json"
            checked(
                record,
                pinned,
                record["base"],
                verification,
                args.timeout,
                worker_sha=actual,
            )
            require(
                commit(worker, "HEAD") == actual, "Worker moved during verification"
            )
            require(commit(repo, base_ref) == pinned, "Base moved; closure rejected")
            event.update(
                ok=True,
                verified_base_sha=pinned,
                verification_evidence=str(verification),
            )
            event.pop("error", None)
            record.update(
                ok=True,
                next_action="Run dispatch.py finish to stop, clean up, and close the accepted task",
            )
        except ERRORS as exc:
            event.update(ok=False, error=error_text(exc))
            record.update(
                ok=False, next_action="repair/review or reconcile; retain worker"
            )
        finally:
            save(path, record)
        return event


def handle(args):
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError("--timeout must be finite and positive")
    try:
        return emit(execute(args))
    except ERRORS as exc:
        return emit({"ok": False, "error": error_text(exc)})
