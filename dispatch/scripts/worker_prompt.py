"""Worker instructions with task context read directly from Aven."""

import shlex
from pathlib import Path

from worker_runtime import run


def bullets(values):
    """Keep multiline values together in a Markdown list."""
    return "\n".join("- " + str(value).replace("\n", "\n  ") for value in values)


def render(task_ref, *, base, launch_base, branch, acceptance_checks):
    """Fetch plain Aven context for the task and render the worker instructions."""
    context = run(["aven", "context", task_ref])
    contract = (Path(__file__).resolve().parent.parent / "worker.md").read_text()
    sections = [
        "## Work location\n\n" + bullets([
            "Task ref: " + task_ref,
            "Base branch: " + base,
            "Launch-base commit: " + launch_base,
            "Worker branch: " + branch,
        ]),
        "## Task context\n\n" + context.rstrip(),
        contract.rstrip(),
        "## Required checks\n\nRun each command exactly as shown, in this order:\n\n"
        # Shell quoting preserves arguments; rendering never executes checks.
        + "\n\n".join("    " + shlex.join(argv).replace("\n", "\n    ")
                       for argv in acceptance_checks),
    ]
    return "\n\n".join(sections) + "\n"
