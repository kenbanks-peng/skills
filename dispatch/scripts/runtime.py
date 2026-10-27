"""Shared, windowless process and evidence operations for dispatch scripts."""

import contextlib
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import time
import uuid
from pathlib import Path


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


@contextlib.contextmanager
def lock(directory):
    with (Path(directory) / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("another script owns this run directory") from None
        yield


def environment():
    return {
        **os.environ,
        "GIT_PAGER": "cat",
        "PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    }


def capture(argv, cwd=None, timeout=30, extra_env=None):
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            env={**environment(), **(extra_env or {})},
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ValueError(
            f"{argv[0]} timed out; reconcile effects before retry"
        ) from None
    if result.returncode:
        raise ValueError(
            f"{argv[0]} exited {result.returncode}: "
            + (result.stderr + result.stdout[-8192:]).decode(errors="replace").strip()
        )
    return result.stdout


def git(cwd, *args):
    return capture(["git", "--no-pager", *args], cwd=cwd)


def identity(cwd):
    """Read commit and content identity without changing the index."""
    root = Path(git(cwd, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    head = git(root, "rev-parse", "HEAD").decode().strip()
    status = git(root, "status", "--porcelain=v1", "-z")
    digest = hashlib.sha256()
    digest.update(head.encode() + b"\0" + status)
    digest.update(
        git(root, "diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD", "--")
    )
    for raw in sorted(
        git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    ):
        if not raw:
            continue
        path = root / os.fsdecode(raw)
        digest.update(raw + b"\0")
        if path.is_symlink():
            digest.update(b"link\0" + os.fsencode(os.readlink(path)))
        else:
            digest.update(str(path.stat().st_mode).encode() + b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
        digest.update(b"\0")
    return {
        "root": str(root),
        "head": head,
        "branch": git(root, "branch", "--show-current").decode().strip(),
        "fingerprint": digest.hexdigest(),
        "dirty": bool(status),
    }


def outside(directory, root):
    if Path(directory).resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("evidence directory must be outside the checkout")


def full_id(value):
    try:
        if str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError):
        raise ValueError("expected a full lowercase window UUID") from None
    return value


class Native:
    def __init__(self, server):
        if (
            not isinstance(server, str)
            or len(server) > 14
            or any(
                c
                not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
                for c in server
            )
        ):
            raise ValueError("invalid tuios server name")
        self.server = server

    def call(self, *args, json_output=True):
        route = ["--server", self.server] if self.server else []
        raw = capture(
            ["tuios", *route, *args],
            timeout=60,
            extra_env={"TUIOS_SERVER": self.server},
        )
        if not json_output:
            return raw.decode(errors="replace")
        value = json.loads(raw)
        if isinstance(value, dict) and value.get("success") is False:
            raise ValueError(f"tuios refused: {value}")
        return value

    def inventory(self):
        hosts = self.call("ls", "--all-hosts", "--json")
        if not isinstance(hosts, dict) or not isinstance(hosts.get("hosts"), list):
            raise ValueError("unsupported all-host session inventory")
        names = set()
        for host in hosts["hosts"]:
            if host.get("status") != "up":
                raise ValueError(f"host unavailable: {host.get('host', 'unknown')}")
            names.add(host["host"])
        panes = self.call("list-windows", "--all", "--all-hosts", "--json")
        if not isinstance(panes, dict) or not isinstance(panes.get("panes"), list):
            raise ValueError("unsupported all-host pane inventory")
        result = {}
        for pane in panes["panes"]:
            session = pane["session"]
            host = pane.get("host", "local")
            if ":" in session:
                prefix, session = session.split(":", 1)
                if host != "local" and host != prefix:
                    raise ValueError("conflicting pane host identities")
                host = prefix
            if host not in names:
                raise ValueError("pane host is absent from host inventory")
            address = session if host == "local" else f"{host}:{session}"
            window = full_id(pane["window_id"])
            key = address + "/" + window
            if key in result:
                raise ValueError("duplicate pane identity")
            result[key] = {
                **pane,
                "session": address,
                "window_id": window,
                "host": host,
            }
        return result

    def resting(self, session, window, require_agent=False):
        agents = self.call("list-agents", "-s", session, "--json")
        rows = agents.get("agents") if isinstance(agents, dict) else None
        if not isinstance(rows, list):
            raise ValueError("unsupported agent inventory")
        matches = [row for row in rows if row.get("window_id") == window]
        if len(matches) > 1:
            raise ValueError("duplicate agent identity")
        if require_agent and (not matches or matches[0].get("state") == "none"):
            raise ValueError("worker native state is missing")
        if matches and matches[0].get("state") not in {
            "idle",
            "done",
            "errored",
            "none",
        }:
            raise ValueError(
                "worker is not at rest; stop it safely before cleanup/delivery"
            )
        queues = self.call("queue", "ls", "-s", session, "-w", window, "--json")
        if not isinstance(queues, dict) or not isinstance(queues.get("entries"), list):
            raise ValueError("unsupported queue inventory")
        if queues["entries"]:
            raise ValueError(
                "worker has queued work; reconcile it before cleanup/delivery"
            )


def install_interrupts():
    def interrupt(signum, frame):
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, interrupt)


def execute(argv, cwd, log, timeout):
    """Run argv without a terminal; stop its process group on timeout or interrupt."""
    started = time.monotonic()
    with Path(log).open("wb") as stream:
        try:
            process = subprocess.Popen(
                argv,
                cwd=cwd,
                env=environment(),
                stdin=subprocess.DEVNULL,
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except OSError as error:
            stream.write(str(error).encode())
            return {"exit_code": None, "status": "launch_error", "elapsed_s": 0}
        status = "completed"
        try:
            process.wait(timeout=timeout)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            status = (
                "timeout"
                if isinstance(error, subprocess.TimeoutExpired)
                else "interrupted"
            )
        finally:
            # Also remove background children left by an otherwise completed command.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            if status != "completed":
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    return {
        "exit_code": process.returncode,
        "status": status,
        "elapsed_s": round(time.monotonic() - started, 3),
    }
