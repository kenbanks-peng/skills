"""Worker instructions with task context read directly from Aven."""

import json
import shlex
from pathlib import Path

from .runtime import run


def bullets(values):
    """Keep multiline values together in a Markdown list."""
    return "\n".join("- " + str(value).replace("\n", "\n  ") for value in values)


def scoped_context(data):
    """Keep requirements and decisions; omit duplicate note bodies and machine IDs."""
    task = data["task"]
    sections = [
        task["display_ref"] + ": " + task["title"],
        "Description:\n" + task["description"],
    ]
    # Keep scheduling constraints, relationships, attachments, and metadata.
    extra = {
        key: value
        for key, value in data.items()
        if key not in ("task", "notes") and value
    }
    if extra:
        sections.append("Related context:\n" + json.dumps(extra, ensure_ascii=False))
    notes = list(dict.fromkeys(note["body"] for note in data["notes"]))
    if notes:
        sections.append("Notes:\n" + "\n\n".join(notes))
    return "\n\n".join(sections)


def render(task_ref, *, base, launch_base, branch, acceptance_checks, context=None):
    """Fetch plain Aven context for the task and render the worker instructions."""
    if context is None:
        context = run(["aven", "context", task_ref])
    contract = (Path(__file__).resolve().parents[2] / "worker.md").read_text()
    sections = [
        "## Work location\n\n"
        + bullets(
            [
                "Task ref: " + task_ref,
                "Base branch: " + base,
                "Launch-base commit: " + launch_base,
                "Worker branch: " + branch,
            ]
        ),
        "## Task context\n\n" + context.rstrip(),
        contract.rstrip(),
        "## Required checks\n\nRun each command exactly as shown, in this order:\n\n"
        # Shell quoting preserves arguments; rendering never executes checks.
        + "\n\n".join(
            "    " + shlex.join(argv).replace("\n", "\n    ")
            for argv in acceptance_checks
        ),
    ]
    return "\n\n".join(sections) + "\n"
