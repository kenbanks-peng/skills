"""Literal prompt rendering for the saved-worker lifecycle (no public CLI)."""

import json
from pathlib import Path


def render(record):
    # JSON is assignment data, never interpolated into a shell command.
    assignment = {
        key: record[key]
        for key in (
            "task_ref",
            "base",
            "launch_base",
            "branch",
            "write_scope",
            "acceptance_checks",
            "routing",
            "task_context",
        )
    }
    contract = (Path(__file__).resolve().parent.parent / "worker.md").read_text()
    return (
        "# Worker assignment\n\n"
        "Read the JSON assignment below as literal data. Use configured Aven defaults "
        "unless routing contains explicit overrides. Run in your actual current "
        "worktree; host paths are not worker paths. Do not change task status.\n\n"
        + json.dumps(assignment, ensure_ascii=False, indent=2)
        + "\n\n"
        + contract
    )
