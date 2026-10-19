#!/usr/bin/env python3
"""Compact CLI capability discovery and latest dispatch report output."""

import argparse
import json
import re
import shutil
from pathlib import Path

from worker_runtime import emit, run

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
        if not all(all(flags.values()) for flags in item["commands"].values()):
            data["ok"] = False
    cache.parent.mkdir(parents=True, exist_ok=True)
    # The cache is run-local evidence, not a repository configuration file.
    temporary = cache.with_suffix(cache.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(cache)
    return data


def latest_report(data, kind, authorization=None, after=None):
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
        if authorization and not re.search(
            r"(?<![A-Za-z0-9_-])" + re.escape(authorization) + r"(?![A-Za-z0-9_-])",
            body,
        ):
            continue
        if after and note["created_at"] <= after:
            continue
        selected.append(note)
    if not selected:
        raise ValueError("No matching report; inspect worker state or use recovery")
    # Do not rely on Aven's presentation order.
    selected.sort(key=lambda n: (n["created_at"], n["id"]))
    return {"ok": True, "kind": kind, "note": selected[-1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    discovery = subs.add_parser(
        "discover", help="Cache capabilities; emit no help text"
    )
    discovery.add_argument("--cache", type=Path, required=True)
    discovery.add_argument("--refresh", action="store_true")
    report = subs.add_parser("report", help="Return the latest matching note only")
    report.add_argument("--task", required=True)
    report.add_argument(
        "--kind",
        required=True,
        choices=("RESULT", "MERGE", "BLOCKED", "VERIFIED", "DISPATCH", "SUMMARY"),
    )
    report.add_argument("--authorization")
    report.add_argument(
        "--after", help="Exclusive ISO timestamp from the previous event"
    )
    report.add_argument(
        "--input", type=Path, help="Use retained Aven full JSON instead of fetching"
    )
    report.add_argument(
        "--save", type=Path, help="Retain fetched full JSON for recovery"
    )
    report.add_argument("--db")
    report.add_argument("--workspace")
    args = parser.parse_args()
    try:
        if args.command == "discover":
            result = discover(args.cache, args.refresh)
        else:
            if args.input:
                text = args.input.read_text()
            else:
                argv = ["aven", "show", args.task, "--full", "--json"]
                for flag in ("db", "workspace"):
                    if getattr(args, flag):
                        argv.extend(["--" + flag, getattr(args, flag)])
                text = run(argv)
            data = json.loads(text)
            task = data.get("task", {})
            if task.get("ref") != args.task:
                raise ValueError(
                    "Report snapshot must match the exact full task reference"
                )
            if args.save:
                with args.save.open("x") as output:
                    output.write(text)
            result = latest_report(data, args.kind, args.authorization, args.after)
    except (ValueError, OSError, KeyError, TypeError) as error:
        result = {"ok": False, "error": str(error)}
    return emit(result)


if __name__ == "__main__":
    raise SystemExit(main())
