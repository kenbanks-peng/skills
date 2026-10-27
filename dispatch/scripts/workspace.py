#!/usr/bin/env python3
"""Record exact run-owned windows, audit inventory, and close saved, idle resources."""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from runtime import Native, full_id, identity, load, lock, outside, save

ROLES = {"aven", "linux-worker", "auxiliary"}


def key(session, window):
    if not session or session.startswith("-") or "/" in session:
        raise ValueError("invalid session address")
    return session + "/" + full_id(window)


def initialize(args):
    directory = Path(args.run_dir).resolve()
    repo = identity(args.repo)
    outside(directory, repo["root"])
    native = Native(args.server)
    baseline = native.inventory()
    dispatch = key(args.session, args.dispatch)
    if dispatch not in baseline:
        raise ValueError("dispatch window is absent from inventory")
    directory.mkdir(parents=True, exist_ok=False)
    state = {
        "schema": 1,
        "server": args.server,
        "repo": repo,
        "dispatch": dispatch,
        "baseline": list(baseline),
        "owned": {
            dispatch: {
                "role": "dispatch",
                "session": args.session,
                "window_id": args.dispatch,
            }
        },
        "excluded": [],
        "events": [],
    }
    save(directory / "baseline.json", baseline)
    save(directory / "run.json", state)
    return {"run_dir": str(directory), "dispatch": dispatch}


def inspect(state, native, final=False):
    inventory = native.inventory()
    unknown = sorted(
        set(inventory)
        - set(state["baseline"])
        - set(state["owned"])
        - set(state["excluded"])
    )
    auxiliary = sorted(
        k
        for k, row in state["owned"].items()
        if k in inventory and row["role"] == "auxiliary"
    )
    remaining = sorted(
        k for k in state["owned"] if k in inventory and k != state["dispatch"]
    )
    issues = []
    if state["dispatch"] not in inventory:
        issues.append("dispatch is missing")
    if unknown:
        issues.append(
            "unclassified new windows; register ownership or exclude unrelated IDs"
        )
    if auxiliary and not final:
        issues.append("auxiliary windows exist; no hidden-window support is certified")
    if remaining and final:
        issues.append("run-owned windows remain besides dispatch")
    return {
        "ok": not issues,
        "observed_at": time.time(),
        "issues": issues,
        "unknown": unknown,
        "auxiliary": auxiliary,
        "remaining": remaining,
        "panes": inventory,
    }


def register(state, native, args):
    address = key(args.session, args.window)
    inventory = native.inventory()
    if address == state["dispatch"]:
        raise ValueError("dispatch ownership cannot change")
    if address in state["baseline"]:
        raise ValueError("refusing ownership of a pre-existing unrelated window")
    if address not in inventory:
        raise ValueError("window is absent from inventory")
    if args.command == "exclude":
        if address in state["owned"]:
            raise ValueError("cannot exclude an owned window")
        if address not in state["excluded"]:
            state["excluded"].append(address)
        return {"excluded": address}
    if address in state["excluded"]:
        raise ValueError("window was excluded as unrelated")
    if args.role == "linux-worker" and args.system != "Linux":
        raise ValueError(
            "Linux worker registration requires --system Linux from host preflight"
        )
    resource = {"role": args.role, "session": args.session, "window_id": args.window}
    if address in state["owned"] and state["owned"][address] != resource:
        raise ValueError("owned window role cannot change")
    state["owned"][address] = resource
    return {"registered": address, "role": args.role}


def queue_once(state, native, directory, args):
    address = key(args.session, args.window)
    if state["owned"].get(address, {}).get("role") != "linux-worker":
        raise ValueError("queue target must be a registered Linux worker")
    text = Path(args.prompt_file).read_text(encoding="utf-8")
    if not text.strip() or len(text.encode()) > 16384:
        raise ValueError("prompt must contain 1 to 16384 UTF-8 bytes")
    if not args.id.strip() or len(args.id) > 256:
        raise ValueError("follow-up ID must contain 1 to 256 characters")
    digest = hashlib.sha256(text.encode()).hexdigest()
    requests = state.setdefault("followups", {})
    previous = requests.get(args.id)
    if previous:
        if previous["window"] != address or previous["sha256"] != digest:
            raise ValueError("follow-up ID already names different work")
        if previous["status"] != "submitted":
            raise ValueError(
                "follow-up submission is uncertain; reconcile without requeue"
            )
        return previous
    inventory = native.inventory()
    if address not in inventory or inventory[address].get("agent_state") not in {
        "working",
        "idle",
        "done",
    }:
        raise ValueError("queue target state is missing, blocked, or unsupported")
    request = {"window": address, "sha256": digest, "status": "pending"}
    requests[args.id] = request
    save(directory / "run.json", state)
    response = native.call(
        "queue", "-s", args.session, "-w", args.window, "--json", "--", text
    )
    if not isinstance(response, dict) or response.get("success") is not True:
        raise ValueError("queue response is uncertain; reconcile without requeue")
    request.update(status="submitted", response=response)
    save(directory / "run.json", state)
    return request


def cleanup(state, native, directory, evidence_saved, selected=None):
    if not evidence_saved:
        raise ValueError(
            "save results and stop background writers first; pass --evidence-saved"
        )
    if selected is not None and (
        selected not in state["owned"] or selected == state["dispatch"]
    ):
        raise ValueError("close needs an owned non-dispatch window")
    initial = inspect(state, native)
    # Never close anything when the protected dispatch identity is uncertain.
    if state["dispatch"] not in initial["panes"]:
        raise ValueError("dispatch is missing; cleanup blocked")
    failures = {}
    for address, row in state["owned"].items():
        if (
            address == state["dispatch"]
            or address not in initial["panes"]
            or (selected is not None and address != selected)
        ):
            continue
        try:
            native.resting(
                row["session"],
                row["window_id"],
                require_agent=row["role"] == "linux-worker",
            )
            log = native.call(
                "capture-pane",
                "-s",
                row["session"],
                "-w",
                row["window_id"],
                "--scrollback",
                "--lines",
                "0",
                json_output=False,
            )
            (directory / (row["window_id"] + ".log")).write_text(log)
            # Persist intent before the close. A resumed cleanup inventories first.
            state["events"].append(
                {
                    "action": "close",
                    "window": address,
                    "status": "pending",
                    "time": time.time(),
                }
            )
            save(directory / "run.json", state)
            native.call(
                "close-window", "-s", row["session"], row["window_id"], "--json"
            )
            state["events"][-1]["status"] = "returned"
        except (ValueError, OSError) as error:
            failures[address] = str(error)
        finally:
            save(directory / "run.json", state)
    result = inspect(state, native, final=selected is None)
    result["failures"] = failures
    result["ok"] = result["ok"] and not failures
    filename = (
        "cleanup.json"
        if selected is None
        else "close-" + selected.split("/")[-1] + ".json"
    )
    save(directory / filename, result)
    return result


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--run-dir", required=True)
    sub = root.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--repo", required=True)
    init.add_argument("--server", default=os.environ.get("TUIOS_SERVER", ""))
    init.add_argument("--session", required=True)
    init.add_argument("--dispatch", required=True)
    for name in ("register", "exclude"):
        command = sub.add_parser(name)
        command.add_argument("--session", required=True)
        command.add_argument("--window", required=True)
        if name == "register":
            command.add_argument("--role", required=True, choices=sorted(ROLES))
            command.add_argument("--system", choices=["Linux", "Darwin"])
    queued = sub.add_parser("queue")
    queued.add_argument("--session", required=True)
    queued.add_argument("--window", required=True)
    queued.add_argument("--id", required=True)
    queued.add_argument("--prompt-file", required=True)
    audit = sub.add_parser("audit")
    audit.add_argument("--final", action="store_true")
    sub.add_parser("status")
    close = sub.add_parser("cleanup")
    close.add_argument("--evidence-saved", action="store_true")
    single = sub.add_parser("close")
    single.add_argument("--session", required=True)
    single.add_argument("--window", required=True)
    single.add_argument("--evidence-saved", action="store_true")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        directory = Path(args.run_dir).resolve()
        if args.command == "init":
            result = initialize(args)
        else:
            with lock(directory):
                state = load(directory / "run.json")
                if state.get("schema") != 1:
                    raise ValueError("unsupported run state")
                native = Native(state["server"])
                if args.command in {"register", "exclude"}:
                    result = register(state, native, args)
                    save(directory / "run.json", state)
                elif args.command == "queue":
                    result = queue_once(state, native, directory, args)
                elif args.command in {"cleanup", "close"}:
                    selected = (
                        key(args.session, args.window)
                        if args.command == "close"
                        else None
                    )
                    result = cleanup(
                        state, native, directory, args.evidence_saved, selected
                    )
                else:
                    try:
                        result = inspect(
                            state, native, final=getattr(args, "final", False)
                        )
                    except (ValueError, OSError, KeyError, TypeError) as error:
                        save(
                            directory / "inventory.json",
                            {
                                "ok": False,
                                "panes": {},
                                "observed_at": time.time(),
                                "issues": [str(error)],
                            },
                        )
                        raise
                    save(directory / "inventory.json", result)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok", True) else 1
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"workspace: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
