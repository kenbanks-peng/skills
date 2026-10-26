"""Internal dispatch UI adapters.

Run in the dispatcher agent's original host terminal, not a worker container.
Startup is never invoked by task intake. Launch/resume use the exact worker adapter.
Herdr contract evidence: kenbanks-peng/workmux at
84fd26da903939e15963ec334232793b5d98fc31, src/multiplexer/herdr/{client,mod}.rs:
protocol 22, session.snapshot, pane.process_info(shell_pid), tab.rename.
Inherited labels/active-pane hints are deliberately not accepted as identity.
"""

import json
import os
import re
import shlex
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
        require(
            endpoint and Path(endpoint).is_absolute(),
            "Herdr startup requires an absolute HERDR_SOCKET_PATH on the host",
        )
        self.endpoint = endpoint
        self.identity = self.socket_identity()

    def socket_identity(self):
        stat = os.stat(self.endpoint)
        return stat.st_dev, stat.st_ino

    def request(self, method, **params):
        require(
            self.socket_identity() == self.identity,
            "Herdr socket changed; refusing to reuse tab identity",
        )
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(8)
            stream.connect(self.endpoint)
            require(
                self.socket_identity() == self.identity,
                "Herdr socket changed during connection",
            )
            payload = {"id": "dispatch-ui", "method": method, "params": params}
            stream.sendall(json.dumps(payload).encode() + b"\n")
            with stream.makefile("rb") as response:
                line = response.readline(8 * 1024 * 1024 + 1)
            require(
                len(line) <= 8 * 1024 * 1024 and line.endswith(b"\n"),
                "Incomplete or oversized Herdr response",
            )
        data = json.loads(line)
        require(
            isinstance(data, dict) and data.get("id") == "dispatch-ui",
            "Unexpected Herdr response identity",
        )
        require("error" not in data, f"Herdr {method} failed: {data.get('error')}")
        require(isinstance(data.get("result"), dict), "Missing Herdr result")
        return data["result"]

    def snapshot(self):
        data = self.request("session.snapshot")["snapshot"]
        require(isinstance(data, dict), "Malformed Herdr snapshot")
        version = data.get("version", "")
        require(
            isinstance(version, str)
            and re.fullmatch(r"\d+\.\d+\.\d+", version)
            and tuple(map(int, version.split("."))) >= (0, 9, 0)
            and data.get("protocol") == 22,
            "Unsupported Herdr API; expected >= 0.9.0 protocol 22",
        )
        require(
            isinstance(data.get("panes"), list) and isinstance(data.get("tabs"), list),
            "Malformed Herdr inventory",
        )
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
    require(
        len(matches) == 1,
        f"Cannot identify dispatcher pane: found {len(matches)} ancestry matches; "
        "run startup in the original dispatcher host terminal",
    )
    pane = matches[0]
    tabs = [tab for tab in inventory["tabs"] if tab["tab_id"] == pane["tab_id"]]
    require(
        len(tabs) == 1 and tabs[0]["workspace_id"] == pane["workspace_id"],
        "Missing or ambiguous Herdr tab identity",
    )
    require(isinstance(pane["tab_id"], str) and pane["tab_id"], "Missing Herdr tab ID")
    identity = tuple(
        pane[key] for key in ("pane_id", "terminal_id", "tab_id", "workspace_id")
    )
    require(
        all(isinstance(value, str) and value for value in identity),
        "Missing Herdr pane identity",
    )
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
            require(
                confirmed == pane,
                "Dispatcher pane moved during startup; retry explicitly",
            )
            client.request("tab.rename", tab_id=tab["tab_id"], label="dispatcher")
        confirmed, tab = current_herdr_tab(client, ancestors())
        require(
            confirmed == pane and tab["label"] == "dispatcher",
            "Dispatcher tab naming could not be verified",
        )
        return {
            "backend": "herdr",
            "pane_id": pane[0],
            "tab_id": tab["tab_id"],
            "name": "dispatcher",
        }
    require(env.get("TMUX"), "Startup requires the original Herdr or tmux host context")
    pane = env.get("TMUX_PANE", "")
    require(re.fullmatch(r"%\d+", pane), "Missing or invalid TMUX_PANE identity")
    row = command(
        ["tmux", "display-message", "-p", "-t", pane, "#{pane_id}\t#{window_id}"]
    ).split("\t")
    require(
        len(row) == 2 and row[0] == pane and re.fullmatch(r"@\d+", row[1]),
        "Cannot resolve exact dispatcher tmux window",
    )
    window = row[1]
    # Prevent tmux's automatic process-name updates from replacing the fixed name.
    command(["tmux", "set-window-option", "-t", window, "automatic-rename", "off"])
    command(["tmux", "rename-window", "-t", window, "dispatcher"])
    require(
        command(
            [
                "tmux",
                "display-message",
                "-p",
                "-t",
                pane,
                "#{window_id}\t#{window_name}",
            ]
        )
        == window + "\tdispatcher",
        "Dispatcher tmux window naming could not be verified",
    )
    return {"backend": "tmux", "pane_id": pane, "tab_id": window, "name": "dispatcher"}


def aven_tab(repo, argv, record, persist, environ=None):
    """Create once, retaining intent before mutation and exact identity afterward.

    layout.apply's new-tab contract matches Workmux's pinned Herdr new_tab:
    never supply tab_id (that would replace an occupied tab).
    An interrupted create is deliberately not retried, even if no ID was saved.
    """
    require(
        not record.get("aven_close_attempted") and not record.get("aven_closed"),
        "Run closure has started; use a new run ID for new work",
    )
    env = os.environ if environ is None else environ
    if env.get("HERDR_ENV") == "1":
        client = Herdr(env.get("HERDR_SOCKET_PATH"))
        pane, _ = current_herdr_tab(client, ancestors())
        parent = dict(
            backend="herdr",
            endpoint=client.endpoint,
            socket_identity=list(client.identity),
            pane_id=pane[0],
            terminal_id=pane[1],
            tab_id=pane[2],
            workspace_id=pane[3],
        )
    else:
        require(
            env.get("TMUX"), "Aven tab requires the original Herdr or tmux host context"
        )
        pane = env.get("TMUX_PANE", "")
        require(re.fullmatch(r"%\d+", pane), "Missing exact dispatcher tmux pane")
        row = command(
            [
                "tmux",
                "display-message",
                "-p",
                "-t",
                pane,
                "#{socket_path}\t#{session_id}\t#{window_id}\t#{pane_id}",
            ]
        ).split("\t")
        require(
            len(row) == 4
            and row[3] == pane
            and Path(row[0]).is_absolute()
            and re.fullmatch(r"\$\d+", row[1])
            and re.fullmatch(r"@\d+", row[2]),
            "Cannot identify exact dispatcher tmux server/session",
        )
        stat = os.stat(row[0])
        parent = dict(
            backend="tmux",
            endpoint=row[0],
            session=row[1],
            tab_id=row[2],
            pane_id=pane,
            socket_identity=[stat.st_dev, stat.st_ino],
        )

    require(
        not record.get("dispatcher") or record["dispatcher"] == parent,
        "Saved dispatcher UI identity changed; no replacement Aven tab will be opened",
    )
    record["dispatcher"] = parent

    def tmux(*args):
        return command(["tmux", "-S", parent["endpoint"], *args])

    def verify():
        saved = record["aven_tab"]
        require(saved["tab_id"] != parent["tab_id"], "Aven tab overlaps dispatcher")
        if parent["backend"] == "herdr":
            inventory = client.snapshot()
            matches = [
                p
                for p in inventory["panes"]
                if all(
                    p.get(k) == saved[k]
                    for k in ("pane_id", "terminal_id", "tab_id", "workspace_id")
                )
            ]
            require(
                len(matches) == 1, "Saved Aven pane identity changed or disappeared"
            )
            require(
                any(
                    t["tab_id"] == saved["tab_id"]
                    and t["workspace_id"] == parent["workspace_id"]
                    for t in inventory["tabs"]
                ),
                "Saved Aven tab disappeared",
            )
        else:
            observed = tmux(
                "display-message",
                "-p",
                "-t",
                saved["pane_id"],
                "#{pane_id}\t#{window_id}\t#{session_id}",
            )
            require(
                observed
                == "\t".join([saved["pane_id"], saved["tab_id"], parent["session"]]),
                "Saved Aven tmux identity changed",
            )

    if record.get("aven_tab"):
        verify()
        return record
    require(
        not record.get("creation_attempted"),
        "Aven tab creation was interrupted; reconcile retained intent, never retry by label",
    )
    startup(env)
    if parent["backend"] == "herdr":
        confirmed, _ = current_herdr_tab(client, ancestors())
        require(confirmed == pane, "Dispatcher moved before Aven tab creation")
    record["creation_attempted"] = True
    persist(record)
    if parent["backend"] == "herdr":
        result = client.request(
            "layout.apply",
            workspace_id=parent["workspace_id"],
            tab_label="aven",
            focus=False,
            root={"type": "pane", "cwd": str(repo), "command": argv},
        )
        tab = result.get("tab", result.get("layout", {}))["tab_id"]
        record["created_tab_id"] = tab
        persist(record)
        matches = [p for p in client.snapshot()["panes"] if p["tab_id"] == tab]
        require(len(matches) == 1, "Cannot identify newly created Aven pane")
        record["aven_tab"] = {
            k: matches[0][k]
            for k in ("pane_id", "terminal_id", "tab_id", "workspace_id")
        }
    else:
        row = tmux(
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{window_id}\t#{pane_id}",
            "-t",
            parent["session"] + ":",
            "-n",
            "aven",
            "-c",
            str(repo),
            "exec " + shlex.join(argv),
        ).split("\t")
        require(
            len(row) == 2
            and re.fullmatch(r"@\d+", row[0])
            and re.fullmatch(r"%\d+", row[1]),
            "Missing created Aven tmux identity",
        )
        record["aven_tab"] = dict(tab_id=row[0], pane_id=row[1])
    persist(record)
    verify()
    return record


def close_aven_tab(record, persist):
    """Close only the saved run tab, after the dispatcher authorizes run closure."""
    parent, saved = record["dispatcher"], record["aven_tab"]
    require(
        saved["tab_id"] != parent["tab_id"] and saved["pane_id"] != parent["pane_id"],
        "Aven tab overlaps dispatcher",
    )
    endpoint = parent["endpoint"]

    def check_socket():
        stat = os.stat(endpoint)
        require(
            [stat.st_dev, stat.st_ino] == parent["socket_identity"],
            "Saved UI socket changed; preserve the Aven tab",
        )

    check_socket()
    if parent["backend"] == "herdr":
        client = Herdr(endpoint)

        def inventory():
            check_socket()
            data = client.snapshot()
            panes = [
                p
                for p in data["panes"]
                if p["tab_id"] == saved["tab_id"]
                or p["pane_id"] == saved["pane_id"]
                or p["terminal_id"] == saved["terminal_id"]
            ]
            tabs = [t for t in data["tabs"] if t["tab_id"] == saved["tab_id"]]
            if not panes and not tabs:
                return False
            require(len(panes) == 1, "Aven tab contains other panes; preserve them")
            require(
                all(panes[0].get(k) == v for k, v in saved.items()),
                "Saved Aven pane identity changed",
            )
            require(
                len(tabs) == 1
                and tabs[0]["workspace_id"]
                == saved["workspace_id"]
                == parent["workspace_id"],
                "Saved Aven tab identity changed",
            )
            return True

        def close():
            check_socket()
            client.request("tab.close", tab_id=saved["tab_id"])
    else:
        require(parent["backend"] == "tmux", "Unsupported saved UI backend")
        require(
            re.fullmatch(r"@\d+", saved["tab_id"])
            and re.fullmatch(r"%\d+", saved["pane_id"])
            and re.fullmatch(r"\$\d+", parent["session"]),
            "Invalid saved tmux identity",
        )

        def tmux(*args):
            check_socket()
            return command(["tmux", "-S", endpoint, *args])

        def inventory():
            rows = tmux(
                "list-panes", "-a", "-F", "#{pane_id}\t#{window_id}\t#{session_id}"
            ).splitlines()
            panes = [row.split("\t") for row in rows]
            matches = [
                p
                for p in panes
                if len(p) == 3 and (p[0] == saved["pane_id"] or p[1] == saved["tab_id"])
            ]
            if not matches:
                return False
            require(
                matches == [[saved["pane_id"], saved["tab_id"], parent["session"]]],
                "Saved Aven tmux identity changed or tab contains other panes",
            )
            return True

        def close():
            # Remove only the saved pane, never a window with unrelated panes.
            tmux("kill-pane", "-t", saved["pane_id"])

    present = inventory()
    if not present:
        require(
            record.get("aven_close_attempted"),
            "Saved Aven tab disappeared before authorized closure",
        )
    else:
        require(
            not record.get("aven_closed"),
            "Closed Aven identity reappeared; preserve it",
        )
        require(inventory(), "Aven tab disappeared before closure")
        record["aven_close_attempted"] = True
        persist(record)
        close()
        require(not inventory(), "Aven tab closure not confirmed")
    record["aven_closed"] = True
    persist(record)
    return record


def worker_tab(ui, saved=None):
    """Resolve the exact worker tab identity without changing its label.

    Workmux Herdr pane keys are server-lifetime~terminal_id, not native pane IDs.
    Labels are display data, never selectors.
    """
    require(len(ui["agents"]) == 1, "Expected one exact worker UI identity")
    pane = ui["agents"][0]["pane_id"]
    context = ui["context"]
    if context["backend"] == "herdr":
        endpoint = context["instance"]
        client = Herdr(endpoint)
        boot, separator, terminal = pane.partition("~")
        require(
            boot and separator and terminal, "Expected verified Workmux Herdr pane key"
        )

        def resolve():
            inventory = client.snapshot()
            panes = [p for p in inventory["panes"] if p["terminal_id"] == terminal]
            require(len(panes) == 1, "Missing or ambiguous worker terminal identity")
            p = panes[0]
            tabs = [
                t
                for t in inventory["tabs"]
                if t["tab_id"] == p["tab_id"] and t["workspace_id"] == p["workspace_id"]
            ]
            require(len(tabs) == 1, "Missing or ambiguous worker tab identity")
            identity = {
                key: p[key]
                for key in ("pane_id", "terminal_id", "tab_id", "workspace_id")
            }
            require(
                all(isinstance(v, str) and v for v in identity.values()),
                "Missing worker pane identity",
            )
            identity.update(
                backend="herdr",
                endpoint=endpoint,
                socket_identity=list(client.identity),
                workmux_pane=pane,
            )
            return identity, tabs[0]["label"]

        identity, label = resolve()
        require(saved is None or identity == saved, "Saved worker tab identity changed")
        return identity
    require(context["backend"] == "tmux", "Unsupported worker UI backend")
    require(re.fullmatch(r"%\d+", pane), "Invalid worker tmux pane")
    endpoint = context["instance"]
    require(
        isinstance(endpoint, str) and Path(endpoint).is_absolute(),
        "Missing exact worker tmux socket",
    )

    def tmux(*argv):
        return command(["tmux", "-S", endpoint, *argv])

    def resolve():
        row = tmux(
            "display-message",
            "-p",
            "-t",
            pane,
            "#{pane_id}\t#{window_id}\t#{session_id}",
        ).split("\t")
        require(
            len(row) == 3
            and row[0] == pane
            and re.fullmatch(r"@\d+", row[1])
            and row[2] == ui["agents"][0]["session"],
            "Cannot resolve exact worker tmux window",
        )
        return dict(
            backend="tmux",
            endpoint=endpoint,
            pane_id=pane,
            tab_id=row[1],
            session=row[2],
        )

    identity = resolve()
    require(saved is None or identity == saved, "Saved worker tab identity changed")
    return identity
