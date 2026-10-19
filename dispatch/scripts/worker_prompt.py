#!/usr/bin/env python3
"""Generate an initial dispatch worker prompt from JSON parameters."""

import argparse
import json
import re
from pathlib import Path

TEXT_FIELDS = (
    "task_ref",
    "project",
    "routing",
    "branch",
    "base",
    "launch_base",
    "objective",
)
LIST_FIELDS = ("write_scope", "acceptance_checks")
OPTIONAL_LIST_FIELDS = ("context", "attachments")


def validate(params):
    if not isinstance(params, dict):
        raise ValueError("parameters must be a JSON object")
    unknown = params.keys() - set(TEXT_FIELDS + LIST_FIELDS + OPTIONAL_LIST_FIELDS)
    if unknown:
        raise ValueError("unknown parameters: " + ", ".join(sorted(unknown)))
    for field in TEXT_FIELDS:
        value = params.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be a nonempty string")
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", params["launch_base"]):
        raise ValueError(
            "launch_base must be a full Git commit SHA (40 or 64 hex characters)"
        )
    for field in LIST_FIELDS + OPTIONAL_LIST_FIELDS:
        value = params.get(field, [] if field in OPTIONAL_LIST_FIELDS else None)
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise ValueError(f"{field} must be a list of nonempty strings")
        if field in LIST_FIELDS and not value:
            raise ValueError(f"{field} must contain at least one item")


def render(params, contract):
    validate(params)
    if not contract.strip():
        raise ValueError("worker contract is empty")
    lines = [
        "# Worker assignment",
        "",
        f"Task: {params['task_ref']}",
        f"Aven project: {params['project']}",
        f"Aven routing: {params['routing']}",
        f"Assigned Workmux branch: {params['branch']}",
        f"Local base branch: {params['base']}",
        f"Launch base revision: {params['launch_base']}",
        "",
        "## Objective",
        "",
        params["objective"],
    ]
    for field, heading in (
        ("write_scope", "Write scope"),
        ("acceptance_checks", "Acceptance criteria and required checks"),
        ("context", "Additional context"),
        ("attachments", "Attachments"),
    ):
        if params.get(field):
            lines.extend(["", f"## {heading}", ""])
            lines.extend("- " + item for item in params[field])
    return "\n".join(lines) + "\n\n" + contract


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "JSON parameters:\n"
            f"  Required nonempty strings: {', '.join(TEXT_FIELDS)}\n"
            f"  Required nonempty string lists: {', '.join(LIST_FIELDS)}\n"
            f"  Optional string lists: {', '.join(OPTIONAL_LIST_FIELDS)}\n\n"
            "launch_base: full Git commit SHA (40 or 64 hex characters), captured\n"
            "before generation using git rev-parse --verify refs/heads/<base>^{commit}.\n"
            "routing: configured Aven defaults or diagnosed overrides; guidance,\n"
            "not a CLI override. Use repository-relative source paths and preserve\n"
            "attachment paths. Put dependencies, concurrent ownership, and special\n"
            "instructions in context. Unknown fields are rejected.\n\n"
            "Example shape (replace task values and SHA placeholder):\n"
            + json.dumps(
                {
                    "task_ref": "SND-AG91",
                    "project": "sandbox",
                    "routing": "workspace default; preserve configured shared .aven routing",
                    "branch": "demo-alpha",
                    "base": "main",
                    "launch_base": "<full SHA captured immediately before launch>",
                    "objective": "Add exactly one line: <!-- demo worker alpha: concurrent dispatch -->",
                    "write_scope": ["demo.md only, specifically the alpha comment"],
                    "acceptance_checks": [
                        "Own exact comment appears once",
                        "git diff --check passes",
                        "Only demo.md differs from launch base",
                    ],
                    "context": ["Create demo.md if absent; preserve existing text."],
                    "attachments": [],
                },
                indent=2,
            )
            + "\n\nAppends the current worker.md contract. Text is literal: shell\n"
            "expressions and paths are not expanded. Does not launch workers or\n"
            "change Aven or Git. Existing output files are never overwritten."
        ),
    )
    parser.add_argument(
        "--params",
        type=Path,
        required=True,
        help="UTF-8 JSON parameter file (schema below)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="new UTF-8 Markdown prompt file (parent must exist)",
    )
    args = parser.parse_args()
    try:
        params = json.loads(args.params.read_text(encoding="utf-8"))
        contract = (Path(__file__).resolve().parent.parent / "worker.md").read_text(
            encoding="utf-8"
        )
        prompt = render(params, contract)
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            output.write(prompt)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
