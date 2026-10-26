#!/usr/bin/env python3
"""Dispatch lifecycle: startup, launch, inspect/resume, report, integrate, finish, close-run."""

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from dispatch_lib import (
    archive,
    cleanup,
    finish,
    git,
    integration,
    launch,
    output,
    recovery,
    reports,
    startup,
    stop,
    verification,
)


def configure_git(parser):
    parser.add_argument(
        "--repo", required=True, help="Existing repository checkout path"
    )
    parser.add_argument(
        "--worker-worktree", required=True, help="Exact registered worker worktree root"
    )
    parser.add_argument(
        "--worker-branch", required=True, help="Expected local worker branch name"
    )
    parser.add_argument(
        "--base", required=True, help="Explicit local base branch name (no default)"
    )


def configure_integration(parser):
    parser.add_argument("task")
    parser.add_argument("--reviewed-commit")
    parser.add_argument("--result-id", help="ID of the latest reviewed RESULT note")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--reconcile",
        action="store_true",
        help="Observe an attempted merge and rerun checks; never merge again",
    )
    mode.add_argument(
        "--new-attempt",
        action="store_true",
        help="Explicit new review after repair of a pre-merge failure",
    )
    mode.add_argument(
        "--closure",
        action="store_true",
        help="Read-only rejection of base movement before task closure",
    )
    parser.add_argument("--timeout", type=float, default=300)


def configure_finish(parser):
    parser.add_argument("task")
    parser.add_argument(
        "--inspect", action="store_true", help="Observe without mutation"
    )


def configure_stop(parser):
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--previous",
        help="Matching prior stop JSON for rechecking auto-removed containers",
    )
    parser.add_argument("--timeout", type=int, default=30)


def configure_archive(parser):
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--stop-evidence", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--execute", action="store_true")


def configure_cleanup(parser):
    parser.add_argument(
        "--repo", required=True, help="Exact canonical repository root outside worker"
    )
    parser.add_argument(
        "--worktree", required=True, help="Exact registered linked worker worktree path"
    )
    parser.add_argument(
        "--branch",
        required=True,
        help="Explicit local worker branch (not a ref or handle)",
    )
    parser.add_argument(
        "--base", required=True, help="Explicit local verified base branch"
    )
    parser.add_argument(
        "--verified-base-sha",
        required=True,
        help="Full SHA on which required checks passed",
    )
    parser.add_argument(
        "--worker-commit",
        required=True,
        help="Full verified worker tip SHA, ancestor of base",
    )
    parser.add_argument(
        "--receipt",
        help="Launch receipt; required with --stop-evidence for container workers",
    )
    parser.add_argument(
        "--stop-evidence",
        help="Confirmed stop JSON; rechecked against the container before cleanup",
    )
    parser.add_argument(
        "--parent",
        help="Optional exact immediate parent; rmdir only, nonempty retained",
    )
    parser.add_argument(
        "--execute", action="store_true", help="Perform removal rather than dry-run"
    )
    parser.add_argument(
        "--authorize-cleanup",
        action="store_true",
        help="Explicitly authorize cleanup after verification and stopping writers",
    )


def configure_recovery(parser):
    parser.add_argument("--repo", required=True, help="Explicit repository directory")
    parser.add_argument(
        "--handle",
        action="append",
        default=[],
        help="Optional exact Workmux handle; repeatable",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10,
        help="Seconds per Workmux command (default: 10)",
    )


def configure_verification(parser):
    parser.add_argument(
        "--repo", required=True, help="Existing repository checkout path"
    )
    parser.add_argument("--base", required=True, help="Explicit local base branch name")
    parser.add_argument(
        "--worker-commit",
        required=True,
        help="Full checked post-rebase worker commit SHA",
    )
    parser.add_argument(
        "--checks-file",
        required=True,
        action="append",
        help=(
            'UTF-8 JSON file containing nonempty argv arrays, e.g. [["python3", "-m", "unittest"]]. '
            "Repeat to concatenate files in order; every file must be nonempty. Paths in argv are relative to the temporary checkout."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=300,
        help="Positive timeout in seconds per check (default: 300)",
    )


def configure_startup(parser):
    parser.add_argument("task", help="Aven task for final run reporting")
    parser.add_argument("--run-id", help="Stable run identity (default: task ref)")


def worker(parser, *, new=False):
    parser.add_argument("task", help="Full Aven task reference")
    parser.set_defaults(
        base=None,
        check=None,
        platform=None,
        config=None,
        runtime=None,
        timeout=120,
        run_id=None,
        resume=False,
    )
    if new:
        parser.add_argument(
            "--base", help="Required for a new launch: local integration base branch"
        )
        parser.add_argument(
            "--check",
            action="append",
            help="Required check as a JSON argv array; repeat in order",
        )
        parser.add_argument("--platform", choices=("linux", "darwin"))
        parser.add_argument("--config", help="Workmux config override")
        parser.add_argument(
            "--runtime", choices=("apple-container", "docker", "podman", "local")
        )
        parser.add_argument("--run-id", help="Same run identity as startup")
        parser.add_argument("--timeout", type=int, default=120)


def parser():
    cli = argparse.ArgumentParser(description=__doc__)
    subs = cli.add_subparsers(dest="command", required=True)

    def command(name, help, handler, configure=None, group=subs):
        p = group.add_parser(name, help=help, description=help)
        p.add_argument(
            "--verbose", action="store_true", help="Return complete command evidence"
        )
        p.set_defaults(handler=handler)
        if configure:
            configure(p)
        return p

    command(
        "startup",
        "Verify Aven and open the saved run tab",
        startup.handle,
        configure_startup,
    )
    command(
        "launch",
        "Create one worker from an explicit assignment",
        launch.execute,
        lambda p: worker(p, new=True),
    )
    p = command(
        "inspect", "Read live worker state without changes", launch.execute, worker
    )
    p.add_argument(
        "--wait",
        type=int,
        help="Wait up to this many seconds for a worker event before observing",
    )
    p = command(
        "resume",
        "Reconcile the saved worker; never create a replacement",
        launch.execute,
        worker,
    )
    p.set_defaults(resume=True)
    p = command(
        "close-run",
        "Close the run after SUMMARY and complete cleanup",
        launch.close_run,
        configure_startup,
    )
    p.add_argument(
        "--authorize-close",
        action="store_true",
        help="Confirm final reporting and all run work are complete",
    )
    p = command(
        "report",
        "Select the latest report bound to the current worker revision",
        reports.handle,
    )
    p.add_argument("--task", required=True)
    p.add_argument(
        "--kind",
        default="RESULT",
        choices=("RESULT", "BLOCKED", "VERIFIED", "DISPATCH", "SUMMARY"),
    )
    p.add_argument("--after", help="Exclusive ISO timestamp")
    p.add_argument("--input", type=Path, help="Retained full Aven JSON")
    p.add_argument("--save", type=Path, help="Save complete fetched Aven response")
    command(
        "integrate",
        "Integrate a reviewed RESULT and verify pinned revisions",
        integration.handle,
        configure_integration,
    )
    command(
        "finish",
        "Stop, archive, clean up, report VERIFIED and confirm done",
        finish.handle,
        configure_finish,
    )
    p = subs.add_parser("recover", help="Exceptional recovery only; see recovery.md")
    rs = p.add_subparsers(dest="recovery_command", required=True)
    for name, module, configure in (
        ("snapshot", recovery, configure_recovery),
        ("preflight", git, configure_git),
        ("verify", verification, configure_verification),
        ("stop", stop, configure_stop),
        ("archive", archive, configure_archive),
        ("cleanup", cleanup, configure_cleanup),
    ):
        command(name, module.__doc__, module.handle, configure, rs)
    p = command(
        "doctor", "Diagnose unsupported CLI flags or tool changes", reports.handle
    )
    p.set_defaults(command="discover")
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--refresh", action="store_true")
    return cli


def main(argv=None):
    args = parser().parse_args(argv)
    return output.invoke(args.handler, args)


if __name__ == "__main__":
    raise SystemExit(main())
