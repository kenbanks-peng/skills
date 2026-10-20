#!/usr/bin/env python3
"""Launch or inspect one worker; derive and save all launch coordinates."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

from dispatch_ui import aven_tab, worker_tab
from git_preflight import (
    CheckError,
    branch_ref,
    commit,
    git,
    normal_index,
    operations,
    paths,
    require,
)
from worker_prompt import render
from worker_runtime import canonical, container_ids, emit, inspect, run, worker_path

ERRORS = (ValueError, OSError, KeyError, TypeError, CheckError)


def error_text(error):
    if isinstance(error, (KeyError, TypeError, json.JSONDecodeError)):
        return (
            "Unexpected CLI/record schema: "
            + str(error)
            + ". Inspect the retained response and use explicit compatibility troubleshooting."
        )
    return str(error)


def save(path, data):
    """Replace one record atomically; never expose a half-written JSON record."""
    fd, temporary = tempfile.mkstemp(prefix=".record-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(data, output, indent=2, ensure_ascii=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aven_context_command(args, task_ref, *, machine=False):
    argv = ["aven", "context", task_ref]
    if machine:
        argv.append("--json")
    for flag in ("db", "workspace"):
        value = getattr(args, flag)
        if value:
            argv.extend(["--" + flag, value])
    return argv


def aven_context(args, repo):
    # Keep structured validation/recovery separate from the worker-facing CLI text.
    context = json.loads(run(aven_context_command(args, args.task, machine=True), repo))
    ref = context["task"]["display_ref"]
    require(
        bool(re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", ref)),
        "Unexpected task reference schema; use compatibility troubleshooting",
    )
    return context


def multiplexer(repo):
    if os.environ.get("HERDR_ENV") == "1":
        return {"backend": "herdr"}, None
    if os.environ.get("TMUX"):
        session = run(["tmux", "display-message", "-p", "#{session_id}"], repo).strip()
        require(bool(session), "Cannot identify the original tmux session")
        return {"backend": "tmux", "session": session}, session
    raise ValueError("Launch needs the original Herdr or tmux context")


def validate_assignment(args):
    require(args.base is not None, "A new launch requires --base")
    require(bool(args.scope), "A new launch requires --scope")
    for scope in args.scope:
        require(
            not Path(scope).is_absolute()
            and ".." not in Path(scope).parts
            and bool(scope.strip()),
            "Use repository-relative write scopes",
        )
    require(bool(args.check), "A new launch requires at least one --check JSON argv")
    checks = [json.loads(value) for value in args.check]
    require(
        all(
            isinstance(check, list)
            and check
            and all(isinstance(arg, str) and arg for arg in check)
            for check in checks
        ),
        "--check must be a nonempty JSON argv array",
    )
    return checks


def create_record(args, identity, context, directory):
    repo = identity["worktree"]
    checks = validate_assignment(args)
    require(
        not context.get("is_blocked") and not context.get("has_conflicts"),
        "Aven task has blocked dependencies or conflicts",
    )
    require(
        context["task"]["status"] != "done" and not context["task"]["deleted"],
        "Cannot launch a done or deleted task",
    )
    base_ref = branch_ref(repo, args.base)
    normal_index(repo)
    require(not operations(repo), "Repository has an unfinished Git operation")
    ref = context["task"]["display_ref"]
    handle = "dispatch-" + ref.lower()
    branch = "dispatch/" + ref.lower()
    require(
        git(
            repo,
            "show-ref",
            "--verify",
            "--quiet",
            "refs/heads/" + branch,
            allowed=(0, 1),
        ).returncode
        != 0,
        "Worker branch already exists without a saved record; reconcile ownership",
    )
    runtime = args.runtime or (
        "apple-container" if sys.platform == "darwin" else "docker"
    )
    require(
        args.allow_local or runtime != "local",
        "Local/macOS execution requires --allow-local approval",
    )
    if runtime == "local":
        require(
            args.config or sys.platform == "darwin",
            "Local execution on Linux requires an explicit sandbox-disabled --config",
        )
        default_config = "~/.config/workmux/agents.macos.yaml"
    else:
        default_config = "~/.config/workmux/agents.linux.yaml"
    config = Path(args.config or default_config).expanduser().resolve(strict=True)
    require(
        args.allow_local or "macos" not in config.name.lower(),
        "Local/macOS execution requires --allow-local approval",
    )
    origin, parent = multiplexer(repo)
    return {
        "schema_version": 1,
        "ok": False,
        "repo": repo,
        "common_dir": identity["common_dir"],
        "task_ref": ref,
        "task_id": context["task"]["id"],
        "task_context": context,
        "task_context_text": run(aven_context_command(args, ref), repo),
        "base": args.base,
        "launch_base": commit(repo, base_ref),
        "branch": branch,
        "handle": handle,
        "config": str(config),
        "config_sha256": digest(config),
        "runtime": runtime,
        "local_approved": args.allow_local,
        "origin": origin,
        "parent_session": parent,
        "write_scope": args.scope,
        "acceptance_checks": checks,
        "routing": {
            key: getattr(args, key) for key in ("db", "workspace") if getattr(args, key)
        },
        "record_path": str(directory / "worker.json"),
        "events": [],
        "next_action": "launch",
    }


def ui_identity(ui):
    """Window labels may drift; pane, session and server identity may not."""
    return {**ui, "agents": [
        {key: value for key, value in agent.items() if key != "window_name"}
        for agent in ui["agents"]
    ]}


def record_worker_tab(record, event, path):
    identity = worker_tab(record["ui"], record.get("worker_tab"))
    record["worker_tab"] = identity
    save(path, record)
    event["worker_tab"] = identity


def observe(record, event, directory, archive_prompts=True):
    """Retain raw observations before validation, including ambiguous identities."""
    repo, handle = record["repo"], record["handle"]
    rows = json.loads(run(["workmux", "list", "--json", handle], repo))
    event["workmux_list"] = rows
    matches = [row for row in rows if row["handle"] == handle and not row["is_main"]]
    require(len(matches) == 1, "Expected one non-primary Workmux worktree")
    row = matches[0]
    require(row["branch"] == record["branch"], "Observed worker branch mismatch")
    worktree = canonical(row["path"])
    require(
        paths(worktree)["common_dir"] == record["common_dir"],
        "Observed worker belongs to a different repository",
    )
    require(
        git(worktree, "symbolic-ref", "-q", "HEAD").stdout.strip()
        == "refs/heads/" + record["branch"],
        "Worker HEAD identity mismatch",
    )
    event["worktree"] = str(worktree)
    require(
        not directory.is_relative_to(worktree),
        "Evidence directory must be outside the worker worktree",
    )

    # Copy generated prompts before checking UI/runtime, which can already have exited.
    event["prompts"] = []
    prompt_dir = worktree / ".workmux"
    require(not prompt_dir.is_symlink(), "Generated prompt directory is a symlink")
    for path in sorted(prompt_dir.glob("PROMPT-*.md")):
        require(not path.is_symlink() and path.is_file(), "Invalid generated prompt")
        sha = digest(path)
        archive = directory / ("prompt-" + sha + ".md")
        if archive_prompts:
            if not archive.exists():
                archive.write_bytes(path.read_bytes())
            require(digest(archive) == sha, "Archived prompt hash mismatch")
        event["prompts"].append(
            {
                "path": str(path.relative_to(worktree)),
                "sha256": sha,
                "archive_path": str(archive),
            }
        )
    # UI and container queries are independent. Retain either even if the other fails.
    status = None
    try:
        status = json.loads(run(["workmux", "status", "--json", handle], repo))
        event["workmux_status"] = status
    except ERRORS as error:
        event["status_error"] = error_text(error)
    if record["runtime"] != "local":
        event["containers"] = []
        try:
            event["container_ids"] = container_ids(record["runtime"])
            for identity in event["container_ids"]:
                event["containers"].append(inspect(record["runtime"], identity))
        except ERRORS as error:
            event["container_error"] = error_text(error)
    require(
        status is not None, "Cannot observe worker UI: " + event.get("status_error", "")
    )
    agents = [
        agent
        for agent in status["agents"]
        if agent["worktree"] == handle and agent["project_path"] == repo
    ]
    require(
        not status.get("target_errors") and len(agents) == 1,
        "Expected one exact worker UI/agent identity",
    )
    agent = agents[0]
    require(
        bool(agent["pane_id"]),
        "Worker pane unavailable",
    )
    require(
        status["context"]["backend"] == record["origin"]["backend"],
        "Worker multiplexer context mismatch",
    )
    require(
        agent["status"] in ("working", "waiting", "done"),
        "Startup unconfirmed; inspect the observed worker status",
    )
    event["ui"] = {
        "context": status["context"],
        "agents": [
            {
                key: agent.get(key)
                for key in (
                    "pane_id",
                    "session",
                    "window_name",
                    "agent_kind",
                    "workdir",
                )
            }
        ],
    }
    event["agent_type"] = agent["agent_kind"]
    if record["runtime"] == "local":
        require(bool(event["agent_type"]), "Actual local agent type unavailable")
        require(
            agent.get("workdir") == str(worktree),
            "Local worker root must be observed in UI status; check runtime/config",
        )
        event.update(container=None, worker_worktree=agent["workdir"])
    else:
        require(
            "container_error" not in event,
            "Container observation incomplete: " + event.get("container_error", ""),
        )
        matches = []
        for container in event["containers"]:
            try:
                guest = worker_path(container, worktree)
            except ValueError:
                continue
            if container["status"] in ("running", "exited", "stopped"):
                matches.append((container, guest))
        require(len(matches) == 1, "Expected one container with the exact worker mount")
        event["container"], event["worker_worktree"] = matches[0]
        if not event["agent_type"]:
            require(
                event["container"]["status"] == "running",
                "No live agent process evidence",
            )
            binary = (
                "container"
                if record["runtime"] == "apple-container"
                else record["runtime"]
            )
            probe = Path(__file__).with_name("agent_processes.py").read_text()
            event["agent_processes"] = json.loads(
                run(
                    [
                        binary,
                        "exec",
                        event["container"]["id"],
                        "python3",
                        "-c",
                        probe,
                        event["worker_worktree"],
                    ],
                    repo,
                )
            )
            processes = event["agent_processes"]
            require(
                isinstance(processes, list)
                and len(processes) == 1
                and processes[0]["cwd"] == event["worker_worktree"]
                and processes[0]["kind"] == "pi"
                and isinstance(processes[0]["pid"], int)
                and processes[0]["pid"] > 0
                and bool(processes[0]["start_ticks"]),
                "Expected one actual agent process in the exact worker root",
            )
            event["agent_type"] = processes[0]["kind"]
    event["ui"]["agents"][0]["agent_kind"] = event["agent_type"]
    require(
        git(
            repo,
            "merge-base",
            "--is-ancestor",
            record["launch_base"],
            "refs/heads/" + record["branch"],
            allowed=(0, 1),
        ).returncode
        == 0,
        "Worker no longer contains the launch revision",
    )
    for key in ("worktree", "worker_worktree", "ui", "agent_type"):
        if key in record:
            require(
                (ui_identity(record[key]) == ui_identity(event[key])
                 if key == "ui" else record[key] == event[key]),
                "Saved " + key + " identity changed; reconcile before continuing",
            )
    if record.get("container"):
        require(
            record["container"]["id"] == event["container"]["id"]
            and record["container"]["mounts"] == event["container"]["mounts"],
            "Saved container identity changed; reconcile before continuing",
        )
    # Workmux received a pinned SHA; retain the explicit local integration base
    # on the first confirmed observation, including recovery of a partial launch.
    # A read-only inspect never changes Git metadata.
    if "worktree" not in record and archive_prompts:
        git(
            repo,
            "config",
            "--local",
            "branch." + record["branch"] + ".workmux-base",
            record["base"],
        )
    for key in (
        "worktree",
        "worker_worktree",
        "ui",
        "container",
        "agent_type",
        "prompts",
    ):
        record[key] = event[key]


def startup_run(args):
    """Resolve routing in the caller's directory before moving the UI to Git root."""
    require(shutil.which("aven"), "aven is missing from PATH; no UI tabs were changed")
    require(re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id or args.task), "Invalid run ID")
    identity = paths(Path.cwd())
    repo, common = identity["worktree"], Path(identity["common_dir"])
    with (common / "dispatch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("Another dispatch operation owns this repository") from error
        directory = common / "dispatch-ui"
        directory.mkdir(exist_ok=True)
        path = directory / ((args.run_id or args.task) + ".json")
        if path.exists():
            record = json.loads(path.read_text())
            require(record["repo"] == repo and record["task"] == args.task,
                    "Saved dispatch run belongs to another repository/task")
            for flag in ("db", "workspace"):
                value = getattr(args, flag)
                require(value is None or value == record["routing"][flag],
                        "Routing override differs from saved " + flag)
        else:
            flags = []
            for flag in ("db", "workspace"):
                value = getattr(args, flag)
                if value:
                    flags.extend(["--" + flag, value])
            # doctor opens read-only, unlike commands that may initialize a missing DB.
            doctor = json.loads(run(["aven", "doctor", "--json", *flags], Path.cwd()))
            rows = {row["code"]: row for section in doctor["sections"]
                    for row in section["rows"]}
            db = Path(rows["database.path"]["value"]).expanduser().resolve(strict=True)
            require(db.is_file() and rows["database.open"]["status"] == "ok",
                    "Aven database unavailable; refusing to initialize a new database")
            context_flags = ["--workspace", args.workspace] if args.workspace else []
            context = json.loads(run(["aven", "context", args.task, "--json",
                                      "--db", str(db), *context_flags], Path.cwd()))
            routing = dict(db=str(db), workspace=context["workspace"]["key"],
                           project=context["project"]["key"])
            require(all(isinstance(v, str) and v for v in routing.values()),
                    "Missing Aven database/workspace/project routing")
            record = dict(schema_version=1, repo=repo, task=args.task, routing=routing)
            save(path, record)
        routing = record["routing"]
        require(Path(routing["db"]).is_file(), "Saved Aven database is missing")
        argv = [shutil.which("aven"), "tui", "--db", routing["db"],
                "--workspace", routing["workspace"], "--project", routing["project"]]
        record["argv"] = argv
        aven_tab(repo, argv, record, lambda data: save(path, data))
        return dict(record, ok=True, record_path=str(path))


def execute(args):
    identity = paths(Path.cwd())
    repo = identity["worktree"]
    common = Path(identity["common_dir"])
    # One lock for all launch records, including linked dispatcher worktrees.
    with (common / "dispatch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(
                "Another dispatch operation owns this repository; retry after it exits"
            ) from error
        # Full references also locate saved routing without another caller input.
        if re.fullmatch(r"[A-Za-z0-9]+-[A-Za-z0-9]+", args.task):
            previous = common / "dispatch-workers" / args.task / "worker.json"
            if previous.exists():
                routing = json.loads(previous.read_text())["routing"]
                for flag in ("db", "workspace"):
                    if getattr(args, flag) is None and flag in routing:
                        setattr(args, flag, routing[flag])
        context = aven_context(args, repo)
        directory = common / "dispatch-workers" / context["task"]["display_ref"]
        path = directory / "worker.json"
        existing = path.exists()
        if existing:
            record = json.loads(path.read_text())
            require(
                record["schema_version"] == 1
                and record["repo"] == repo
                and record["common_dir"] == str(common)
                and record["task_id"] == context["task"]["id"],
                "Saved worker record identity mismatch",
            )
            for option, field in (
                ("base", "base"),
                ("scope", "write_scope"),
                ("runtime", "runtime"),
                ("db", "routing"),
                ("workspace", "routing"),
            ):
                value = getattr(args, option)
                if value:
                    saved = (
                        record[field].get(option)
                        if field == "routing"
                        else record[field]
                    )
                    require(
                        value == saved,
                        "Assignment override differs from saved " + option,
                    )
            if args.config:
                require(
                    str(Path(args.config).expanduser().resolve()) == record["config"],
                    "Config override differs from saved config",
                )
            if args.check:
                require(
                    [json.loads(value) for value in args.check]
                    == record["acceptance_checks"],
                    "Required checks differ from saved assignment",
                )
            if args.command == "inspect" and not args.resume:
                event = {"action": "inspect", "ok": False}
                try:
                    observe(record, event, directory, archive_prompts=False)
                    event["ok"] = True
                except ERRORS as error:
                    event["error"] = error_text(error)
                record["inspection"] = event
                record["ok"] = event["ok"]
                return record
        else:
            require(
                args.command == "launch",
                "No saved worker record; inspect cannot create a worker",
            )
            record = create_record(args, identity, context, directory)
            directory.mkdir(parents=True, exist_ok=True)
            prompt = directory / "assignment.md"
            with prompt.open("x", encoding="utf-8") as output:
                output.write(render(record))
            snapshot = directory / "config.yaml"
            snapshot.write_bytes(Path(record["config"]).read_bytes())
            require(
                digest(snapshot) == record["config_sha256"],
                "Selected config changed during preparation",
            )
            record["config_snapshot"] = str(snapshot)
            record["prompt"] = str(prompt)
            record["prompt_sha256"] = digest(prompt)
            # Save intent before any external mutation. An interrupted launch is never repeated.
            save(path, record)
        event = {"action": "observe" if existing else "launch", "ok": False}
        record["events"].append(event)
        record.update(
            ok=False, last_action=event["action"], next_action="inspect/resume"
        )
        save(path, record)
        try:
            if not existing:
                require(
                    commit(repo, branch_ref(repo, record["base"]))
                    == record["launch_base"],
                    "Base moved since prompt creation; no worker was started",
                )
                # A pre-existing Workmux resource is ownership evidence, not permission to add.
                rows = json.loads(run(["workmux", "list", "--json"], repo))
                event["before_list"] = rows
                require(
                    not any(
                        row["handle"] == record["handle"]
                        or row["branch"] == record["branch"]
                        for row in rows
                    ),
                    "Existing Workmux identity; reconcile ownership",
                )
                require(
                    commit(repo, branch_ref(repo, record["base"]))
                    == record["launch_base"],
                    "Base moved since prompt creation; no worker was started",
                )
                save(path, record)
                argv = [
                    "workmux",
                    "add",
                    record["branch"],
                    "--base",
                    record["launch_base"],
                    "--name",
                    record["handle"],
                    "--target-name",
                    record["task_ref"],
                    "-b",
                    "-P",
                    record["prompt"],
                    "--config",
                    record["config"],
                ]
                if record["runtime"] != "local":
                    argv.append("--sandbox")
                if record["parent_session"]:
                    argv.extend(["--parent-session", record["parent_session"]])
                require(
                    digest(Path(record["config"])) == record["config_sha256"],
                    "Selected config changed before creation",
                )
                event["argv"] = argv
                record["creation_attempted"] = True
                save(path, record)
                try:
                    event["launch_output"] = run(argv, repo, timeout=args.timeout)
                except ERRORS as error:
                    event["launch_error"] = error_text(error)
                    raise
                try:
                    event["wait_output"] = run(
                        [
                            "workmux",
                            "wait",
                            record["handle"],
                            "--status",
                            "working",
                            "--timeout",
                            str(args.timeout),
                        ],
                        repo,
                        timeout=args.timeout + 15,
                    )
                except ERRORS as error:
                    # A worker can finish before wait starts. Observed state decides.
                    event["wait_error"] = error_text(error)
            require(
                record.get("creation_attempted"),
                "Creation was never attempted; reconcile the retained assignment",
            )
            observe(record, event, directory)
            record_worker_tab(record, event, path)
            if "wait_error" in event:
                require(
                    not any(
                        word in event["wait_error"].lower()
                        for word in (
                            "unknown",
                            "unexpected",
                            "unrecognized",
                            "unsupported",
                            "invalid value",
                        )
                    ),
                    "Unsupported Workmux wait command/flag/schema; use explicit compatibility troubleshooting",
                )
            if not existing:
                require(
                    digest(Path(record["config"])) == record["config_sha256"],
                    "Selected config changed during launch; inspect retained resources",
                )
            event["ok"] = True
            record.update(ok=True, next_action="review/monitor")
        except ERRORS as error:
            event["error"] = error_text(error)
            if "launch_error" in event:
                try:
                    observe(record, event, directory)
                    record_worker_tab(record, event, path)
                except ERRORS as observation_error:
                    event["observation_error"] = error_text(observation_error)
            record["error"] = error_text(error)
        else:
            record.pop("error", None)
        finally:
            save(path, record)
        return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("startup", "launch", "inspect"))
    parser.add_argument("--run-id", help="Stable startup run identity; defaults to the designated task ref")
    parser.add_argument("task", help="Aven task ref; configured routing defaults apply")
    parser.add_argument("--base", help="Explicit local base branch (new launch)")
    parser.add_argument(
        "--scope", action="append", help="Repository-relative write scope"
    )
    parser.add_argument(
        "--check", action="append", help="Required check as a JSON argv array"
    )
    parser.add_argument("--config", help="Genuine Workmux config override")
    parser.add_argument(
        "--runtime", choices=("apple-container", "docker", "podman", "local")
    )
    parser.add_argument(
        "--allow-local",
        action="store_true",
        help="Explicit approval for local/macOS execution",
    )
    parser.add_argument("--db", help="Diagnosed Aven routing override")
    parser.add_argument("--workspace", help="Diagnosed Aven routing override")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reconcile observations only; never add/open a replacement",
    )
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        return emit(startup_run(args) if args.command == "startup" else execute(args))
    except ERRORS as error:
        return emit(
            {
                "ok": False,
                "error": error_text(error),
                "next_action": "Inspect retained records; use compatibility troubleshooting only for unsupported CLI/schema behavior",
            }
        )


if __name__ == "__main__":
    raise SystemExit(main())
