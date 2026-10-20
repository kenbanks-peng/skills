"""Worker instructions with task context read directly from Aven."""

import shlex
from pathlib import Path

from worker_runtime import run


def bullets(values):
    """Keep multiline values together in a Markdown list."""
    return "\n".join("- " + str(value).replace("\n", "\n  ") for value in values)


def render(task_ref, *, base, launch_base, branch, write_scope, acceptance_checks,
           routing, repo=None):
    """Fetch plain Aven context for the task and render the worker instructions."""
    argv = ["aven", "context", task_ref]
    for key in ("db", "workspace"):
        if routing.get(key):
            argv.extend(["--" + key, routing[key]])
    context = run(argv, repo)
    sections = [
        "# Worker assignment: " + task_ref,
        "Complete the task below within the assigned write scope. "
        "Run the required checks, commit your changes, and report the result.",
        "## Task context\n\n" + context.rstrip(),
        "## Work location\n\n" + bullets([
            "Task ref: " + task_ref,
            "Base branch: " + base,
            "Launch-base commit: " + launch_base,
            "Worker branch: " + branch,
        ]),
        "## Write scope\n\nEdit only these repository-relative paths:\n\n"
        + bullets(write_scope),
        "## Required checks\n\nRun each command exactly as shown, in this order:\n\n"
        # Shell quoting preserves arguments; rendering never executes checks.
        + "\n\n".join("    " + shlex.join(argv).replace("\n", "\n    ")
                       for argv in acceptance_checks),
        "## Aven reporting\n\nUse this routing for task reads and reports:\n\n"
        + bullets(key + ": " + (routing.get(key) or "configured default")
                  for key in ("db", "workspace")),
    ]
    contract = (Path(__file__).resolve().parent.parent / "worker.md").read_text()
    sections.append(contract.rstrip())
    return "\n\n".join(sections) + "\n"
