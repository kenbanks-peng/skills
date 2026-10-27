#!/usr/bin/env python3
"""Check a recorded container's identity before state, stop, or delete."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def capture(argv):
    return subprocess.run(argv, text=True, capture_output=True, check=True).stdout


def owned_state(record):
    if record["phase"] not in {"launch-intent", "exited"}:
        raise ValueError("No saved launch intent")
    entries = json.loads(capture(["linux", "inspect", record["id"]]))
    if not isinstance(entries, list) or len(entries) != 1:
        raise ValueError("Expected exactly one container")
    entry = entries[0]
    config = entry["configuration"]
    mounts = config["mounts"]
    expected = {record["worktree"], record["common_git"]}
    if not any(Path(record["attempt"]).is_relative_to(root) for root in expected):
        expected.add(record["attempt"])
    if (
        config["id"] != record["id"]
        or config["initProcess"]["workingDirectory"] != record["worktree"]
        or any(
            not any(
                mount.get("source") == path and mount.get("destination") == path
                for mount in mounts
            )
            for path in expected
        )
    ):
        raise ValueError("Container identity or mount mismatch")
    return entry["status"]["state"]


def load_record(attempt):
    attempt = attempt.resolve(strict=True)
    record = json.loads((attempt / "container.json").read_text())
    if record["attempt"] != str(attempt):
        raise ValueError("Receipt attempt path mismatch")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("action", choices=("state", "stop", "delete"))
    args = parser.parse_args()
    record = load_record(args.attempt)
    state = owned_state(record)
    if args.action == "state":
        print(state)
        return
    if args.action == "stop":
        if state == "running":
            subprocess.run(
                ["linux", "stop", "--time", "10", record["id"]],
                check=True,
                stdout=subprocess.DEVNULL,
            )
        elif state != "stopped":
            raise ValueError(f"Cannot stop container in state: {state}")
        if owned_state(record) != "stopped":
            raise ValueError("Container did not stop")
        return
    if state != "stopped":
        raise ValueError("Refusing to delete a container that is not stopped")
    subprocess.run(
        ["linux", "delete", record["id"]], check=True, stdout=subprocess.DEVNULL
    )
    entries = json.loads(capture(["linux", "list", "--all", "--format", "json"]))
    if not isinstance(entries, list) or any(
        entry["id"] == record["id"] for entry in entries
    ):
        raise ValueError("Container absence not confirmed")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError):
        # Never print inspect output or subprocess argv: they may contain secrets.
        print(
            "Container operation failed; retain receipt and reconcile live state",
            file=sys.stderr,
        )
        sys.exit(1)
