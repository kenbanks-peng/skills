#!/usr/bin/env python3
"""Render a read-only TML view or a state patch. Do not launch or schedule work."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "dashboard.tml"
STATES = {"none", "working", "needs_input", "idle", "done", "errored", "unknown"}
TEXT_FIELDS = (
    "task", "task_state", "attempt", "agent", "session", "pane", "branch",
    "worktree", "environment", "queue", "review", "checks", "delivery",
    "blockers", "cleanup",
)
NATIVE_FIELDS = ("state", "source", "identity", "evidence_age_ms", "completion_seq", "subagents")
EMPTY_STATE = '{"revision":0,"board":{"run":"No snapshot","observed_at":"unknown","tasks":[]}}'
MAX_PATCH = 64 * 1024
MAX_DOCUMENT = 256 * 1024


def text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: expected non-empty text; use 'none' or 'unknown'")
    if any(ord(c) < 32 and c not in "\n\r\t" for c in value):
        raise ValueError(f"{label}: control character")
    return value


def keys(value, required, label):
    if not isinstance(value, dict) or set(value) != set(required):
        raise ValueError(f"{label}: expected keys {', '.join(required)}")


def board(snapshot):
    """Validate dispatcher input. Native fields are observations, not inferred states."""
    keys(snapshot, ("run", "revision", "observed_at", "tasks"), "snapshot")
    text(snapshot["run"], "run")
    text(snapshot["observed_at"], "observed_at")
    if type(snapshot["revision"]) is not int or snapshot["revision"] < 0:
        raise ValueError("revision: expected a non-negative integer")
    if not isinstance(snapshot["tasks"], list):
        raise ValueError("tasks: expected a list")
    rows, seen = [], set()
    for task in snapshot["tasks"]:
        keys(task, (*TEXT_FIELDS, "dependencies", "native"), "task")
        row = {key: text(task[key], key) for key in TEXT_FIELDS}
        pair = (row["task"], row["attempt"])
        if pair in seen:
            raise ValueError("duplicate task and attempt")
        seen.add(pair)
        deps = task["dependencies"]
        if not isinstance(deps, list):
            raise ValueError("dependencies: expected a list")
        row["dependencies"] = ", ".join(text(dep, "dependency") for dep in deps) or "none"
        native = task["native"]
        keys(native, NATIVE_FIELDS, "native")
        if text(native["state"], "native.state") not in STATES:
            raise ValueError("native.state: unknown native state")
        for key in ("state", "source", "identity"):
            row[key] = text(native[key], "native." + key)
        for key in ("evidence_age_ms", "completion_seq", "subagents"):
            value = native[key]
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"native.{key}: expected a non-negative integer or null")
            row[key] = "unknown" if value is None else str(value)
        rows.append(row)
    return {"run": snapshot["run"], "observed_at": snapshot["observed_at"], "tasks": rows}


def compact(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def render(snapshot):
    view = board(snapshot)
    state = {"revision": snapshot["revision"], "board": view}
    template = TEMPLATE.read_text(encoding="utf-8")
    document = template.replace(EMPTY_STATE, escape(compact(state)))
    if len(document.encode("utf-8")) > MAX_DOCUMENT:
        raise ValueError("document exceeds native 256 KiB limit; reduce snapshot")
    return document


def patch(previous, current):
    before, after = board(previous), board(current)
    if previous["run"] != current["run"]:
        raise ValueError("cannot patch another run")
    if current["revision"] <= previous["revision"]:
        raise ValueError("patch revision must increase")
    ops = [
        {"op": "test", "path": "/revision", "value": previous["revision"]},
        {"op": "test", "path": "/board/run", "value": previous["run"]},
    ]
    if before != after:
        ops.append({"op": "replace", "path": "/board", "value": after})
    ops.append({"op": "replace", "path": "/revision", "value": current["revision"]})
    result = compact(ops)
    if len(result.encode("utf-8")) > MAX_PATCH:
        raise ValueError("patch exceeds native 64 KiB limit; reduce snapshot")
    return result


def observe(snapshot, inventory):
    """Replace native observations, including stale/missing workers, from one inventory."""
    board(snapshot)
    if not isinstance(inventory, dict) or not isinstance(inventory.get("panes"), dict):
        raise ValueError("expected workspace status/audit inventory")
    stamp = inventory.get("observed_at")
    if (inventory.get("ok") is not True or type(stamp) not in (int, float)
            or not 0 <= datetime.now(timezone.utc).timestamp() - stamp <= 60):
        raise ValueError("inventory failed or is older than 60 seconds; run workspace status")
    current = json.loads(compact(snapshot))
    current["revision"] += 1
    current["observed_at"] = datetime.now(timezone.utc).isoformat()
    for task in current["tasks"]:
        address = task["session"] + "/" + task["pane"]
        pane = inventory["panes"].get(address, {})
        state = pane.get("agent_state", "unknown")
        task["native"] = {
            "state": state if state in STATES else "unknown",
            "source": "workspace inventory" if pane else "missing from inventory",
            "identity": address, "evidence_age_ms": None,
            "completion_seq": pane.get("completion_seq"),
            "subagents": None,
        }
    board(current)
    return current


def report(snapshot):
    view = board(snapshot)

    def short(value, width):
        return " ".join(value.split())[:width]

    lines = [f"Dispatch: {short(view['run'], 60)} (revision {snapshot['revision']})",
             "Task                 State        Environment     Blocker",
             "-" * 79]
    for row in view["tasks"]:
        lines.append(f"{short(row['task'], 20):20} {short(row['state'], 12):12} "
                     f"{short(row['environment'], 15):15} {short(row['blockers'], 26)}")
    if not view["tasks"]:
        lines.append("No tasks.")
    return "\n".join(line[:80] for line in lines)


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    render_command = commands.add_parser("render", help="write TML to stdout")
    render_command.add_argument("snapshot")
    patch_command = commands.add_parser("patch", help="write JSON Patch to stdout")
    patch_command.add_argument("previous")
    patch_command.add_argument("current")
    report_command = commands.add_parser("report", help="print status in the existing dispatch pane")
    report_command.add_argument("snapshot")
    observe_command = commands.add_parser("observe", help="refresh native fields from workspace inventory")
    observe_command.add_argument("snapshot")
    observe_command.add_argument("--inventory", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "render":
            result = render(load(args.snapshot))
        elif args.command == "patch":
            result = patch(load(args.previous), load(args.current))
        elif args.command == "report":
            result = report(load(args.snapshot))
        else:
            result = compact(observe(load(args.snapshot), load(args.inventory)))
    except (ValueError, TypeError, OSError) as error:
        print(f"dashboard: {error}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
