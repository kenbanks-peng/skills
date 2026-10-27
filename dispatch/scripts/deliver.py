#!/usr/bin/env python3
"""Deliver one reviewed, checked candidate through native ship, then check the target."""

import argparse
import json
import sys
from pathlib import Path

from checks import run_plan, validate
from runtime import Native, git, identity, install_interrupts, load, lock, outside, save
from workspace import key


def deliver(args, state):
    native = Native(state["server"])
    address = key(args.session, args.window)
    owned = state["owned"].get(address)
    if not owned or owned["role"] in {"dispatch", "aven"}:
        raise ValueError("source must be a registered task window")
    inventory = native.inventory()
    if address not in inventory or inventory[address]["host"] != "local":
        raise ValueError(
            "native ship needs an existing local candidate; pull Linux work first"
        )
    source = identity(args.cwd)
    pane_cwd = inventory[address].get("cwd")
    if not pane_cwd or identity(pane_cwd)["root"] != source["root"]:
        raise ValueError("source checkout does not match the native pane")
    target = identity(args.target_repo)
    if source["root"] == target["root"]:
        raise ValueError("source and target must use separate checkouts")
    source_common = git(
        args.cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    target_common = git(
        args.target_repo, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    if source_common != target_common:
        raise ValueError("source and target are not in the same Git repository")
    if target["dirty"]:
        raise ValueError("target checkout is dirty")
    if git(args.target_repo, "branch", "--show-current").decode().strip() != args.into:
        raise ValueError("target checkout is not on the recorded target branch")
    if git(args.cwd, "branch", "--show-current").decode().strip() in {"", args.into}:
        raise ValueError("source needs a distinct task branch")
    evidence = load(args.checks)
    if not evidence.get("passed") or evidence.get("status") != "passed":
        raise ValueError("candidate checks did not pass")
    if evidence.get("after") != source or evidence.get("before") != source:
        raise ValueError("check evidence is stale or belongs to another checkout")
    if not args.reviewed:
        raise ValueError(
            "independent review is required; pass --reviewed after acceptance"
        )
    plan = validate(load(args.integration_plan))
    native.resting(
        args.session, args.window, require_agent=owned["role"] == "linux-worker"
    )
    output = Path(args.output).resolve()
    outside(output, source["root"])
    outside(output, target["root"])
    output.mkdir(parents=True, exist_ok=False)
    result = {
        "source": source,
        "target_before": target,
        "steps": [],
        "status": "prepared",
        "policy": args.policy,
        "into": args.into,
    }
    save(output / "result.json", result)

    def ship(operation, *flags):
        # An interrupted pending step is never replayed by this script.
        step = {"operation": operation, "status": "pending"}
        result["steps"].append(step)
        save(output / "result.json", result)
        response = native.call(
            "ship", operation, "-s", args.session, "-w", args.window, *flags, "--json"
        )
        step.update(status="returned", response=response)
        save(output / "result.json", result)

    try:
        if source["dirty"]:
            ship("commit", "-m", args.message)
        result["candidate"] = identity(args.cwd)
        if result["candidate"]["dirty"]:
            raise ValueError("source remains dirty after commit")
        native.resting(
            args.session, args.window, require_agent=owned["role"] == "linux-worker"
        )
        if identity(args.target_repo) != target:
            raise ValueError("target changed before merge")
        ship("merge", "--into", args.into, "--" + args.policy, "-m", args.message)
        result["target_after"] = identity(args.target_repo)
        result["status"] = "merged"
        save(output / "result.json", result)
        integrated = run_plan(
            plan, args.target_repo, output / "integration", evidence["system"]
        )
        result["status"] = "delivered" if integrated["passed"] else "integration_failed"
    except (ValueError, OSError, KeyboardInterrupt) as error:
        result["error"] = (
            str(error) or "interrupted; reconcile native state before retry"
        )
        result["status"] = "blocked"
    finally:
        save(output / "result.json", result)
    return result


def main(argv=None):
    install_interrupts()
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "run-dir",
        "session",
        "window",
        "cwd",
        "target-repo",
        "into",
        "message",
        "checks",
        "integration-plan",
        "output",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--policy", required=True, choices=["squash", "ff-only"])
    parser.add_argument("--reviewed", action="store_true")
    args = parser.parse_args(argv)
    try:
        if (
            not args.message.strip()
            or not args.into.strip()
            or args.into.startswith("-")
        ):
            raise ValueError(
                "message and target branch must be explicit non-empty values"
            )
        with lock(args.run_dir):
            state = load(Path(args.run_dir) / "run.json")
            result = deliver(args, state)
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "delivered" else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"deliver: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
