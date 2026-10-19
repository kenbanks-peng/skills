#!/usr/bin/env python3
"""Shared bounded CLI calls and container observations for dispatch helpers."""

import json
import subprocess
from pathlib import Path


def run(argv, cwd=None, timeout=30):
    try:
        result = subprocess.run(
            argv, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError(f"{argv!r}: timed out after {timeout}s") from error
    if result.returncode:
        raise ValueError(f"{argv!r}: exit {result.returncode}: {result.stderr.strip()}")
    return result.stdout


def canonical(value):
    path = Path(value)
    if not path.is_absolute() or path != path.resolve(strict=True):
        raise ValueError(f"Expected an absolute canonical path: {value}")
    return path


def inspect(runtime, identity):
    if not identity or identity.startswith("-"):
        raise ValueError("Expected an exact container identity")
    binary = "container" if runtime == "apple-container" else runtime
    data = json.loads(run([binary, "inspect", identity]))
    if not isinstance(data, list) or len(data) != 1:
        raise ValueError("Container inspect must return exactly one object")
    return normalize(runtime, data[0])


def normalize(runtime, data):
    if runtime == "apple-container":
        config = data["configuration"]
        identity = config["id"]
        status = data["status"]
        if isinstance(status, dict):
            status = status.get("state")
        if not isinstance(status, str) or not status.strip():
            raise ValueError("Expected a non-empty Apple container status.state string")
        status = status.lower()
        mounts = [
            {"source": m["source"], "destination": m["destination"]}
            for m in config["mounts"]
        ]
        working_directory = config.get("initProcess", {}).get("workingDirectory")
    else:
        identity = data["Id"]
        status = data["State"]["Status"].lower()
        mounts = [
            {"source": m["Source"], "destination": m["Destination"]}
            for m in data["Mounts"]
            if m.get("Type") == "bind"
        ]
        working_directory = data.get("Config", {}).get("WorkingDir")
    if not isinstance(identity, str) or not identity:
        raise ValueError("Missing container identity")
    return {
        "id": identity,
        "status": status,
        "mounts": mounts,
        "working_directory": working_directory,
    }


def container_ids(runtime):
    binary = "container" if runtime == "apple-container" else runtime
    if runtime == "apple-container":
        data = json.loads(run([binary, "list", "--all", "--format", "json"]))
        if not isinstance(data, list):
            raise ValueError("Expected a container list")
        return [item["configuration"]["id"] for item in data]
    return run([binary, "ps", "-aq", "--no-trunc"]).split()


def containers(runtime):
    return [inspect(runtime, identity) for identity in container_ids(runtime)]


def worker_path(observation, worktree):
    matches = [
        m["destination"] for m in observation["mounts"] if m["source"] == str(worktree)
    ]
    if len(matches) != 1 or not Path(matches[0]).is_absolute():
        raise ValueError("Container does not have one exact worktree bind mount")
    return matches[0]


def load_receipt(path):
    data = json.loads(Path(path).read_text())
    if data.get("schema_version") != 1 or data.get("ok") is not True:
        raise ValueError("A successful version 1 launch receipt is required")
    canonical(data["repo"])
    canonical(data["worktree"])
    return data


def emit(result):
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1
