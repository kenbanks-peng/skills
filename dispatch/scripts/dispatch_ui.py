#!/usr/bin/env python3
"""Explicit dispatch UI startup: python3 dispatch/scripts/dispatch_ui.py startup.

Run in the dispatcher agent's original host terminal, not a worker container.
Startup is never invoked by task intake. Launch/resume use the exact worker adapter.
Herdr contract evidence: kenbanks-peng/workmux at
84fd26da903939e15963ec334232793b5d98fc31, src/multiplexer/herdr/{client,mod}.rs:
protocol 22, session.snapshot, pane.process_info(shell_pid), tab.rename.
Inherited labels/active-pane hints are deliberately not accepted as identity.
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from pathlib import Path


class UIError(ValueError):
    """Unsafe or unsupported UI identity; no fallback target is permitted."""


def require(condition, message):
    if not condition:
        raise UIError(message)


def command(argv):
    try:
        result = subprocess.run(argv, text=True, capture_output=True, timeout=10)
    except subprocess.TimeoutExpired as error:
        raise UIError(f"{argv[0]} timed out; preserve the saved UI identity") from error
    require(result.returncode == 0, f"{argv[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def ancestors():
    """Use the host process tree, not a container PID or inherited pane hint."""
    lineage = set()
    pid = os.getpid()
    if sys.platform == "linux":
        while pid > 0 and pid not in lineage:
            lineage.add(pid)
            # comm may contain spaces or parentheses; fields after its final ')'
            # begin with state, then ppid.
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            pid = int(fields[1])
        return lineage
    rows = command(["ps", "-axo", "pid=,ppid="])
    parents = {}
    for row in rows.splitlines():
        child, parent = map(int, row.split())
        parents[child] = parent
    while pid > 0 and pid not in lineage:
        lineage.add(pid)
        pid = parents.get(pid, 0)
    return lineage


class Herdr:
    """Bounded, non-retrying requests to one pinned local socket endpoint."""

    def __init__(self, endpoint):
        require(endpoint and Path(endpoint).is_absolute(),
                "Herdr startup requires an absolute HERDR_SOCKET_PATH on the host")
        self.endpoint = endpoint
        self.identity = self.socket_identity()

    def socket_identity(self):
        stat = os.stat(self.endpoint)
        return stat.st_dev, stat.st_ino

    def request(self, method, **params):
        require(self.socket_identity() == self.identity,
                "Herdr socket changed; refusing to reuse tab identity")
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(8)
            stream.connect(self.endpoint)
            require(self.socket_identity() == self.identity,
                    "Herdr socket changed during connection")
            payload = {"id": "dispatch-ui", "method": method, "params": params}
            stream.sendall(json.dumps(payload).encode() + b"\n")
            with stream.makefile("rb") as response:
                line = response.readline(8 * 1024 * 1024 + 1)
            require(len(line) <= 8 * 1024 * 1024 and line.endswith(b"\n"),
                    "Incomplete or oversized Herdr response")
        data = json.loads(line)
        require(isinstance(data, dict) and data.get("id") == "dispatch-ui",
                "Unexpected Herdr response identity")
        require("error" not in data, f"Herdr {method} failed: {data.get('error')}")
        require(isinstance(data.get("result"), dict), "Missing Herdr result")
        return data["result"]

    def snapshot(self):
        data = self.request("session.snapshot")["snapshot"]
        require(isinstance(data, dict), "Malformed Herdr snapshot")
        version = data.get("version", "")
        require(isinstance(version, str) and re.fullmatch(r"\d+\.\d+\.\d+", version)
                and tuple(map(int, version.split("."))) >= (0, 9, 0)
                and data.get("protocol") == 22,
                "Unsupported Herdr API; expected >= 0.9.0 protocol 22")
        require(isinstance(data.get("panes"), list) and isinstance(data.get("tabs"), list),
                "Malformed Herdr inventory")
        return data


def current_herdr_tab(client, lineage):
    inventory = client.snapshot()
    matches = []
    for pane in inventory["panes"]:
        pane_id = pane["pane_id"]
        require(isinstance(pane_id, str) and pane_id, "Missing Herdr pane ID")
        info = client.request("pane.process_info", pane_id=pane_id)["process_info"]
        pid = info["shell_pid"]
        require(type(pid) is int and pid > 0, "Missing Herdr shell PID")
        if pid in lineage:
            matches.append(pane)
    require(len(matches) == 1,
            f"Cannot identify dispatcher pane: found {len(matches)} ancestry matches; "
            "run startup in the original dispatcher host terminal")
    pane = matches[0]
    tabs = [tab for tab in inventory["tabs"] if tab["tab_id"] == pane["tab_id"]]
    require(len(tabs) == 1 and tabs[0]["workspace_id"] == pane["workspace_id"],
            "Missing or ambiguous Herdr tab identity")
    require(isinstance(pane["tab_id"], str) and pane["tab_id"], "Missing Herdr tab ID")
    identity = tuple(pane[key] for key in
                     ("pane_id", "terminal_id", "tab_id", "workspace_id"))
    require(all(isinstance(value, str) and value for value in identity),
            "Missing Herdr pane identity")
    return identity, tabs[0]


def startup(environ=None):
    env = os.environ if environ is None else environ
    if env.get("HERDR_ENV") == "1":
        client = Herdr(env.get("HERDR_SOCKET_PATH"))
        lineage = ancestors()
        pane, tab = current_herdr_tab(client, lineage)
        if tab["label"] != "dispatcher":
            # Re-resolve before mutation: a moved pane must not rename its old tab.
            confirmed, _ = current_herdr_tab(client, ancestors())
            require(confirmed == pane, "Dispatcher pane moved during startup; retry explicitly")
            client.request("tab.rename", tab_id=tab["tab_id"], label="dispatcher")
        confirmed, tab = current_herdr_tab(client, ancestors())
        require(confirmed == pane and tab["label"] == "dispatcher",
                "Dispatcher tab naming could not be verified")
        return {"backend": "herdr", "pane_id": pane[0],
                "tab_id": tab["tab_id"], "name": "dispatcher"}
    require(env.get("TMUX"), "Startup requires the original Herdr or tmux host context")
    pane = env.get("TMUX_PANE", "")
    require(re.fullmatch(r"%\d+", pane), "Missing or invalid TMUX_PANE identity")
    row = command(["tmux", "display-message", "-p", "-t", pane,
                   "#{pane_id}\t#{window_id}"]).split("\t")
    require(len(row) == 2 and row[0] == pane and re.fullmatch(r"@\d+", row[1]),
            "Cannot resolve exact dispatcher tmux window")
    window = row[1]
    # Prevent tmux's automatic process-name updates from replacing the fixed name.
    command(["tmux", "set-window-option", "-t", window, "automatic-rename", "off"])
    command(["tmux", "rename-window", "-t", window, "dispatcher"])
    require(command(["tmux", "display-message", "-p", "-t", pane,
                     "#{window_id}\t#{window_name}"]) == window + "\tdispatcher",
            "Dispatcher tmux window naming could not be verified")
    return {"backend": "tmux", "pane_id": pane, "tab_id": window, "name": "dispatcher"}


def worker_tab(ui, name, saved=None, *, rename=True):
    """Name only the observed worker, pinning its full tab identity before mutation.

    Workmux Herdr pane keys are server-lifetime~terminal_id, not native pane IDs.
    Labels are display data, never selectors. Call with rename=False and persist
    the returned identity before the first mutation so interrupted resume is safe.
    """
    require(re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", name),
            "Invalid displayed worker task reference")
    require(len(ui["agents"]) == 1, "Expected one exact worker UI identity")
    pane = ui["agents"][0]["pane_id"]
    context = ui["context"]
    if context["backend"] == "herdr":
        endpoint = context["instance"]
        client = Herdr(endpoint)
        boot, separator, terminal = pane.partition("~")
        require(boot and separator and terminal, "Expected verified Workmux Herdr pane key")

        def resolve():
            inventory = client.snapshot()
            panes = [p for p in inventory["panes"] if p["terminal_id"] == terminal]
            require(len(panes) == 1, "Missing or ambiguous worker terminal identity")
            p = panes[0]
            tabs = [t for t in inventory["tabs"] if t["tab_id"] == p["tab_id"]
                    and t["workspace_id"] == p["workspace_id"]]
            require(len(tabs) == 1, "Missing or ambiguous worker tab identity")
            identity = {key: p[key] for key in
                        ("pane_id", "terminal_id", "tab_id", "workspace_id")}
            require(all(isinstance(v, str) and v for v in identity.values()),
                    "Missing worker pane identity")
            identity.update(backend="herdr", endpoint=endpoint,
                            socket_identity=list(client.identity), workmux_pane=pane)
            return identity, tabs[0]["label"]

        identity, label = resolve()
        require(saved is None or identity == saved, "Saved worker tab identity changed")
        if rename:
            confirmed, _ = resolve()
            require(confirmed == identity, "Worker pane moved before naming")
            if label != name:
                client.request("tab.rename", tab_id=identity["tab_id"], label=name)
            confirmed, label = resolve()
            require(confirmed == identity and label == name,
                    "Worker tab naming could not be verified")
        return identity
    require(context["backend"] == "tmux", "Unsupported worker UI backend")
    require(re.fullmatch(r"%\d+", pane), "Invalid worker tmux pane")
    endpoint = context["instance"]
    require(isinstance(endpoint, str) and Path(endpoint).is_absolute(),
            "Missing exact worker tmux socket")

    def tmux(*argv):
        return command(["tmux", "-S", endpoint, *argv])

    def resolve():
        row = tmux("display-message", "-p", "-t", pane,
                   "#{pane_id}\t#{window_id}\t#{session_id}").split("\t")
        require(len(row) == 3 and row[0] == pane and re.fullmatch(r"@\d+", row[1])
                and row[2] == ui["agents"][0]["session"],
                "Cannot resolve exact worker tmux window")
        return dict(backend="tmux", endpoint=endpoint, pane_id=pane,
                    tab_id=row[1], session=row[2])

    identity = resolve()
    require(saved is None or identity == saved, "Saved worker tab identity changed")
    if rename:
        require(resolve() == identity, "Worker pane moved before naming")
        for option in ("automatic-rename", "allow-rename"):
            tmux("set-window-option", "-t", identity["tab_id"], option, "off")
        tmux("rename-window", "-t", identity["tab_id"], name)
        require(resolve() == identity and tmux("display-message", "-p", "-t", pane,
                "#{window_name}") == name, "Worker tab naming could not be verified")
    return identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["startup"])
    parser.parse_args()
    try:
        print(json.dumps(startup()))
    except (UIError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"dispatch UI startup: {error}; no fallback tab was selected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
