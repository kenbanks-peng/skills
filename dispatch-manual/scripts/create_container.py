#!/usr/bin/env python3
"""Create, but do not start, one recorded Apple container from linux config."""

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


def create_argv(resolved, identity, label):
    """Accept only the linux container argv contract used by this skill."""
    if (
        not isinstance(resolved, list)
        or not all(isinstance(word, str) for word in resolved)
        or len(resolved) < 6
        or resolved[:2] != ["container", "run"]
        or resolved[-2:] != ["sleep", "infinity"]
    ):
        raise ValueError(
            "Expected linux to resolve Apple container run ... sleep infinity"
        )
    options = resolved[2:-3]
    result = [
        "container",
        "create",
        "--name",
        identity,
        "--label",
        f"dispatch.owner={label}",
    ]
    value_options = {
        "--memory",
        "--cpus",
        "--user",
        "--mount",
        "--workdir",
        "--env",
        "--tmpfs",
    }
    names = 0
    index = 0
    while index < len(options):
        option = options[index]
        if option in {"--rm", "-it", "-i", "-t"}:
            index += 1
            continue
        if option not in value_options | {"--name"} or index + 1 >= len(options):
            raise ValueError(f"Unsupported linux option: {option}")
        value = options[index + 1]
        if option == "--name":
            names += 1
        else:
            result.extend([option, value])
        index += 2
    if names != 1:
        raise ValueError("Expected exactly one generated linux container name")
    return result + resolved[-3:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worktree", required=True, type=Path)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--memory", help="Explicit linux memory override, such as 1G")
    args = parser.parse_args()
    worktree = args.worktree.resolve(strict=True)
    attempt = args.attempt.resolve(strict=True)
    common = Path(
        capture(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=worktree,
        ).strip()
    ).resolve(strict=True)
    if (attempt == worktree or worktree in attempt.parents) and not (
        attempt != common and common in attempt.parents
    ):
        raise ValueError(
            "Attempt records must be outside source files or inside common Git metadata"
        )
    for path in (worktree, common, attempt):
        if any(char in str(path) for char in ":,\n"):
            raise ValueError("Mount paths cannot contain colon, comma, or newline")
    intent_path = attempt / "container.json"
    if intent_path.exists():
        raise ValueError(
            "Existing container intent: reconcile it; do not repeat create"
        )
    linux = shutil.which("linux")
    runtime = shutil.which("container")
    if not linux or not runtime:
        raise ValueError("Required executables: linux and Apple container")
    command = [linux, "container", "-dry-run", "-mount", f"{common}:{common}:rw"]
    if attempt != common and common not in attempt.parents:
        command += ["-mount", f"{attempt}:{attempt}:rw"]
    if args.memory:
        command += ["-memory", args.memory]
    # Apple virtiofs ownership can differ from the host UID. Trust only this
    # checkout in this container's process environment, never a global wildcard.
    environment = {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": str(worktree),
    }
    for kind in ("AUTHOR", "COMMITTER"):
        ident = capture(["git", "var", f"GIT_{kind}_IDENT"], cwd=worktree).strip()
        match = re.fullmatch(r"(.*) <([^<>]+)> [0-9]+ [+-][0-9]{4}", ident)
        if not match or not match[1]:
            raise ValueError(f"Host Git {kind.lower()} identity is unavailable")
        environment[f"GIT_{kind}_NAME"] = match[1]
        environment[f"GIT_{kind}_EMAIL"] = match[2]
    for key, value in environment.items():
        command += ["-env", f"{key}={value}"]
    command += ["--", "sleep", "infinity"]
    resolved = json.loads(capture(command, cwd=worktree))
    identity = "dispatch-" + uuid.uuid4().hex
    owner = uuid.uuid4().hex
    argv = create_argv(resolved, identity, owner)
    argv[0] = runtime
    mounts = [argv[i + 1] for i, word in enumerate(argv[:-3]) if word == "--mount"]
    expected_mount = f"type=bind,source={worktree},target={worktree}"
    if expected_mount not in mounts:
        raise ValueError("linux did not mount the worktree at the same absolute path")
    if argv.count("--workdir") != 1 or argv[argv.index("--workdir") + 1] != str(
        worktree
    ):
        raise ValueError("linux did not select the expected workdir")
    record = {
        "id": identity,
        "owner": owner,
        "runtime": runtime,
        "worktree": str(worktree),
        "common_git": str(common),
        "attempt": str(attempt),
        "image": argv[-3],
        "phase": "create-intent",
    }
    # Exclusive creation prevents an uncertain launch from being repeated.
    fd = os.open(intent_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    # Do not save the resolved argv: environment values can contain credentials.
    subprocess.run(argv, cwd=worktree, check=True, stdout=subprocess.DEVNULL)
    record["phase"] = "created"
    temporary = intent_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record, indent=2) + "\n")
    temporary.chmod(0o600)
    temporary.replace(intent_path)
    print(intent_path)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        # CalledProcessError's string includes argv, which can contain credentials.
        if isinstance(error, subprocess.CalledProcessError):
            print(
                f"Command failed (exit {error.returncode}); retain intent and reconcile",
                file=sys.stderr,
            )
        else:
            print(str(error), file=sys.stderr)
        sys.exit(1)
