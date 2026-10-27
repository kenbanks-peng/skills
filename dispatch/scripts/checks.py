#!/usr/bin/env python3
"""Run an ordered check plan without terminal windows; save logs and exact evidence."""

import argparse
import platform
import socket
import sys
from pathlib import Path

from runtime import execute, identity, install_interrupts, load, outside, save


def validate(plan):
    if not isinstance(plan, list) or not plan:
        raise ValueError("plan must be a non-empty list")
    seen = set()
    for check in plan:
        if not isinstance(check, dict) or set(check) != {"name", "argv", "timeout_s"}:
            raise ValueError("each check needs name, argv, timeout_s")
        name, argv, timeout = check["name"], check["argv"], check["timeout_s"]
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError("check names must be unique non-empty text")
        seen.add(name)
        if (
            not isinstance(argv, list)
            or not argv
            or any(not isinstance(arg, str) or "\0" in arg for arg in argv)
            or not argv[0]
        ):
            raise ValueError("argv must be a non-empty string list")
        if type(timeout) not in (int, float) or not 0 < timeout <= 86400:
            raise ValueError("timeout_s must be positive and at most 86400")
    return plan


def run_plan(plan, cwd, output, require_system):
    validate(plan)
    if platform.system() != require_system:
        raise ValueError(
            f"requires {require_system}; current system is {platform.system()}"
        )
    before = identity(cwd)
    output = Path(output).resolve()
    outside(output, before["root"])
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "schema": 1,
        "cwd": str(Path(cwd).resolve()),
        "system": platform.system(),
        "host": socket.gethostname(),
        "before": before,
        "after": None,
        "checks": [],
        "passed": False,
        "status": "running",
    }
    save(output / "result.json", result)
    try:
        for index, check in enumerate(plan):
            log = output / f"{index + 1:03d}.log"
            entry = {**check, "log": str(log), "status": "running"}
            result["checks"].append(entry)
            save(output / "result.json", result)
            entry.update(
                execute(
                    check["argv"], str(Path(cwd).resolve()), log, check["timeout_s"]
                )
            )
            save(output / "result.json", result)
            if entry["status"] == "interrupted":
                break
        result["after"] = identity(cwd)
        result["passed"] = (
            len(result["checks"]) == len(plan)
            and all(
                row["status"] == "completed" and row["exit_code"] == 0
                for row in result["checks"]
            )
            and result["before"] == result["after"]
        )
        result["status"] = "passed" if result["passed"] else "failed"
    finally:
        save(output / "result.json", result)
    return result


def main(argv=None):
    install_interrupts()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--require-system", required=True, choices=["Linux", "Darwin"])
    args = parser.parse_args(argv)
    try:
        result = run_plan(load(args.plan), args.cwd, args.output, args.require_system)
        print(Path(args.output).resolve() / "result.json")
        return 0 if result["passed"] else 1
    except (ValueError, OSError) as error:
        print(f"checks: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
