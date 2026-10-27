#!/usr/bin/env python3
"""Record a named linux launch, then launch it once on request."""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


def capture(argv, cwd=None):
    return subprocess.run(
        argv, cwd=cwd, text=True, capture_output=True, check=True
    ).stdout


def save(path, record):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(path)


def launch_argv(record, command):
    worktree = record["worktree"]
    common = record["common_git"]
    attempt = record["attempt"]
    argv = [
        "linux",
        "launch",
        "--name",
        record["id"],
        "-it",
        "-mount",
        f"{common}:{common}:rw",
    ]
    if not any(Path(attempt).is_relative_to(root) for root in (worktree, common)):
        argv += ["-mount", f"{attempt}:{attempt}:rw"]
    environment = {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": worktree,
    }
    for kind in ("AUTHOR", "COMMITTER"):
        ident = capture(["git", "var", f"GIT_{kind}_IDENT"], cwd=worktree).strip()
        match = re.fullmatch(r"(.*) <([^<>]+)> [0-9]+ [+-][0-9]{4}", ident)
        if not match or not match[1]:
            raise ValueError(f"Host Git {kind.lower()} identity is unavailable")
        environment[f"GIT_{kind}_NAME"] = match[1]
        environment[f"GIT_{kind}_EMAIL"] = match[2]
    for key, value in environment.items():
        argv += ["-env", f"{key}={value}"]
    return argv + ["--"] + command


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    attempt = args.attempt.resolve(strict=True)
    path = attempt / "container.json"
    if not shutil.which("linux"):
        raise ValueError("Required executable: linux")
    if args.launch:
        record = json.loads(path.read_text())
        if record["phase"] != "prepared" or record["attempt"] != str(attempt):
            raise ValueError(
                "Existing launch intent: reconcile it; do not repeat launch"
            )
        command = args.command
        if command[:1] == ["--"]:
            command = command[1:]
        if not command:
            command = [
                "pi",
                "--session",
                f"{attempt}/pi.jsonl",
                "--tui-mode",
                "regular",
                "--",
                f"@{attempt}/prompt.md",
            ]
        argv = launch_argv(record, command)
        record["phase"] = "launch-intent"
        save(path, record)
        # Do not save argv or capture terminal I/O.
        result = subprocess.run(argv, cwd=record["worktree"], check=False)
        record["phase"] = "exited"
        record["exit_code"] = result.returncode
        save(path, record)
        return result.returncode
    if not args.worktree:
        parser.error("--worktree is required when preparing a launch")
    worktree = args.worktree.resolve(strict=True)
    common = Path(
        capture(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=worktree,
        ).strip()
    ).resolve(strict=True)
    if attempt.is_relative_to(worktree) and not (
        attempt.is_relative_to(worktree / ".dispatch")
        or (attempt != common and attempt.is_relative_to(common))
    ):
        raise ValueError(
            "Attempt records must be outside source files, inside .dispatch, or inside common Git metadata"
        )
    for location in (worktree, common, attempt):
        if any(char in str(location) for char in ":,\n"):
            raise ValueError("Mount paths cannot contain colon, comma, or newline")
    record = {
        "id": "dispatch-" + uuid.uuid4().hex,
        "worktree": str(worktree),
        "common_git": str(common),
        "attempt": str(attempt),
        "phase": "prepared",
    }
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(path)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        if isinstance(error, subprocess.CalledProcessError):
            print(
                f"Command failed (exit {error.returncode}); reconcile saved state",
                file=sys.stderr,
            )
        else:
            print(str(error), file=sys.stderr)
        sys.exit(1)
