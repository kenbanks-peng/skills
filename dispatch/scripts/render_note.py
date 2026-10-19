#!/usr/bin/env python3
"""Render a dispatch evidence note from JSON parameters without posting it to Aven."""

import argparse
import json
from pathlib import Path
from string import Template

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
KINDS = ("DISPATCH", "RESULT", "MERGE_PENDING", "MERGE_VERIFIED", "BLOCKED", "SUMMARY")
INPUT_FIELDS = {
    'DISPATCH': ['task_ref', 'handle', 'branch', 'worktree', 'base', 'launch_base', 'agent_type', 'config', 'execution_mode', 'worker_worktree', 'launch_receipt'],
    'RESULT': ['summary', 'worker_commit', 'task_ref', 'components', 'checks'],
    'MERGE_PENDING': ['worker_commit', 'base', 'base_sha', 'task_ref', 'authorization_id', 'checks'],
    'MERGE_VERIFIED': ['base', 'verified_base_sha', 'task_ref', 'verification_evidence', 'cleanup_evidence', 'repo', 'branch', 'worktree', 'worker_commit'],
    'BLOCKED': ['error', 'next_action', 'owner', 'task_ref', 'phase', 'command', 'working_directory', 'retained_state', 'evidence'],
    'SUMMARY': ['outcome', 'task_ref', 'verified_base_sha', 'checks', 'follow_ups'],
}
LIST_FIELDS = {"components", "checks", "retained_state", "evidence", "follow_ups"}


def closure_evidence(params):
    verification = json.loads(
        Path(params["verification_evidence"]).read_text(encoding="utf-8")
    )
    cleanup = json.loads(Path(params["cleanup_evidence"]).read_text(encoding="utf-8"))
    if not isinstance(verification, dict) or not isinstance(cleanup, dict):
        raise ValueError("verification and cleanup evidence must be JSON objects")
    checks = verification.get("checks")
    plan = cleanup.get("plan")
    repository = verification.get("repo")
    if not (
        verification.get("ok") is True
        and verification.get("base_moved") is False
        and verification.get("tested_sha") == params["verified_base_sha"]
        and verification.get("worker_sha") == params["worker_commit"]
        and isinstance(checks, list)
        and checks
        and all(
            isinstance(check, dict)
            and check.get("status") == "passed"
            and check.get("returncode") == 0
            and isinstance(check.get("argv"), list)
            and check["argv"]
            and all(isinstance(arg, str) for arg in check["argv"])
            for check in checks
        )
        and cleanup.get("ok") is True
        and cleanup.get("executed") is True
        and isinstance(plan, dict)
        and plan.get("verified_base_sha") == params["verified_base_sha"]
        and plan.get("worker_commit") == params["worker_commit"]
        and isinstance(repository, dict)
        and repository.get("worktree") == params["repo"] == plan.get("repo")
        and repository.get("common_dir") == plan.get("common_dir")
        and bool(repository.get("common_dir"))
        and verification.get("base_ref") == "refs/heads/" + params["base"]
        and plan.get("base") == params["base"]
        and plan.get("branch") == params["branch"]
        and plan.get("worktree") == params["worktree"]
    ):
        raise ValueError(
            "closure requires matching resource identity, successful verification, and executed cleanup evidence"
        )
    count = len({tuple(check["argv"]) for check in checks})
    return f"{count} distinct check{'s' if count != 1 else ''} passed"


def required_fields(kind):
    return INPUT_FIELDS[kind]


def render(kind, params):
    template = (TEMPLATES / f"{kind}.md").read_text(encoding="utf-8")
    required = required_fields(kind)
    if not isinstance(params, dict) or set(params) != set(required):
        raise ValueError("parameters must contain exactly: " + ", ".join(required))
    rendered = {}
    for field in required:
        value = params[field]
        if field in LIST_FIELDS:
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(item, str) or not item.strip() for item in value)
            ):
                raise ValueError(f"{field} must be a nonempty list of nonempty strings")
            rendered[field] = "; ".join(dict.fromkeys(item.strip() for item in value))
        else:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a nonempty string")
            rendered[field] = value
    if kind == "MERGE_VERIFIED":
        rendered["checks"] = closure_evidence(params)
    rendered["run_context"] = "; ".join(
        dict.fromkeys(rendered.get(name, "") for name in ("config", "execution_mode"))
    )
    note = Template(template).substitute(rendered)
    return note.replace(str(Path.home()) + "/", "~/")


def main():
    schemas = []
    for kind in KINDS:
        names = required_fields(kind)
        schemas.append(
            kind
            + ":\n  "
            + ", ".join(
                name + (" [list]" if name in LIST_FIELDS else "") for name in names
            )
        )
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "JSON fields by kind (all required; unknown fields rejected):\n\n"
            + "\n\n".join(schemas)
            + "\n\nFields are nonempty strings except [list], which requires nonempty string lists.\n"
            "Use Git-generated SHAs and actual check evidence, never inferred passes.\n"
            "MERGE_PENDING renders MERGE (worker integration); MERGE_VERIFIED renders VERIFIED (dispatch closure).\n"
            "For MERGE_VERIFIED, verification_evidence and cleanup_evidence are paths to\n"
            "JSON stdout from verify_base.py and cleanup_worker.py (relative to cwd or absolute).\n"
            "Successful evidence must match full SHAs and exact repository/base/worker identity.\n"
            "Use canonical paths for repo and worktree. Dry runs are rejected.\n"
            "Rendering does not recheck current Git state or establish semantic correctness.\n"
            "Review for relevance and add material decisions or exceptions before posting with tasks. Failed/skipped checks belong\n"
            "in BLOCKED, not a success note. Include an authorization ID in BLOCKED.phase\n"
            'for a merge failure. For SUMMARY.follow_ups use ["None"] if none exist.\n'
        ),
    )
    parser.add_argument("--kind", choices=KINDS, required=True)
    parser.add_argument(
        "--params", type=Path, required=True, help="UTF-8 JSON parameter file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New Markdown note file; parent must exist",
    )
    args = parser.parse_args()
    try:
        note = render(args.kind, json.loads(args.params.read_text(encoding="utf-8")))
        with args.output.open("x", encoding="utf-8", newline="\n") as output:
            output.write(note)
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
