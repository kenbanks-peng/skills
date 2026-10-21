#!/usr/bin/env python3
"""Verify Aven and open the project tab once for a dispatch run."""

import argparse
import fcntl
import json
import re
import shutil
from pathlib import Path

from dispatch import ERRORS, error_text, save
from dispatch_ui import aven_tab
from git_preflight import paths, require
from worker_runtime import emit, run


def startup_run(args):
    """Check Aven availability from the same Git root used by the UI."""
    require(shutil.which("aven"), "aven is missing from PATH; no UI tabs were changed")
    require(re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id or args.task), "Invalid run ID")
    identity = paths(Path.cwd())
    repo, common = identity["worktree"], Path(identity["common_dir"])
    with (common / "dispatch.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError(
                "Another dispatch operation owns this repository"
            ) from error
        directory = common / "dispatch-ui"
        directory.mkdir(exist_ok=True)
        path = directory / ((args.run_id or args.task) + ".json")
        if path.exists():
            record = json.loads(path.read_text())
            require(
                record["repo"] == repo and record["task"] == args.task,
                "Saved dispatch run belongs to another repository/task",
            )

        else:
            # doctor opens read-only, unlike commands that may initialize a missing DB.
            doctor = json.loads(run(["aven", "doctor", "--json"], repo))
            rows = {
                row["code"]: row
                for section in doctor["sections"]
                for row in section["rows"]
            }
            db = Path(rows["database.path"]["value"]).expanduser().resolve(strict=True)
            require(
                db.is_file() and rows["database.open"]["status"] == "ok",
                "Aven database unavailable; refusing to initialize a new database",
            )
            context = json.loads(run(["aven", "context", args.task, "--json"], repo))
            routing = dict(
                db=str(db),
                workspace=context["workspace"]["key"],
                project=context["project"]["key"],
            )
            require(
                all(isinstance(v, str) and v for v in routing.values()),
                "Missing Aven database/workspace/project routing",
            )
            record = dict(
                schema_version=1,
                repo=repo,
                task=args.task,
                routing=routing,
                task_id=context["task"]["id"],
                task_ref=context["task"]["display_ref"],
                prior_note_ids=[note["id"] for note in context["notes"]],
            )
            save(path, record)
        routing = record["routing"]
        require(Path(routing["db"]).is_file(), "Saved Aven database is missing")
        argv = [shutil.which("aven"), "tui", "--project", routing["project"]]
        record["argv"] = argv
        aven_tab(repo, argv, record, lambda data: save(path, data))
        record["ok"] = True
        save(path, record)
        return dict(record, ok=True, record_path=str(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", help="Aven task for final run reporting")
    parser.add_argument("--run-id", help="Stable run identity (default: task ref)")
    args = parser.parse_args()
    try:
        return emit(startup_run(args))
    except ERRORS as error:
        return emit(
            {
                "ok": False,
                "error": error_text(error),
                "next_action": "Inspect retained startup records and UI identity",
            }
        )


if __name__ == "__main__":
    raise SystemExit(main())
