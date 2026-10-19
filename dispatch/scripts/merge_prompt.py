#!/usr/bin/env python3
"""Render a single-attempt merge authorization with the current merge.md procedure."""

import argparse
import json
from pathlib import Path

FIELDS = (
    "task_ref",
    "project",
    "routing",
    "branch",
    "worktree",
    "base",
    "authorization_id",
)


def render(params, procedure):
    if not isinstance(params, dict):
        raise ValueError("parameters must be a JSON object")
    unknown = params.keys() - set(FIELDS + ("acceptance_checks",))
    if unknown:
        raise ValueError("unknown parameters: " + ", ".join(sorted(unknown)))
    for field in FIELDS:
        if not isinstance(params.get(field), str) or not params[field].strip():
            raise ValueError(f"{field} must be a nonempty string")
    checks = params.get("acceptance_checks")
    if (
        not isinstance(checks, list)
        or not checks
        or any(not isinstance(check, str) or not check.strip() for check in checks)
    ):
        raise ValueError(
            "acceptance_checks must be a nonempty list of nonempty strings"
        )
    if not procedure.strip():
        raise ValueError("merge procedure is empty")
    labels = (
        "Task",
        "Aven project",
        "Aven routing",
        "Worker branch",
        "Worker worktree",
        "Recorded local base",
        "Authorization ID",
    )
    lines = ["# Merge authorization", ""]
    lines.extend(f"{label}: {params[field]}" for field, label in zip(FIELDS, labels))
    lines.extend(
        [
            "",
            "This authorizes one merge attempt only. Include this authorization ID in the result or failure note so dispatch can distinguish it from an earlier attempt.",
            "",
            "## Required post-rebase checks",
            "",
        ]
    )
    lines.extend("- " + check for check in checks)
    return "\n".join(lines) + "\n\n" + procedure


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Required JSON nonempty strings: " + ", ".join(FIELDS) + ".\n"
            "Required nonempty string list: acceptance_checks. Unknown fields are rejected.\n"
            "authorization_id: a new unique ID for this attempt (retain it in Aven).\n"
            "worktree: worker-visible path. base: recorded local branch, not a remote ref.\n"
            "routing: configured Aven defaults or diagnosed overrides.\n"
            "Generate only after review and preflight. Generation does not send authorization,\n"
            "run Git, or change Aven. The current merge.md is inlined for sandboxed workers.\n"
            "Use a new output file in an existing directory; literal text is not evaluated."
        ),
    )
    parser.add_argument(
        "--params", type=Path, required=True, help="UTF-8 JSON parameter file"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="New Markdown authorization file"
    )
    args = parser.parse_args()
    try:
        params = json.loads(args.params.read_text(encoding="utf-8"))
        procedure = (Path(__file__).resolve().parent.parent / "merge.md").read_text(
            encoding="utf-8"
        )
        prompt = render(params, procedure)
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            output.write(prompt)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
