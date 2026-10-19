#!/usr/bin/env python3
"""Launch one Workmux worker and emit host/guest paths and exact UI/container IDs."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from worker_runtime import canonical, containers, emit, load_receipt, run, worker_path


def observe(args, result):
    rows = json.loads(run(["workmux", "list", "--json", args.handle], args.repo))
    matches = [r for r in rows if r["handle"] == args.handle and not r["is_main"]]
    if len(matches) != 1:
        raise ValueError("Expected one non-primary Workmux worktree")
    row = matches[0]
    worktree = canonical(row["path"])
    if row["branch"] != args.branch:
        raise ValueError("Observed worker branch does not match launch")
    result.update(worktree=str(worktree), branch=row["branch"])
    status = json.loads(run(["workmux", "status", "--json", args.handle], args.repo))
    result["ui"] = {
        "context": status["context"],
        "agents": [
            {
                k: a.get(k)
                for k in ("pane_id", "session", "window_name", "agent_kind", "workdir")
            }
            for a in status["agents"]
            if a["worktree"] == args.handle and a["project_path"] == args.repo
        ],
    }
    if status.get("target_errors") or not result["ui"]["agents"]:
        raise ValueError("Worker UI identity is unavailable")
    if any(not a["pane_id"] for a in result["ui"]["agents"]):
        raise ValueError("Worker pane ID is unavailable")
    if args.runtime == "local":
        result["worker_worktree"] = str(worktree)
        result["container"] = None
    else:
        matches = []
        for container in containers(args.runtime):
            if container["status"] == "running":
                try:
                    guest = worker_path(container, worktree)
                except ValueError:
                    continue
                matches.append((container, guest))
        if len(matches) != 1:
            raise ValueError(
                "Expected one running container with the exact worker mount"
            )
        container, guest = matches[0]
        result["container"] = container
        result["worker_worktree"] = guest
    result["prompts"] = []
    directory = worktree / ".workmux"
    if directory.is_symlink():
        raise ValueError("Generated prompt directory is a symlink")
    for path in sorted(directory.glob("PROMPT-*.md")):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Invalid generated prompt: {path}")
        result["prompts"].append(
            {
                "path": str(path.relative_to(worktree)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )


def launch(args):
    result = {
        "schema_version": 1,
        "ok": False,
        "repo": args.repo,
        "handle": args.handle,
        "runtime": args.runtime,
        "config": args.config,
        "base": args.base,
    }
    try:
        canonical(args.repo)
        args.config = str(Path(args.config).expanduser().resolve(strict=True))
        result["config"] = args.config
        canonical(args.prompt)
        if not args.handle or args.handle.startswith("-") or ":" in args.handle:
            raise ValueError("Use a local, explicit worker handle without ':'")
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", args.launch_base):
            raise ValueError(
                "--launch-base must be the full SHA used in the worker prompt"
            )
        if args.observe_only:
            if not args.previous:
                raise ValueError("--observe-only requires --previous launch receipt")
            previous = load_receipt(args.previous)
            if any(
                previous[key] != result[key]
                for key in ("repo", "handle", "runtime", "base")
            ):
                raise ValueError("Previous launch identity mismatch")
            if previous["branch"] != args.branch:
                raise ValueError("Previous branch mismatch")
            if previous["launch_base"] != args.launch_base:
                raise ValueError("Original launch SHA mismatch")
            result["launch_base"] = previous["launch_base"]
            observe(args, result)
            run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    result["launch_base"],
                    f"refs/heads/{args.branch}",
                ],
                args.repo,
            )
            result["ok"] = True
            return result
        result["launch_base"] = run(
            ["git", "rev-parse", "--verify", f"refs/heads/{args.base}^{{commit}}"],
            args.repo,
        ).strip()
        if result["launch_base"] != args.launch_base:
            raise ValueError(
                "Base moved since prompt generation; regenerate and review the prompt"
            )
        argv = [
            "workmux",
            "add",
            args.branch,
            "--base",
            args.base,
            "--name",
            args.handle,
            "-b",
            "-P",
            args.prompt,
            "--config",
            args.config,
        ]
        if args.parent_session:
            argv.extend(["--parent-session", args.parent_session])
        # Preserve launch output in the receipt, never mix it into JSON stdout.
        try:
            result["launch_output"] = run(argv, args.repo, timeout=args.timeout)
        except ValueError as error:
            result["launch_error"] = str(error)
            try:
                observe(args, result)
            except (ValueError, OSError, KeyError, TypeError) as observation_error:
                result["observation_error"] = str(observation_error)
            raise
        startup_error = None
        try:
            run(
                [
                    "workmux",
                    "wait",
                    args.handle,
                    "--status",
                    "working",
                    "--timeout",
                    str(args.timeout),
                ],
                args.repo,
                timeout=args.timeout + 15,
            )
        except ValueError as error:
            startup_error = str(error)
        observe(args, result)
        run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                result["launch_base"],
                f"refs/heads/{args.branch}",
            ],
            args.repo,
        )
        if startup_error:
            raise ValueError(
                "Startup unconfirmed; retained observations: " + startup_error
            )
        result["ok"] = True
    except (ValueError, OSError, KeyError, TypeError) as error:
        result["error"] = str(error)
    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Run in the original multiplexer. Read the prompt before launch. Persist stdout "
            "outside the worktree even on failure; reconcile partial resources before retry. "
            "Use CLI discovery once per run. This adapter does not change Aven."
        ),
    )
    for field in (
        "repo",
        "branch",
        "base",
        "handle",
        "config",
        "prompt",
        "launch-base",
    ):
        parser.add_argument("--" + field, required=True)
    parser.add_argument(
        "--runtime",
        required=True,
        choices=("apple-container", "docker", "podman", "local"),
    )
    parser.add_argument("--parent-session")
    parser.add_argument(
        "--observe-only",
        action="store_true",
        help="Refresh paths, IDs, and prompt hashes without launching",
    )
    parser.add_argument(
        "--previous", help="Original successful receipt for --observe-only"
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return emit(launch(args))


if __name__ == "__main__":
    raise SystemExit(main())
