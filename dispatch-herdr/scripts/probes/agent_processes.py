#!/usr/bin/env python3
"""Read live Linux pi process identity inside the exact worker container."""

import json
import sys
from pathlib import Path


def is_pi(argv, executable):
    # pi sets its Node process title to `pi`, replacing its original argv.
    if Path(executable).name not in ("node", "nodejs", "pi") or not argv:
        return False
    if Path(argv[0]).name == "pi":
        return True
    return (
        Path(argv[0]).name in ("node", "nodejs")
        and len(argv) > 1
        and any(
            argv[1].endswith(package + "/pi-coding-agent/dist/cli.js")
            for package in ("@earendil-works", "@mariozechner")
        )
    )


def observe(worktree, proc=Path("/proc")):
    found = []
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            cwd = str((path / "cwd").readlink())
            if cwd != worktree:
                continue
            executable = str((path / "exe").readlink())
            argv = [
                arg
                for arg in (path / "cmdline").read_bytes().decode().split("\0")
                if arg
            ]
            if not is_pi(argv, executable):
                continue
            # Field 22 is starttime; split after comm, which may contain spaces.
            stat = (path / "stat").read_text().rsplit(")", 1)[1].split()
            if stat[0] == "Z":
                continue
            found.append(
                {
                    "pid": int(path.name),
                    "start_ticks": stat[19],
                    "exe": executable,
                    "argv": argv[:1] if Path(argv[0]).name == "pi" else argv[:2],
                    "cwd": cwd,
                    "kind": "pi",
                }
            )
        except FileNotFoundError:
            # A process that exited during observation is not startup proof.
            continue
    return found


if __name__ == "__main__":
    print(json.dumps(observe(sys.argv[1])))
