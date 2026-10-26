"""Stop the exact recorded worker container and independently verify exit."""

import json
import time
from pathlib import Path

from .runtime import container_ids, emit, inspect, load_receipt, run, worker_path


def stop(receipt, execute=False, timeout=30, previous=None):
    result = {
        "ok": False,
        "executed": execute,
        "receipt": {
            key: receipt.get(key)
            for key in (
                "task_ref",
                "common_dir",
                "repo",
                "worktree",
                "worker_worktree",
                "handle",
                "runtime",
                "container",
                "record_path",
            )
        },
        "observations": [],
    }
    try:
        if receipt["runtime"] == "local" or not receipt.get("container"):
            raise ValueError(
                "Local/Lima workers require separate process-stop evidence"
            )
        identity = receipt["container"]["id"]
        runtime = receipt["runtime"]
        if runtime not in ("apple-container", "docker", "podman"):
            raise ValueError("Unsupported runtime")
        result.update(
            repo=receipt["repo"],
            worktree=receipt["worktree"],
            handle=receipt["handle"],
            container_id=identity,
        )

        stop_requested = False
        previous_matches = bool(
            previous
            and previous.get("ok") is True
            and previous.get("stopped") is True
            and previous.get("container_id") == identity
            and previous.get("repo") == receipt["repo"]
            and previous.get("worktree") == receipt["worktree"]
            and previous.get("handle") == receipt["handle"]
        )

        def observe():
            try:
                observation = inspect(runtime, identity)
            except ValueError:
                if not (stop_requested or previous_matches):
                    raise
                identities = container_ids(runtime)
                result["observations"].append({"listed_container_ids": identities})
                if identity in identities:
                    raise
                return "removed"
            result["observations"].append(observation)
            if observation["id"] != identity:
                raise ValueError("Container identity changed")
            if (
                worker_path(observation, receipt["worktree"])
                != receipt["worker_worktree"]
            ):
                raise ValueError("Worker mount changed")
            return observation["status"]

        status = observe()
        stopped = (
            ("stopped", "removed")
            if runtime == "apple-container"
            else ("exited", "removed")
        )
        if status in stopped:
            result.update(ok=True, stopped=True)
            return result
        if status != "running":
            raise ValueError(f"Unknown or unsafe container state: {status}")
        if not execute:
            result.update(ok=True, stopped=False, dry_run=True)
            return result
        binary = "container" if runtime == "apple-container" else runtime
        if observe() != "running":
            raise ValueError(
                "Container state changed before stop; inspect before retry"
            )
        run([binary, "stop", "--time", str(timeout), identity], timeout=timeout + 15)
        stop_requested = True
        deadline = time.monotonic() + timeout
        while True:
            status = observe()
            if status in stopped:
                result.update(ok=True, stopped=True)
                return result
            if status != "running" or time.monotonic() >= deadline:
                raise ValueError(f"Container exit not confirmed: {status}")
            time.sleep(min(0.25, max(0, deadline - time.monotonic())))
    except (ValueError, OSError, KeyError, TypeError) as error:
        result["error"] = str(error)
    return result


def handle(args):
    if args.timeout <= 0:
        raise ValueError("--timeout must be positive")
    try:
        previous = (
            json.loads(Path(args.previous).read_text()) if args.previous else None
        )
        result = stop(load_receipt(args.receipt), args.execute, args.timeout, previous)
    except (OSError, ValueError, KeyError) as error:
        result = {"ok": False, "error": str(error)}
    return emit(result)
