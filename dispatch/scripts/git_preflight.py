#!/usr/bin/env python3
"""Check Git merge preconditions without changes."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


class CheckError(Exception):
    pass


def git_env():
    return {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }


def git(repo, *args, allowed=(0,)):
    argv = ["git", "--no-optional-locks", "-C", str(repo), *args]
    result = subprocess.run(
        argv, capture_output=True, text=True, errors="replace", env=git_env()
    )
    if result.returncode not in allowed:
        raise CheckError(f"{argv!r}: exit {result.returncode}: {result.stderr.strip()}")
    return result


def require(condition, message):
    if not condition:
        raise CheckError(message)


def branch_ref(repo, name):
    require(
        bool(name) and not name.startswith("refs/"),
        "Use a local branch name, not a refs/ path",
    )
    ref = "refs/heads/" + name
    git(repo, "check-ref-format", ref)
    return ref


def commit(repo, revision):
    return git(
        repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}"
    ).stdout.strip()


def paths(repo):
    root = git(repo, "rev-parse", "--show-toplevel").stdout.strip()
    return {
        "worktree": str(Path(root).resolve()),
        "git_dir": git(
            repo, "rev-parse", "--path-format=absolute", "--git-dir"
        ).stdout.strip(),
        "common_dir": str(
            Path(
                git(
                    repo, "rev-parse", "--path-format=absolute", "--git-common-dir"
                ).stdout.strip()
            ).resolve()
        ),
    }


def status(repo, ignored=False):
    args = [
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--ignore-submodules=none",
    ]
    if ignored:
        args.append("--ignored")
    return git(repo, *args).stdout


def normal_index(repo):
    entries = git(repo, "ls-files", "-v", "-z").stdout.split("\0")
    abnormal = [entry for entry in entries if entry and not entry.startswith("H ")]
    require(
        not abnormal, f"Non-normal index entries (including hidden flags): {abnormal!r}"
    )


def operations(repo):
    found = []
    for name in (
        "MERGE_HEAD",
        "rebase-merge",
        "rebase-apply",
        "CHERRY_PICK_HEAD",
        "REVERT_HEAD",
        "sequencer",
        "BISECT_START",
    ):
        path = git(
            repo, "rev-parse", "--path-format=absolute", "--git-path", name
        ).stdout.strip()
        if Path(path).exists():
            found.append({"operation": name, "path": path})
    return found


def preflight(args, evidence):
    evidence["repo"] = paths(args.repo)
    worker = Path(args.worker_worktree).resolve(strict=True)
    evidence["worker"] = paths(worker)
    require(
        str(worker) == evidence["worker"]["worktree"],
        "Worker path must be the actual worktree root, not a subdirectory",
    )
    require(
        evidence["repo"]["common_dir"] == evidence["worker"]["common_dir"],
        "Worker belongs to a different repository",
    )
    registered = git(args.repo, "worktree", "list", "--porcelain", "-z").stdout.split(
        "\0"
    )
    roots = {
        str(Path(item[9:]).resolve())
        for item in registered
        if item.startswith("worktree ")
    }
    require(str(worker) in roots, "Worker is not a registered worktree")
    worker_ref = branch_ref(args.repo, args.worker_branch)
    base_ref = branch_ref(args.repo, args.base)
    require(worker_ref != base_ref, "Worker and base branches must be distinct")
    evidence.update(worker_ref=worker_ref, base_ref=base_ref)
    actual = git(worker, "symbolic-ref", "-q", "HEAD", allowed=(0, 1)).stdout.strip()
    evidence["actual_worker_ref"] = actual or None
    require(actual == worker_ref, "Worker HEAD is detached or on the wrong branch")
    evidence["worker_sha"] = commit(worker, "HEAD")
    evidence["base_sha"] = commit(args.repo, base_ref)
    require(
        evidence["worker_sha"] == commit(args.repo, worker_ref),
        "Worker ref and HEAD differ",
    )
    config = git(
        worker,
        "config",
        "--local",
        "--get-all",
        f"branch.{args.worker_branch}.workmux-base",
        allowed=(0, 1),
    ).stdout.splitlines()
    evidence["workmux_base_values"] = config
    require(
        config == [args.base],
        "Local workmux-base must have exactly one value equal to explicit base",
    )
    normal_index(worker)
    evidence["operations"] = operations(worker)
    evidence["status_porcelain"] = status(worker)
    require(not evidence["operations"], "Worker has an unfinished Git operation")
    require(not evidence["status_porcelain"], "Worker has tracked or untracked changes")


def parser():
    result = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Emits one JSON object; exit 0 means the observed preconditions passed, "
            "not authorization to merge. No refs, config, index, or worktree files are changed. "
            "Serialize Git operations: evidence is a snapshot, not a lock. Ignored files are allowed. Non-normal index entries (including assume-unchanged and skip-worktree) are rejected."
        ),
    )
    result.add_argument(
        "--repo", required=True, help="Existing repository checkout path"
    )
    result.add_argument(
        "--worker-worktree", required=True, help="Exact registered worker worktree root"
    )
    result.add_argument(
        "--worker-branch", required=True, help="Expected local worker branch name"
    )
    result.add_argument(
        "--base", required=True, help="Explicit local base branch name (no default)"
    )
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    evidence = {"ok": False}
    try:
        preflight(args, evidence)
        evidence["ok"] = True
    except (CheckError, OSError, ValueError) as exc:
        evidence["error"] = str(exc)
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
