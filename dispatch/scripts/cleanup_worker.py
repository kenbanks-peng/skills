#!/usr/bin/env python3
"""Fail-closed removal of one verified, merged linked worktree and branch."""

import argparse
import errno
import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from recovery_snapshot import git, require, state, worktrees
from stop_worker import stop
from worker_runtime import load_receipt


def exact_path(value):
    path = Path(value).absolute()
    if path != path.resolve(strict=True):
        raise ValueError(f"Path must be canonical and contain no symlinks: {value}")
    return path


def check(condition, message):
    if not condition:
        raise ValueError(message)


def ref(repo, branch):
    return require(
        git(repo, "rev-parse", "--verify", f"refs/heads/{branch}^{{commit}}")
    )


def validate(args):
    repo, worker = exact_path(args.repo), exact_path(args.worktree)
    check(
        require(git(repo, "rev-parse", "--show-toplevel")) == str(repo),
        "--repo must be an exact repository root",
    )
    check(
        repo != worker and worker not in repo.parents,
        "Repository used for cleanup cannot be inside the worker",
    )
    check(args.branch != args.base, "Worker and base branches must be distinct")
    for branch in (args.branch, args.base):
        check(not branch.startswith("-"), "Branch cannot start with an option")
        require(git(repo, "check-ref-format", "refs/heads/" + branch))
    for sha in (args.verified_base_sha, args.worker_commit):
        check(
            re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", sha) is not None,
            "Verified revisions must be full lowercase commit SHAs",
        )
    if args.receipt or args.stop_evidence:
        check(
            bool(args.receipt and args.stop_evidence),
            "--receipt and --stop-evidence must be supplied together",
        )
        receipt = load_receipt(args.receipt)
        evidence = json.loads(Path(args.stop_evidence).read_text())
        check(
            receipt["repo"] == str(repo)
            and receipt["worktree"] == str(worker)
            and receipt["branch"] == args.branch
            and evidence.get("ok") is True
            and evidence.get("stopped") is True
            and evidence.get("repo") == str(repo)
            and evidence.get("worktree") == str(worker)
            and evidence.get("handle") == receipt["handle"]
            and evidence.get("container_id")
            == (receipt.get("container") or {}).get("id"),
            "Worker-stop evidence identity mismatch",
        )
        current = stop(receipt, previous=evidence)
        check(
            current.get("ok") is True and current.get("stopped") is True,
            "Worker container exit is no longer confirmed: " + json.dumps(current),
        )
    listing, records = worktrees(repo)
    require(listing)
    check(bool(records), "No registered worktrees")
    check(
        Path(records[0]["worktree"]).resolve() != worker,
        "Never remove the primary worktree",
    )
    matches = [w for w in records if w.get("worktree") == str(worker)]
    check(len(matches) == 1, "Worker must be the exact registered linked worktree path")
    record = matches[0]
    check(
        not any(k in record for k in ("locked", "prunable", "bare", "detached")),
        "Worker is locked, prunable, bare, or detached",
    )
    check(
        record.get("branch") == "refs/heads/" + args.branch,
        "Registered worker branch mismatch",
    )
    check(record.get("HEAD") == args.worker_commit, "Registered worker commit mismatch")
    check(
        require(git(worker, "rev-parse", "--show-toplevel")) == str(worker),
        "Worker root mismatch",
    )
    states = [state(repo), state(worker)]
    for observation in states:
        check(
            observation["ok"],
            "Cannot fully inspect repository/worktree: " + json.dumps(observation),
        )
        check(
            not observation["operations"],
            "Ongoing Git operation or lock: " + str(observation["operations"]),
        )
    worker_state = states[1]
    index = require(git(worker, "ls-files", "-v", "-z"))
    check(
        all(entry.startswith("H ") for entry in index.split("\0") if entry),
        "Index contains non-normal entries (including assume-unchanged or skip-worktree); cannot establish cleanliness",
    )
    check(
        not worker_state["status"]["stdout"],
        "Worker has dirty, untracked, or ignored files",
    )
    check(
        require(worker_state["branch"]) == "refs/heads/" + args.branch,
        "Worker branch identity mismatch",
    )
    check(require(worker_state["head"]) == args.worker_commit, "Worker HEAD changed")
    common = Path(require(worker_state["common_dir"])).resolve(strict=True)
    git_dir = Path(require(worker_state["git_dir"])).resolve(strict=True)
    check(
        common == Path(require(states[0]["common_dir"])).resolve(),
        "Different common Git directories",
    )
    check(
        git_dir != common and git_dir.parent == common / "worktrees",
        "Not a linked worktree Git directory",
    )
    check(
        (worker / ".git").is_file() and not (worker / ".git").is_symlink(),
        "Invalid linked .git file",
    )
    check(
        Path((git_dir / "gitdir").read_text().strip()) == worker / ".git",
        "Linked worktree backlink mismatch",
    )
    check(
        ref(repo, args.base) == args.verified_base_sha,
        "Base changed since verification",
    )
    check(ref(repo, args.branch) == args.worker_commit, "Worker branch tip changed")
    require(
        git(
            repo,
            "merge-base",
            "--is-ancestor",
            args.worker_commit,
            args.verified_base_sha,
        )
    )
    parent = None
    if args.parent:
        parent = exact_path(args.parent)
        check(
            parent == worker.parent,
            "--parent must be the exact immediate worker parent",
        )
        check(
            parent != repo
            and parent not in repo.parents
            and parent != common
            and parent not in common.parents,
            "Parent contains repository or Git metadata",
        )
    return repo, worker, parent, common


def cleanup(args):
    result = {
        "ok": False,
        "executed": bool(args.execute),
        "actions": [],
        "warning": "Passing base verification and stopped writers are prerequisites. Explicit SHAs "
        "are assertions, not proof that required checks passed; no verification JSON is consumed.",
    }
    try:
        if args.execute:
            check(
                args.authorize_cleanup,
                "--execute requires --authorize-cleanup after verification and stopping writers",
            )
        repo, worker, parent, common = validate(args)
        result["plan"] = {
            "repo": str(repo),
            "common_dir": str(common),
            "worktree": str(worker),
            "branch": args.branch,
            "base": args.base,
            "verified_base_sha": args.verified_base_sha,
            "worker_commit": args.worker_commit,
            "parent": str(parent) if parent else None,
        }
        if not args.execute:
            result.update(ok=True, dry_run=True)
            return result
        check(
            validate(args) == (repo, worker, parent, common),
            "Validated resource identity changed before cleanup",
        )
        removal = git(repo, "worktree", "remove", "--", str(worker))
        result["actions"].append(removal)
        require(removal)
        check(
            ref(repo, args.base) == args.verified_base_sha,
            "Base moved during cleanup; branch retained",
        )
        check(
            ref(repo, args.branch) == args.worker_commit,
            "Worker moved during cleanup; branch retained",
        )
        require(
            git(
                repo,
                "merge-base",
                "--is-ancestor",
                args.worker_commit,
                args.verified_base_sha,
            )
        )
        deletion = git(repo, "branch", "-d", "--", args.branch)
        result["actions"].append(deletion)
        require(deletion)
        if parent:
            check(parent == exact_path(str(parent)), "Parent path changed")
            try:
                os.rmdir(parent)
                result["parent"] = "removed empty parent"
            except OSError as exc:
                if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                    raise
                result["parent"] = "retained nonempty parent"
        result["ok"] = True
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result["error"] = str(exc)
    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Dry-run by default. Execution requires BOTH --execute and --authorize-cleanup. "
            "Authorization asserts required checks passed on the supplied exact base SHA and all "
            "worker writers are stopped. Coordinate these explicit arguments with verify_base; no "
            "guessed JSON schema is accepted. Serialize repository lifecycle operations externally: "
            "Git inspection/removal/ref deletion cannot be atomic. Partial failures retain remaining "
            "resources and return exit 1. No Workmux or Aven calls; sessions must be reconciled separately."
        ),
    )
    parser.add_argument(
        "--repo", required=True, help="Exact canonical repository root outside worker"
    )
    parser.add_argument(
        "--worktree", required=True, help="Exact registered linked worker worktree path"
    )
    parser.add_argument(
        "--branch",
        required=True,
        help="Explicit local worker branch (not a ref or handle)",
    )
    parser.add_argument(
        "--base", required=True, help="Explicit local verified base branch"
    )
    parser.add_argument(
        "--verified-base-sha",
        required=True,
        help="Full SHA on which required checks passed",
    )
    parser.add_argument(
        "--worker-commit",
        required=True,
        help="Full verified worker tip SHA, ancestor of base",
    )
    parser.add_argument(
        "--receipt",
        help="Launch receipt; required with --stop-evidence for container workers",
    )
    parser.add_argument(
        "--stop-evidence",
        help="Confirmed stop JSON; rechecked against the container before cleanup",
    )
    parser.add_argument(
        "--parent",
        help="Optional exact immediate parent; rmdir only, nonempty retained",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Perform removal rather than dry-run"
    )
    parser.add_argument(
        "--authorize-cleanup",
        action="store_true",
        help="Explicitly authorize cleanup after verification and stopping writers",
    )
    args = parser.parse_args()
    result = cleanup(args)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
