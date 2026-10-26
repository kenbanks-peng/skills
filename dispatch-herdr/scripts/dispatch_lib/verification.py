"""Run required argv checks on a pinned local base in an isolated Git worktree."""

import json
import math
import os
import re
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .git import (
    CheckError,
    branch_ref,
    commit,
    git,
    git_env,
    normal_index,
    operations,
    paths,
    require,
    status,
)


def load_checks(files):
    checks = []
    for filename in files:
        with open(filename, encoding="utf-8") as stream:
            value = json.load(stream)
        require(
            isinstance(value, list) and bool(value),
            f"{filename}: expected a nonempty JSON array of argv arrays",
        )
        for argv in value:
            require(
                isinstance(argv, list)
                and bool(argv)
                and all(isinstance(arg, str) and "\0" not in arg for arg in argv)
                and bool(argv[0]),
                f"{filename}: invalid argv array: {argv!r}",
            )
            checks.append(argv)
    require(bool(checks), "At least one check is required")
    return checks


def validate_identity(checkout, pinned):
    require(commit(checkout, "HEAD") == pinned, "Checks changed checkout HEAD")
    require(
        git(checkout, "symbolic-ref", "-q", "HEAD", allowed=(0, 1)).returncode == 1,
        "Checks attached checkout HEAD to a branch",
    )
    normal_index(checkout)
    require(not operations(checkout), "Checkout has an unfinished Git operation")
    for args in (("diff", "--cached"), ("diff",)):
        result = git(
            checkout,
            "-c",
            "core.fsmonitor=false",
            *args,
            "--quiet",
            "--no-ext-diff",
            "--ignore-submodules=none",
            pinned,
            "--",
            allowed=(0, 1),
        )
        require(
            result.returncode == 0, "Tracked checkout content differs from pinned SHA"
        )


def stop_group(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    time.sleep(0.2)
    process.poll()
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_check(check, checkout, timeout):
    require(os.name == "posix", "Check execution requires POSIX process groups")
    limit = 4096
    logs = Path(paths(checkout)["common_dir"]) / "dispatch-checks"
    logs.mkdir(exist_ok=True)
    with (
        tempfile.NamedTemporaryFile(
            dir=logs, prefix="check-", suffix=".stdout", delete=False
        ) as stdout,
        tempfile.NamedTemporaryFile(
            dir=logs, prefix="check-", suffix=".stderr", delete=False
        ) as stderr,
    ):
        process = subprocess.Popen(
            check["argv"],
            cwd=checkout,
            env=git_env(),
            stdout=stdout,
            stderr=stderr,
            shell=False,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        timed_out = False
        try:
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
        finally:
            stop_group(process)
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired as exc:
                raise CheckError(
                    "Check process did not exit after SIGKILL; checkout retained"
                ) from exc
        check.update(
            returncode=process.returncode,
            status="timeout"
            if timed_out
            else ("passed" if process.returncode == 0 else "failed"),
        )
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            stream.flush()
            os.fsync(stream.fileno())
            check[name + "_path"] = stream.name
            check[name + "_bytes"] = os.fstat(stream.fileno()).st_size
            stream.seek(0)
            output = stream.read(limit + 1)
            check[name] = output[:limit].decode("utf-8", errors="replace")
            check[name + "_truncated"] = len(output) > limit
        require(
            not timed_out, f"Check timed out after {timeout} seconds: {check['argv']!r}"
        )


def verify(args, evidence):
    checks = load_checks(args.checks_file)
    evidence["checks"] = [{"argv": argv, "status": "not_run"} for argv in checks]
    evidence["repo"] = paths(args.repo)
    ref = branch_ref(args.repo, args.base)
    evidence["base_ref"] = ref
    pinned = commit(args.repo, ref)
    evidence["tested_sha"] = pinned
    require(
        re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", args.worker_commit)
        is not None,
        "--worker-commit must be a full commit SHA, not a moving ref",
    )
    worker = commit(args.repo, args.worker_commit)
    evidence["worker_sha"] = worker
    ancestor = git(
        args.repo, "merge-base", "--is-ancestor", worker, pinned, allowed=(0, 1)
    )
    evidence["worker_is_ancestor"] = ancestor.returncode == 0
    require(ancestor.returncode == 0, "Worker commit is not an ancestor of pinned base")
    parent = Path(tempfile.mkdtemp(prefix="dispatch-verify-"))
    checkout = parent / "checkout"
    evidence.update(
        temporary_directory=str(parent), worktree=str(checkout), cleanup="retained"
    )
    git(args.repo, "worktree", "add", "--detach", str(checkout), pinned)
    evidence["checkout"] = paths(checkout)
    require(
        commit(checkout, "HEAD") == pinned, "Temporary checkout is not at pinned SHA"
    )
    require(
        not status(checkout, ignored=True),
        "Temporary checkout is not clean before checks",
    )
    for check in evidence["checks"]:
        validate_identity(checkout, pinned)
        try:
            run_check(check, checkout, args.timeout)
        except OSError as exc:
            check.update(status="error", returncode=None, stdout="", stderr=str(exc))
            raise CheckError(f"Cannot execute check: {check['argv']!r}: {exc}") from exc
        require(check["status"] == "passed", f"Check failed: {check['argv']!r}")
    validate_identity(checkout, pinned)
    evidence["operations"] = operations(checkout)
    evidence["status_porcelain"] = status(checkout, ignored=True)
    require(not evidence["operations"], "Checks left an unfinished Git operation")
    require(
        not evidence["status_porcelain"],
        "Checks left tracked, untracked, or ignored files; checkout retained",
    )


def observe_base(args, evidence):
    if "tested_sha" not in evidence:
        return
    try:
        current = commit(args.repo, evidence["base_ref"])
        evidence["base_sha_after"] = current
        evidence["base_moved"] = current != evidence["tested_sha"]
        require(
            not evidence["base_moved"],
            "Base moved since pinning; verification is not safe for closure",
        )
    except (CheckError, OSError) as exc:
        evidence.setdefault("base_moved", None)
        evidence["ok"] = False
        evidence.setdefault("errors", []).append(str(exc))


def handle(args):
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise ValueError("--timeout must be finite and positive")
    evidence = {"ok": False, "checks": [], "cleanup": "not_created"}
    try:
        verify(args, evidence)
        evidence["ok"] = True
    except (CheckError, OSError, ValueError) as exc:
        evidence.setdefault("errors", []).append(str(exc))
    observe_base(args, evidence)
    if evidence["ok"]:
        try:
            git(args.repo, "worktree", "remove", evidence["worktree"])
            evidence["cleanup"] = "removed"
            Path(evidence["temporary_directory"]).rmdir()
        except (CheckError, OSError) as exc:
            evidence["ok"] = False
            evidence.setdefault("errors", []).append(str(exc))
        observe_base(args, evidence)
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["ok"] else 1
