#!/usr/bin/env python3
"""Read-only recovery evidence. No task or multiplexer mutations."""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

LIMIT = 65536
TERMINATE_GRACE = 0.25
REAP_TIMEOUT = 1.0
OPERATIONS = (
    "MERGE_HEAD",
    "REBASE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "BISECT_START",
    "rebase-apply",
    "rebase-merge",
    "sequencer",
    "index.lock",
    "HEAD.lock",
    "packed-refs.lock",
    "shallow.lock",
)


def terminate_group(proc):
    """Escalate even if the leader exits: descendants can still hold the group."""
    errors = []
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            break
        except OSError as exc:
            errors.append(f"killpg({sig.name}): {exc}")
        if sig == signal.SIGTERM:
            time.sleep(TERMINATE_GRACE)
    try:
        proc.wait(timeout=REAP_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"reap: {exc}")
    return errors


def command(argv, cwd, timeout=10):
    """Bound runtime and returned output; preserve failures and truncation."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", LC_ALL="C")
    result = {"argv": argv, "cwd": str(cwd), "ok": False}
    if os.name != "posix":
        result["error"] = "POSIX process-group isolation is required"
        return result
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        try:
            proc = subprocess.Popen(
                argv,
                cwd=cwd,
                env=env,
                stdout=out,
                stderr=err,
                start_new_session=True,
                stdin=subprocess.DEVNULL,
            )
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                result["error"] = str(exc)
                result["timed_out"] = True
                errors = terminate_group(proc)
                if errors:
                    result["termination_errors"] = errors
            result["returncode"] = proc.returncode
        except OSError as exc:
            result["error"] = str(exc)
        for name, stream in (("stdout", out), ("stderr", err)):
            stream.seek(0)
            data = stream.read(LIMIT + 1)
            result[name] = data[:LIMIT].decode("utf-8", errors="replace")
            if len(data) > LIMIT:
                result["truncated"] = True
        result["ok"] = (
            result.get("returncode") == 0
            and not result.get("truncated")
            and "error" not in result
        )
    return result


def git(repo, *args, timeout=10):
    return command(["git", "--no-pager", *args], repo, timeout)


def require(result):
    if not result["ok"]:
        raise ValueError(json.dumps(result, ensure_ascii=True))
    return result["stdout"].strip()


def worktrees(repo):
    result = git(repo, "worktree", "list", "--porcelain", "-z")
    records = []
    if result["ok"]:
        record = {}
        for field in result["stdout"].split("\0"):
            if not field:
                if record:
                    records.append(record)
                    record = {}
            else:
                key, _, value = field.partition(" ")
                record[key] = value
        if record:
            records.append(record)
    return result, records


def state(repo):
    result = {}
    for name, args in {
        "head": ("rev-parse", "--verify", "HEAD"),
        "branch": ("symbolic-ref", "-q", "HEAD"),
        "git_dir": ("rev-parse", "--absolute-git-dir"),
        "common_dir": ("rev-parse", "--path-format=absolute", "--git-common-dir"),
        "status": (
            "status",
            "--porcelain=v1",
            "-z",
            "--untracked-files=all",
            "--ignored",
        ),
    }.items():
        result[name] = git(repo, *args)
    # Detached HEAD is an observation, not a failed snapshot.
    if result["branch"].get("returncode") == 1 and not result["branch"].get("error"):
        result["branch"]["ok"] = True
        result["branch"]["detached"] = True
    result["operations"] = []
    try:
        for key in ("git_dir", "common_dir"):
            directory = Path(require(result[key]))
            for marker in OPERATIONS:
                if os.path.lexists(directory / marker):
                    result["operations"].append(str(directory / marker))
            result["operations"].extend(
                str(p) for p in directory.glob("refs/**/*.lock")
            )
    except (ValueError, OSError) as exc:
        result["operation_error"] = str(exc)
    result["operations"] = sorted(set(result["operations"]))
    result["ok"] = all(
        result[k]["ok"] for k in ("head", "branch", "git_dir", "common_dir", "status")
    )
    result["ok"] = result["ok"] and "operation_error" not in result
    return result


def snapshot(repo, handles=(), timeout=10):
    repo = Path(repo).absolute()
    evidence = {
        "repo": str(repo),
        "read_only": True,
        "note": "Point-in-time observations, not an atomic snapshot or verification authorization.",
    }
    evidence["refs"] = git(repo, "for-each-ref", "--format=%(refname) %(objectname)")
    evidence["repository"] = state(repo)
    listing, records = worktrees(repo)
    evidence["worktree_list"] = listing
    evidence["worktrees"] = [
        dict(record, state=state(record["worktree"]))
        for record in records
        if "worktree" in record
    ]
    wm = {"available": shutil.which("workmux") is not None, "commands": []}
    evidence["workmux"] = wm
    if wm["available"]:
        for subcommand, positional in (("list", "FILTER"), ("status", "WORKTREES")):
            help_result = command(["workmux", subcommand, "--help"], repo, timeout)
            wm["commands"].append(help_result)
            if not help_result["ok"]:
                continue
            help_text = help_result["stdout"] + help_result["stderr"]
            usage = re.search(r"^Usage:.*$", help_text, re.MULTILINE)
            if not usage or f"workmux {subcommand}" not in usage.group():
                wm["commands"].append(
                    {"ok": False, "error": "Unrecognized installed CLI usage"}
                )
                continue
            if handles and f"[{positional}]..." not in usage.group():
                wm["commands"].append(
                    {
                        "ok": False,
                        "error": "Installed help does not establish handle syntax",
                    }
                )
                continue
            argv = ["workmux", subcommand]
            if re.search(r"^\s+--json\b", help_text, re.MULTILINE):
                argv.append("--json")
            argv.extend(handles)
            wm["commands"].append(command(argv, repo, timeout))
    else:
        wm["note"] = "Workmux unavailable; multiplexer evidence not collected."
    evidence["ok"] = (
        evidence["refs"]["ok"]
        and evidence["repository"]["ok"]
        and listing["ok"]
        and all(w["state"]["ok"] for w in evidence["worktrees"])
        and all(c["ok"] for c in wm["commands"])
    )
    evidence["complete"] = evidence["ok"] and wm["available"]
    return evidence


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "JSON on stdout. Exit 1 for failed/truncated observations; missing optional Workmux "
            "is marked incomplete. Git status includes ignored files. No Aven calls. "
            "POSIX required: each command runs in a dedicated session/process group. "
            "Timeout sends group SIGTERM, then SIGKILL after 0.25 seconds, with at most "
            "1 second to reap the leader. Signal/reap errors are retained. Returned output "
            "is capped at 64 KiB per stream; temporary capture files are not size-capped. "
            "Descendants that deliberately leave the process group are not contained."
        ),
    )
    parser.add_argument("--repo", required=True, help="Explicit repository directory")
    parser.add_argument(
        "--handle",
        action="append",
        default=[],
        help="Optional exact Workmux handle; repeatable",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="Seconds per Workmux command (default: 10)",
    )
    args = parser.parse_args()
    if not 0 < args.timeout <= 120 or any(
        not h or h.startswith("-") for h in args.handle
    ):
        parser.error(
            "timeout must be in (0, 120]; handles must be nonempty and not options"
        )
    result = snapshot(args.repo, args.handle, args.timeout)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
