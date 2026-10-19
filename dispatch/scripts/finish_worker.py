#!/usr/bin/env python3
"""Finish one saved worker: inspect, stop, archive, remove, report, and complete."""

import argparse
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

from archive_prompts import archive
from cleanup_worker import validate
from dispatch import ERRORS, error_text, save
from git_preflight import branch_ref, commit, git, operations, paths, require
from stop_worker import stop
from worker_runtime import emit, run


def verification(record):
    integrated = record["integration"]
    require(integrated.get("ok") is True, "No successful independent integration")
    evidence_path = Path(integrated["verification_evidence"])
    worker = Path(record["worktree"])
    require(
        evidence_path.is_absolute()
        and not evidence_path.resolve().is_relative_to(worker),
        "Verification evidence must survive worker removal",
    )
    data = json.loads(evidence_path.read_text())
    require(
        data.get("ok") is True
        and data["tested_sha"] == integrated["verified_base_sha"]
        and data["worker_sha"] == integrated["integrated_worker_sha"]
        and data["base_ref"] == "refs/heads/" + record["base"]
        and data["repo"]["common_dir"] == record["common_dir"]
        and data.get("worker_is_ancestor") is True
        and data.get("base_moved") is False
        and [check["argv"] for check in data["checks"]] == record["acceptance_checks"]
        and all(
            check["status"] == "passed" and check["returncode"] == 0
            for check in data["checks"]
        ),
        "Base verification does not match the saved assignment",
    )
    current_base(record)
    return integrated


def current_base(record):
    repo, integrated = record["repo"], record["integration"]
    require(
        commit(repo, branch_ref(repo, record["base"]))
        == integrated["verified_base_sha"],
        "Base moved since verification; retain resources and verify again",
    )
    git(
        repo,
        "merge-base",
        "--is-ancestor",
        integrated["integrated_worker_sha"],
        integrated["verified_base_sha"],
    )


def observation(record):
    repo, worker = record["repo"], Path(record["worktree"])
    require(worker.is_absolute() and worker == worker.resolve(), "Unsafe worker path")
    require(
        worker != Path(repo) and worker not in Path(repo).parents,
        "Never remove a primary or enclosing worktree",
    )
    listing = git(repo, "worktree", "list", "--porcelain").stdout.split("\n\n")
    primary = listing[0].splitlines()[0].removeprefix("worktree ")
    require(str(worker) != primary, "Never remove the primary worktree")
    matches = [
        entry
        for entry in listing
        if entry.splitlines() and entry.splitlines()[0] == "worktree " + str(worker)
    ]
    if matches:
        require(
            len(matches) == 1 and worker.exists(), "Worker registration is uncertain"
        )
        lines = matches[0].splitlines()
        require(
            "branch refs/heads/" + record["branch"] in lines
            and "HEAD " + record["integration"]["integrated_worker_sha"] in lines,
            "Registered worker identity changed",
        )
        actual = paths(worker)
        git_dir = Path(actual["git_dir"])
        require(
            actual["worktree"] == str(worker)
            and actual["common_dir"] == record["common_dir"]
            and git_dir.parent == Path(record["common_dir"]) / "worktrees"
            and (worker / ".git").is_file()
            and not (worker / ".git").is_symlink()
            and Path((git_dir / "gitdir").read_text().strip()) == worker / ".git"
            and git(worker, "symbolic-ref", "-q", "HEAD").stdout.strip()
            == "refs/heads/" + record["branch"]
            and commit(worker, "HEAD") == record["integration"]["integrated_worker_sha"],
            "Current worker Git identity changed; preserve the resource",
        )
    else:
        require(
            not worker.exists(), "Unregistered resource at worker path; preserve it"
        )
    branch = (
        git(
            repo,
            "show-ref",
            "--verify",
            "--quiet",
            "refs/heads/" + record["branch"],
            allowed=(0, 1),
        ).returncode
        == 0
    )
    if branch:
        require(
            commit(repo, "refs/heads/" + record["branch"])
            == record["integration"]["integrated_worker_sha"],
            "Worker branch changed",
        )
    return {"worktree_present": bool(matches), "branch_present": branch}


def confirm_exit(record, event):
    current = stop(dict(record, finish=None), previous=event["exit_evidence"])
    require(
        current.get("ok") is True and current.get("stopped") is True,
        "Writer exit is no longer confirmed: " + json.dumps(current),
    )


def pending(record, state, reason, evidence):
    resources = []
    for kind, identity in (
        ("worktree", record["worktree"] if state["worktree_present"] else None),
        (
            "branch",
            "refs/heads/" + record["branch"] if state["branch_present"] else None,
        ),
    ):
        if identity:
            resources.append(
                {
                    "resource": kind,
                    "identity": identity,
                    "evidence": str(evidence),
                    "owner": "dispatcher",
                    "next_action": "Inspect retained resource and resolve: " + reason,
                }
            )

    if state["worktree_present"]:
        repo = record["worktree"]
        names = set()
        for argv in (
            ("ls-files", "--others", "--exclude-standard", "-z"),
            ("ls-files", "--others", "--ignored", "--exclude-standard", "-z"),
            ("diff", "--name-only", "-z"),
            ("diff", "--cached", "--name-only", "-z"),
        ):
            names.update(name for name in git(repo, *argv).stdout.split("\0") if name)
        for name in sorted(names):
            resources.append(
                {
                    "resource": "artifact",
                    "identity": str(Path(repo) / name),
                    "evidence": str(evidence),
                    "owner": "dispatcher",
                    "next_action": "Review and preserve changed or unknown content",
                }
            )
    return resources


def housekeeping(record, event, persist):
    # UI is never used to establish writer exit. Do not guess unsupported UI commands.
    ui = record.get("ui", {})
    previous = event.get("housekeeping", [])
    event["housekeeping"] = []
    for agent in ui.get("agents", []):
        item = {
            "resource": "UI",
            "identity": agent,
            "context": ui.get("context"),
            "owner": "dispatcher",
            "status": "pending",
            "next_action": "Inspect exact saved UI identity in the original multiplexer",
        }
        completed = [
            old
            for old in previous
            if old["resource"] == "UI"
            and old["identity"] == agent
            and old["status"] == "closed"
        ]
        if completed:
            event["housekeeping"].append(completed[0])
            continue
        event["housekeeping"].append(item)
        if ui.get("context", {}).get("backend") == "tmux":
            try:
                pane = agent["pane_id"]
                require(bool(re.fullmatch(r"%[0-9]+", pane)), "Invalid saved pane")
                socket = ui["context"].get("socket_path")
                require(
                    bool(socket) and Path(socket).is_absolute(),
                    "Original tmux server identity is unavailable; preserve the pane",
                )
                # A failed lookup may mean it is gone, but is not proof; preserve uncertainty.
                actual = run(
                    [
                        "tmux",
                        "display-message",
                        "-p",
                        "-t",
                        pane,
                        "#{socket_path}\t#{pane_id}\t#{session_id}\t#{pane_current_path}",
                    ]
                ).strip()
                require(
                    actual
                    == "\t".join((socket, pane, agent["session"], record["worktree"])),
                    "UI identity changed",
                )
                run(["tmux", "kill-pane", "-t", pane])
                item.update(status="closed", next_action=None)
            except ERRORS as exc:
                item["error"] = error_text(exc)
        persist()
    parent = record.get("cleanup_parent")
    if parent and any(
        old["resource"] == "empty-parent"
        and old["identity"] == parent
        and old["status"] == "removed"
        for old in previous
    ):
        event["housekeeping"].extend(
            old for old in previous if old["resource"] == "empty-parent"
        )
        return
    if parent:
        item = {
            "resource": "empty-parent",
            "identity": parent,
            "status": "pending",
            "owner": "dispatcher",
            "next_action": "Inspect and remove only if empty",
        }
        event["housekeeping"].append(item)
        try:
            path = Path(parent)
            require(
                path == path.resolve(strict=True)
                and path == Path(record["worktree"]).parent
                and path != Path(record["repo"])
                and path not in Path(record["repo"]).parents
                and path not in Path(record["common_dir"]).parents,
                "Unsafe parent path",
            )
            os.rmdir(path)
            item.update(status="removed", next_action=None)
        except ERRORS as exc:
            item["error"] = error_text(exc)
        persist()


def finish(record, path, authorize=False, inspect_only=False):
    require(record["branch"] != record["base"], "Worker and base branches must differ")
    integrated = verification(record)
    state = observation(record)
    plan = {
        "repo": record["repo"],
        "worktree": record["worktree"],
        "branch": record["branch"],
        "base": record["base"],
        "verified_base_sha": integrated["verified_base_sha"],
        "worker_sha": integrated["integrated_worker_sha"],
        "runtime": record["runtime"],
        "container": record.get("container"),
        "ui": record.get("ui"),
        "prompts": record["prompts"],
        "cleanup_parent": record.get("cleanup_parent"),
        "sequence": [
            "stop",
            "archive",
            "worktree",
            "branch",
            "housekeeping",
            "durable report",
            "task done",
        ],
    }
    event = record.setdefault(
        "finish",
        {
            "authorized": False,
            "actions": {},
            "delivered": False,
            "task_complete": False,
            "pending_cleanup": [],
            "housekeeping": [],
            "plan": plan,
        },
    )
    require(event["plan"] == plan, "Saved finish plan changed; judgment is required")
    if inspect_only:
        return {
            "ok": True,
            "inspection": state,
            "saved_finish": event,
            "writer": stop(
                dict(record, finish=None), previous=event.get("exit_evidence")
            ),
        }
    if not (authorize or event["authorized"]):
        return {
            "ok": True,
            "dry_run": True,
            "plan": event["plan"],
            "observation": state,
        }
    event["authorized"] = True
    event.update(ok=False, delivered=False)
    event.pop("error", None)

    def persist():
        save(path, record)

    def action(name, operation):
        event["actions"][name] = "attempted"
        persist()
        result = operation()
        event["actions"][name] = "complete"
        persist()
        return result

    def guarded_state():
        current_base(record)
        observed = observation(record)
        for kind in ("worktree", "branch"):
            require(
                not (
                    observed[kind + "_present"]
                    and event["actions"].get(kind) == "complete"
                ),
                "Completed " + kind + " reappeared; preserve it and request judgment",
            )
        return observed

    persist()
    try:
        state = guarded_state()
        event["stop"] = stop(
            dict(record, finish=None), execute=True, previous=event.get("exit_evidence")
        )
        persist()
        require(
            event["stop"].get("ok") is True and event["stop"].get("stopped") is True,
            "Writer exit is uncertain: " + json.dumps(event["stop"]),
        )
        event["exit_evidence"] = event["stop"]
        persist()
        event["delivered"] = True
        # Stop may take time: do not archive against the pre-stop snapshot.
        state = guarded_state()
        for kind in ("worktree", "branch"):
            require(
                state[kind + "_present"] or kind in event["actions"],
                "Unexpected missing " + kind + "; inspect saved identity",
            )
        cleanup_error = None
        try:
            if state["worktree_present"]:
                for entry in record["prompts"]:
                    name = "archive:" + entry["path"]
                    target = path.parent / "archive" / Path(entry["path"]).name
                    source = Path(record["worktree"]) / entry["path"]
                    if not source.exists() and name in event["actions"]:
                        require(
                            not source.is_symlink()
                            and not target.is_symlink()
                            and hashlib.sha256(target.read_bytes()).hexdigest()
                            == entry["sha256"],
                            "Missing prompt has no matching durable archive",
                        )
                        event["actions"][name] = "complete"
                        persist()
                        continue

                    def archive_one(entry=entry, target=target, name=name):
                        current = stop(
                            dict(record, finish=None), previous=event["exit_evidence"]
                        )
                        require(
                            current.get("ok") and current.get("stopped"),
                            "Writer exit changed",
                        )
                        guarded_state()
                        single = dict(record, prompts=[entry])
                        result = archive(single, current, target.parent, execute=True)
                        event.setdefault("archives", {})[name] = result
                        require(result["ok"], result.get("error", "Archive failed"))

                    action(name, archive_one)

                current_base(record)
                args = SimpleNamespace(
                    repo=record["repo"],
                    worktree=record["worktree"],
                    branch=record["branch"],
                    base=record["base"],
                    worker_commit=integrated["integrated_worker_sha"],
                    verified_base_sha=integrated["verified_base_sha"],
                    receipt=None,
                    stop_evidence=None,
                    parent=None,
                )
                validate(args)
                confirm_exit(record, event)
                action(
                    "worktree",
                    lambda: git(
                        record["repo"], "worktree", "remove", "--", record["worktree"]
                    ),
                )
            else:
                event["actions"]["worktree"] = "complete"
                persist()
            if state["branch_present"]:
                current_base(record)
                require(not operations(record["repo"]), "Git operation in progress")
                guarded_state()
                confirm_exit(record, event)
                action(
                    "branch",
                    lambda: git(record["repo"], "branch", "-d", "--", record["branch"]),
                )
            else:
                event["actions"]["branch"] = "complete"
                persist()
        except ERRORS as exc:
            cleanup_error = error_text(exc)
        state = observation(record)
        event["pending_cleanup"] = pending(
            record, state, cleanup_error or "Removal pending", path
        )
        if cleanup_error:
            event["cleanup_error"] = cleanup_error
        else:
            event.pop("cleanup_error", None)
        housekeeping(record, event, persist)
        current_base(record)
        confirm_exit(record, event)
        # Report is durable outside removed resources, then saved to Aven before status changes.
        report = path.parent / "completion.md"
        body = (
            "VERIFIED: Integrated work passed independent checks; exact worker exit confirmed.\n"
            + "- Verification: "
            + integrated["verification_evidence"]
            + "\n"
            + "- Pending cleanup: "
            + json.dumps(event["pending_cleanup"])
            + "\n"
            + "- Housekeeping (not a delivery gate): "
            + json.dumps(event["housekeeping"])
            + "\n"
            + "- Finish evidence: "
            + str(path)
            + "\n"
        )
        with report.open("w") as output:
            output.write(body)
            output.flush()
            os.fsync(output.fileno())
        report_sha = hashlib.sha256(body.encode()).hexdigest()
        routing = [
            part
            for key, value in record["routing"].items()
            for part in ("--" + key, value)
        ]
        # Duplicate notes after interruption are safe; never infer a failed write succeeded.
        if (
            event["actions"].get("report") != "complete"
            or event.get("report_sha256") != report_sha
        ):
            action(
                "report",
                lambda: run(
                    [
                        "aven",
                        "note",
                        record["task_ref"],
                        "--file",
                        str(report),
                        *routing,
                    ],
                    record["repo"],
                ),
            )
            event["report_sha256"] = report_sha
            persist()
        current_base(record)
        confirm_exit(record, event)
        if event["actions"].get("task") != "complete":
            action(
                "task",
                lambda: run(
                    [
                        "aven",
                        "edit",
                        record["task_ref"],
                        "--status",
                        "done",
                        "--clear-agent",
                        *routing,
                    ],
                    record["repo"],
                ),
            )
        event.update(ok=True, task_complete=True)
    except ERRORS as exc:
        event.update(ok=False, error=error_text(exc))
    finally:
        persist()
    return event


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task")
    parser.add_argument(
        "--authorize-finish",
        action="store_true",
        help="Authorize the saved plan once, including report and task completion",
    )
    parser.add_argument(
        "--inspect", action="store_true", help="Observe without mutation"
    )
    args = parser.parse_args()
    try:
        require(
            bool(re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", args.task)),
            "Use the full task reference",
        )
        common = Path(paths(Path.cwd())["common_dir"])
        with (common / "dispatch.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            path = common / "dispatch-workers" / args.task / "worker.json"
            record = json.loads(path.read_text())
            require(
                record["schema_version"] == 1
                and record["task_ref"] == args.task
                and record["common_dir"] == str(common)
                and paths(record["repo"])["common_dir"] == str(common),
                "Saved worker record identity mismatch",
            )
            require(
                not path.resolve().is_relative_to(Path(record["worktree"])),
                "Evidence must be outside worker resources",
            )
            return emit(finish(record, path, args.authorize_finish, args.inspect))
    except ERRORS as exc:
        return emit({"ok": False, "error": error_text(exc)})


if __name__ == "__main__":
    raise SystemExit(main())
