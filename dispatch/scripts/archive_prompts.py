#!/usr/bin/env python3
"""Archive receipt-listed generated prompts before strict worktree cleanup."""

import argparse
import hashlib
import json
import os
from pathlib import Path

from git_preflight import git
from worker_runtime import canonical, emit, load_receipt, run


def archive(receipt, stop, destination, execute=False):
    result = {"ok": False, "executed": execute, "files": []}
    try:
        worker = canonical(receipt["worktree"])
        destination = Path(destination)
        if not destination.is_absolute() or destination != destination.resolve():
            raise ValueError("Archive path must be absolute and contain no symlinks")
        if destination == worker or worker in destination.parents:
            raise ValueError("Archive must be outside the worker worktree")
        if not (
            stop.get("ok") is True
            and stop.get("stopped") is True
            and stop.get("worktree") == str(worker)
            and stop.get("repo") == receipt["repo"]
            and stop.get("handle") == receipt["handle"]
            and stop.get("container_id") == (receipt.get("container") or {}).get("id")
        ):
            raise ValueError("Matching confirmed worker-stop evidence is required")
        result.update(worktree=str(worker), archive=str(destination))
        directory = worker / ".workmux"
        if directory.is_symlink():
            raise ValueError("Prompt directory is a symlink")
        entries = receipt["prompts"]
        paths = [entry["path"] for entry in entries]
        if len(set(paths)) != len(paths):
            raise ValueError("Duplicate prompt paths")
        for entry in entries:
            relative = Path(entry["path"])
            if (
                relative.parent != Path(".workmux")
                or not relative.name.startswith("PROMPT-")
                or relative.suffix != ".md"
            ):
                raise ValueError(
                    "Only direct .workmux/PROMPT-*.md files may be archived"
                )
            source = worker / relative
            target = destination / relative.name
            if source.is_symlink() or not source.is_file():
                raise ValueError(f"Missing or unsafe prompt: {source}")
            tracked = run(["git", "ls-files", "--", str(relative)], worker).strip()
            if tracked:
                raise ValueError(f"Tracked prompt must be retained: {source}")
            ignored = git(
                worker, "check-ignore", "-q", "--", str(relative), allowed=(0, 1)
            )
            if ignored.returncode == 0:
                raise ValueError(f"Ignored prompt must be retained: {source}")
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"Prompt changed since receipt: {source}")
            result["files"].append(
                {
                    "source": str(source),
                    "archive": str(target),
                    "sha256": entry["sha256"],
                }
            )
        if not execute:
            result.update(ok=True, dry_run=True)
            return result
        destination.mkdir(parents=True, exist_ok=True)
        for entry in result["files"]:
            source, target = Path(entry["source"]), Path(entry["archive"])
            data = source.read_bytes()
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError("Prompt changed before archival")
            if target.is_symlink():
                raise ValueError("Archive target is a symlink")
            if target.exists():
                if target.read_bytes() != data:
                    raise ValueError("Archive target contains different evidence")
            else:
                with target.open("xb") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
            if target.read_bytes() != data or source.read_bytes() != data:
                raise ValueError("Archive verification failed; source retained")
        for entry in result["files"]:
            source = Path(entry["source"])
            if (
                source.is_symlink()
                or hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]
            ):
                raise ValueError("Prompt changed before removal")
            source.unlink()
        if directory.exists() and not any(directory.iterdir()):
            directory.rmdir()
        result["ok"] = True
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["error"] = str(error)
    return result


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Dry-run by default. Requires matching stop evidence. Unknown .workmux files "
            "remain in place and still block cleanup. Keep stdout with run evidence. "
            "After partial removal, reconcile recorded actions before retrying."
        ),
    )
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--stop-evidence", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    try:
        result = archive(
            load_receipt(args.receipt),
            json.loads(Path(args.stop_evidence).read_text()),
            args.archive,
            args.execute,
        )
    except (OSError, ValueError, KeyError) as error:
        result = {"ok": False, "error": str(error)}
    return emit(result)


if __name__ == "__main__":
    raise SystemExit(main())
