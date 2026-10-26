"""Close only saved worker UI identities; labels and ambient UI are never targets.

Herdr contract: workmux 84fd26da903939e15963ec334232793b5d98fc31,
src/multiplexer/herdr/{client,mod}.rs. Workmux pane keys encode the kernel
server lifetime plus terminal ID, NOT the native Herdr pane ID.
"""

import ctypes
import json
import os
import re
import socket
import struct
import sys
from pathlib import Path

from .runtime import run
from .ui import Herdr, require


def peer_lifetime(stream):
    if sys.platform == "linux":
        pid, uid, _ = struct.unpack(
            "3i", stream.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        )
        require(uid == os.geteuid(), "Herdr peer belongs to another user")
        start = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        return f"{pid}-{start}-{boot}"
    require(sys.platform == "darwin", "Unsupported Herdr peer platform")
    pid = struct.unpack("i", stream.getsockopt(0, 2, 4))[0]  # LOCAL_PEERPID

    class BSDInfo(ctypes.Structure):
        _fields_ = (
            [
                (name, ctypes.c_uint32)
                for name in (
                    "flags",
                    "status",
                    "xstatus",
                    "pid",
                    "ppid",
                    "uid",
                    "gid",
                    "ruid",
                    "rgid",
                    "svuid",
                    "svgid",
                    "rfu",
                )
            ]
            + [("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32)]
            + [
                (name, ctypes.c_uint32)
                for name in ("nfiles", "pgid", "pjobc", "e_tdev", "e_tpgid", "nice")
            ]
            + [("seconds", ctypes.c_uint64), ("micros", ctypes.c_uint64)]
        )

    info = BSDInfo()
    library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    size = ctypes.sizeof(info)
    require(
        library.proc_pidinfo(pid, 3, 0, ctypes.byref(info), size) == size,
        "Cannot verify Herdr peer lifetime",
    )
    require(info.uid == os.geteuid(), "Herdr peer belongs to another user")
    return f"{pid}-{info.seconds}-{info.micros}"


class SavedHerdr(Herdr):
    def __init__(self, endpoint, boot):
        super().__init__(endpoint)
        self.boot = boot

    def request(self, method, **params):
        # Check the kernel peer on EVERY connection, before sending a mutation.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
            stream.settimeout(8)
            stream.connect(self.endpoint)
            dev, ino = self.socket_identity()
            require(
                f"{dev}-{ino}-{peer_lifetime(stream)}" == self.boot,
                "Herdr server lifetime changed; preserve saved UI",
            )
            stream.sendall(
                json.dumps(
                    {"id": "dispatch-cleanup", "method": method, "params": params}
                ).encode()
                + b"\n"
            )
            with stream.makefile("rb") as response:
                line = response.readline(8 * 1024 * 1024 + 1)
        require(
            len(line) <= 8 * 1024 * 1024 and line.endswith(b"\n"),
            "Incomplete or oversized Herdr response",
        )
        data = json.loads(line)
        require(
            data.get("id") == "dispatch-cleanup" and "error" not in data,
            f"Herdr {method} failed: {data}",
        )
        require(isinstance(data.get("result"), dict), "Missing Herdr result")
        return data["result"]


def herdr_target(inventory, terminal, worker):
    matches = [p for p in inventory["panes"] if p["terminal_id"] == terminal]
    require(len(matches) == 1, "Saved Herdr terminal missing or ambiguous")
    pane = matches[0]
    require(pane["cwd"] == worker, "Herdr worker directory changed")
    target = {
        key: pane[key] for key in ("pane_id", "terminal_id", "tab_id", "workspace_id")
    }
    require(
        all(isinstance(value, str) and value for value in target.values()),
        "Incomplete Herdr identity",
    )
    tabs = [t for t in inventory["tabs"] if t["tab_id"] == pane["tab_id"]]
    require(
        len(tabs) == 1 and tabs[0]["workspace_id"] == pane["workspace_id"],
        "Herdr tab identity changed",
    )
    require(
        [p for p in inventory["panes"] if p["tab_id"] == pane["tab_id"]] == [pane],
        "Worker tab contains other panes; preserve them",
    )
    return target


def close_herdr(context, agent, worker, item, persist):
    key = agent["pane_id"]
    boot, separator, terminal = key.partition("~")
    require(
        separator and boot and terminal, "Missing lifetime-qualified Herdr terminal"
    )
    client = SavedHerdr(context.get("instance"), boot)
    inventory = client.snapshot()
    saved = item.get("target")
    if saved and item.get("close_attempted"):
        absent = not any(
            p["terminal_id"] == terminal
            or p["pane_id"] == saved["pane_id"]
            or p["tab_id"] == saved["tab_id"]
            for p in inventory["panes"]
        )
        absent = absent and not any(
            t["tab_id"] == saved["tab_id"] for t in inventory["tabs"]
        )
        if absent:
            return  # Reconcile a lost close response without another mutation.
    target = herdr_target(inventory, terminal, worker)
    require(not saved or saved == target, "Saved Herdr target moved or changed")
    item["target"] = target
    persist()
    require(
        herdr_target(client.snapshot(), terminal, worker) == target,
        "Herdr identity changed before closure",
    )
    item["close_attempted"] = True
    persist()
    client.request("tab.close", tab_id=target["tab_id"])
    after = client.snapshot()
    require(
        not any(t["tab_id"] == target["tab_id"] for t in after["tabs"])
        and not any(
            p["terminal_id"] == terminal or p["tab_id"] == target["tab_id"]
            for p in after["panes"]
        ),
        "Herdr closure not confirmed",
    )


def close_tmux(context, agent, worker, item, persist):
    pane, session = agent["pane_id"], agent["session"]
    endpoint = context.get("socket_path") or context.get("instance")
    require(
        endpoint and Path(endpoint).is_absolute(), "Original tmux socket unavailable"
    )
    require(
        re.fullmatch(r"%\d+", pane) and re.fullmatch(r"\$\d+", session),
        "Invalid saved tmux identity",
    )
    prefix = ["tmux", "-S", endpoint]
    if item.get("close_attempted"):
        remaining = run([*prefix, "list-panes", "-a", "-F", "#{pane_id}"]).splitlines()
        if pane not in remaining:
            return
    actual = run(
        [
            *prefix,
            "display-message",
            "-p",
            "-t",
            pane,
            "#{socket_path}\t#{pane_id}\t#{session_id}\t#{pane_current_path}",
        ]
    ).strip()
    require(
        actual == "\t".join((endpoint, pane, session, worker)), "UI identity changed"
    )
    # Only remove the assigned pane; never kill a window containing other panes.
    item["close_attempted"] = True
    persist()
    run([*prefix, "kill-pane", "-t", pane])
    remaining = run([*prefix, "list-panes", "-a", "-F", "#{pane_id}"]).splitlines()
    require(pane not in remaining, "tmux closure not confirmed")


def close_worker_ui(context, agent, worker, item, persist):
    backend = context.get("backend")
    require(backend in ("herdr", "tmux"), "Unsupported saved UI backend")
    if backend == "herdr":
        close_herdr(context, agent, worker, item, persist)
    else:
        close_tmux(context, agent, worker, item, persist)
