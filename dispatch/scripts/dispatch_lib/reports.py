"""Compatibility troubleshooting and latest dispatch report output."""

import hashlib
import json
import re
import shutil
from pathlib import Path

from .git import CheckError, commit, paths, require
from .runtime import emit, run

COMMANDS = {
    "workmux": {
        "add": ("--config", "--prompt-file", "--name", "--base"),
        "open": ("--continue", "--prompt-file", "--config"),
        "list": ("--json",),
        "status": ("--json",),
        "wait": ("--timeout", "--status", "--any"),
    },
    "aven": {"show": ("--json", "--full"), "context": ("--json",)},
}


def discover(cache, refresh=False):
    fingerprints = {}
    for binary in COMMANDS:
        executable = shutil.which(binary)
        if not executable:
            raise ValueError(f"Required CLI is unavailable: {binary}")
        path = Path(executable).resolve()
        stat = path.stat()
        fingerprints[binary] = [str(path), stat.st_size, stat.st_mtime_ns]
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text())
        if data.get("fingerprints") == fingerprints and data.get("schema_version") == 1:
            return data
    data = {"schema_version": 1, "ok": True, "fingerprints": fingerprints, "tools": {}}
    for binary, commands in COMMANDS.items():
        item = {"version": run([binary, "--version"]).strip(), "commands": {}}
        for command, flags in commands.items():
            help_text = run([binary, command, "--help"])
            available = set(re.findall(r"--[a-z][a-z-]*", help_text))
            item["commands"][command] = {flag: flag in available for flag in flags}
        data["tools"][binary] = item
        for command, flags in item["commands"].items():
            for flag, available in flags.items():
                if not available:
                    data["ok"] = False
                    data.setdefault("errors", []).append(
                        f"{binary} {command}: required flag {flag} is unavailable"
                    )
    cache.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache.with_suffix(cache.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(cache)
    return data


def latest_report(data, kind, after=None):
    notes = data.get("notes")
    if not isinstance(notes, list):
        raise TypeError("Expected aven show --full --json with a notes array")
    selected = []
    for note in notes:
        body = note["body"]
        if not isinstance(body, str) or not isinstance(note["created_at"], str):
            raise TypeError("Invalid note schema")
        if not body.startswith(kind + ":"):
            continue
        if after and note["created_at"] <= after:
            continue
        selected.append(note)
    if not selected:
        raise ValueError("No matching report; inspect worker state or use recovery")
    selected.sort(key=lambda n: (n["created_at"], n["id"]))
    return {"ok": True, "kind": kind, "note": selected[-1]}


def worker_result(data, record, sha):
    """Select newest RESULT, then bind it to this launch and reviewed Git commit."""
    require(data["task"]["ref"] == record["task_ref"], "Result task identity mismatch")
    note = latest_report(data, "RESULT")["note"]
    prior = set(record["prior_note_ids"])
    require(note["id"] not in prior, "RESULT predates the current worker attempt")
    tokens = re.findall(r"(?<![A-Za-z0-9])[0-9a-f]{4,64}(?![A-Za-z0-9])", note["body"])
    for token in tokens:
        if not sha.startswith(token):
            continue
        try:
            if commit(record["repo"], token) == sha:
                return note
        except CheckError:
            # An ambiguous abbreviation is not evidence; another token may be full.
            continue
    raise ValueError("RESULT lacks matching current worker commit evidence")


def handle(args):
    try:
        if args.command == "discover":
            result = discover(args.cache, args.refresh)
        else:
            if args.input:
                text = args.input.read_text()
            else:
                argv = ["aven", "show", args.task, "--full", "--json"]

                text = run(argv)
            data = json.loads(text)
            task = data.get("task", {})
            if task.get("ref") != args.task:
                raise ValueError(
                    "Report snapshot must match the exact full task reference"
                )
            # Retain the complete source once, not in every selected report.
            common = Path(paths(Path.cwd())["common_dir"])
            directory = common / "dispatch-reports"
            directory.mkdir(exist_ok=True)
            source = directory / (hashlib.sha256(text.encode()).hexdigest() + ".json")
            if not source.exists():
                with source.open("x") as output:
                    output.write(text)
            if args.save:
                with args.save.open("x") as output:
                    output.write(text)
            result = latest_report(data, args.kind, args.after)
            result["source_path"] = str(source)
            if args.kind == "RESULT":
                common = Path(paths(Path.cwd())["common_dir"])
                record = json.loads(
                    (
                        common / "dispatch-workers" / args.task / "worker.json"
                    ).read_text()
                )
                sha = commit(record["worktree"], "HEAD")
                result["note"] = worker_result(data, record, sha)
                result.update(
                    worker_commit=sha,
                    record_path=str(
                        common / "dispatch-workers" / args.task / "worker.json"
                    ),
                )
    except (ValueError, OSError, KeyError, TypeError, CheckError) as error:
        result = {"ok": False, "error": str(error)}
    return emit(result)
