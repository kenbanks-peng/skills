"""Bounded agent summaries and complete evidence outside worker resources."""

import contextlib
import io
import json
import os
import tempfile
from pathlib import Path

from .git import CheckError, paths

TEXT_LIMIT = 400
SUMMARY_BUDGET = 8192


def short(value, limit=TEXT_LIMIT):
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "… [see evidence]"


def error_preview(value):
    """Keep the diagnosis, not JSON receipts embedded in legacy exception text."""
    text = str(value)
    prefix, separator, payload = text.partition("{")
    if separator:
        try:
            evidence = json.loads(separator + payload)
            if isinstance(evidence, dict):
                detail = evidence.get("error", "See complete observation in evidence")
                return short(prefix + str(detail))
        except ValueError:
            pass
    return short(text)


def items(values):
    if not isinstance(values, list):
        return short(values)
    return {
        "count": len(values),
        "items": [
            {
                k: short(v)
                for k, v in value.items()
                if k
                in (
                    "resource",
                    "identity",
                    "status",
                    "owner",
                    "next_action",
                    "error",
                    "kind",
                )
            }
            if isinstance(value, dict)
            else error_preview(value)
            for value in values[:3]
        ],
        "more": max(0, len(values) - 3),
    }


def summary(data, args, evidence_path=None):
    """Use explicit fields, never traverse histories or recursive receipts."""
    result = {"ok": data.get("ok") is True}
    for key in (
        "delivered",
        "task_complete",
        "cleanup_complete",
        "finish_complete",
        "aven_closed",
        "executed",
        "stopped",
        "complete",
        "dry_run",
    ):
        if key in data:
            result[key] = data[key]
    for key in (
        "task_ref",
        "task",
        "task_id",
        "handle",
        "branch",
        "run_id",
        "worker_commit",
        "reviewed_commit",
        "checked_worker_sha",
        "launch_base",
        "verified_base_sha",
        "tested_sha",
        "status",
        "aven_status",
        "record_path",
        "source_path",
        "evidence_directory",
        "verification_evidence",
        "completion_report",
        "cleanup",
        "next_action",
        "owner",
        "error",
    ):
        if key in data:
            result[key] = (
                str(data[key])
                if key.endswith(("_path", "_directory", "_evidence"))
                or key == "completion_report"
                else short(data[key])
            )
    if data.get("cleanup") == "retained" and data.get("worktree"):
        result["retained_checkout"] = data["worktree"]
    result.setdefault("task_ref", getattr(args, "task", None))
    if result["task_ref"] is None:
        result.pop("task_ref")
    for key in ("pending_cleanup", "housekeeping", "errors"):
        if key in data:
            result[key] = items(data[key])
    # Inspect returns the current observation, not the historical launch outcome.
    inspection = data.get("inspection")
    if inspection:
        result["status"] = (
            "observed"
            if inspection.get("ok") or "worktree_present" in inspection
            else "inspection_failed"
        )
        for key in ("worktree_present", "branch_present"):
            if key in inspection:
                result[key] = inspection[key]
        if inspection.get("error"):
            result["error"] = short(inspection["error"])
        status = inspection.get("workmux_status", {})
        agents = status.get("agents", [])
        if agents:
            result["worker_status"] = short(agents[0].get("status"))
    note = data.get("note")
    if note:
        result["note"] = {
            key: short(note[key], 600 if key == "body" else TEXT_LIMIT)
            for key in ("id", "created_at", "body")
            if key in note
        }
    if evidence_path:
        result["evidence_path"] = str(evidence_path)
    saved_finish = data.get("finish") or data.get("saved_finish")
    if saved_finish:
        # Saved finish outcomes matter even when the live worker has disappeared.
        for key in (
            "delivered",
            "task_complete",
            "cleanup_complete",
            "finish_complete",
        ):
            if key in saved_finish:
                result[key] = saved_finish[key]
        for key in ("pending_cleanup", "housekeeping"):
            if key in saved_finish:
                result[key] = items(saved_finish[key])
    if inspection:
        # Historical launch errors are not this read-only query's outcome.
        result.pop("error", None)
        if inspection.get("error"):
            result["error"] = short(inspection["error"])
        if inspection.get("wait_error"):
            result["warning"] = short(inspection["wait_error"])
    writer = data.get("writer")
    if writer:
        result["writer_ok"] = writer.get("ok") is True
        result["writer_stopped"] = writer.get("stopped") is True
        if writer.get("error"):
            result["writer_error"] = error_preview(writer["error"])
    if saved_finish and saved_finish.get("error"):
        result["saved_finish_error"] = error_preview(saved_finish["error"])
    events = data.get("events") or []
    if events and not inspection:
        activation = events[-1].get("activation", {})
        if activation.get("status"):
            result["status"] = activation["status"]
    if not result["ok"] or (
        data.get("pending_cleanup")
        or not result.get("finish_complete", True)
        or not data.get("complete", True)
        or (saved_finish and saved_finish.get("pending_cleanup"))
        or result.get("writer_error")
        or result.get("saved_finish_error")
    ):
        result.setdefault("owner", "dispatcher")
        result.setdefault(
            "next_action",
            "Read the error and retained evidence; resolve before closure",
        )
    if result.get("error"):
        result["error"] = error_preview(
            data.get("error") if not inspection else inspection.get("error")
        )
        result["ok"] = False
    # Bound pathological errors and resource identities without hiding their count.
    if len(json.dumps(result, ensure_ascii=True).encode()) > SUMMARY_BUDGET:

        def bound(value):
            if isinstance(value, str):
                return short(value, 60)
            if isinstance(value, dict):
                return {
                    key: (
                        item
                        if key.endswith(("_path", "_directory", "_evidence"))
                        or key == "completion_report"
                        else bound(item)
                    )
                    for key, item in value.items()
                }
            if isinstance(value, list):
                return [bound(item) for item in value]
            return value

        result = bound(result)
    return result


def read_only(args):
    return (
        (args.command == "inspect" and not getattr(args, "resume", False))
        or (args.command == "finish" and getattr(args, "inspect", False))
        or (args.command == "integrate" and getattr(args, "closure", False))
        or (args.command == "recover" and args.recovery_command == "preflight")
    )


def retain(data, args):
    """Write complete evidence durably; never put it in a worker checkout."""
    # Worker/run records already retain complete history atomically. Do not copy
    # that growing history into a new command receipt on each resume.
    if data.get("schema_version") == 1 and data.get("record_path"):
        record = Path(data["record_path"])
        if record.is_file():
            return record
    try:
        repo = getattr(args, "repo", None) or Path.cwd()
        directory = Path(paths(repo)["common_dir"]) / "dispatch-evidence"
    except (OSError, ValueError, CheckError):
        directory = Path.home() / ".local/state/dispatch/evidence"
    directory.mkdir(parents=True, exist_ok=True)
    fd, filename = tempfile.mkstemp(
        prefix=args.command + "-", suffix=".json", dir=directory
    )
    with os.fdopen(fd, "w") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    return Path(filename)


def full_evidence(value):
    """Expand retained subprocess logs only for explicit verbose output."""
    if isinstance(value, list):
        return [full_evidence(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {key: full_evidence(item) for key, item in value.items()}
    for stream in ("stdout", "stderr"):
        if stream + "_path" in value and stream in value:
            try:
                result[stream] = (
                    Path(value[stream + "_path"])
                    .read_bytes()
                    .decode("utf-8", errors="replace")
                )
                result[stream + "_truncated"] = False
            except OSError as error:
                result[stream + "_retrieval_error"] = str(error)
    return result


def invoke(handler, args):
    """Keep command exit codes; present a summary only after retaining evidence."""
    from .runtime import emit

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            result = handler(args)
        if isinstance(result, dict):
            data = result
            code = 0 if data.get("ok") else 1
        else:
            data = json.loads(output.getvalue())
            code = result
    except (ValueError, OSError, KeyError, TypeError, CheckError) as error:
        data, code = {"ok": False, "error": str(error)}, 1
    evidence_path = None
    if not read_only(args):
        try:
            evidence_path = retain(data, args)
        except OSError as error:
            data["ok"] = False
            data["evidence_error"] = str(error)
            data["error"] = "Cannot retain full command evidence: " + str(error)
            code = 1
    if args.verbose:
        if evidence_path:
            data["evidence_path"] = str(evidence_path)
        emit(full_evidence(data))
    else:
        emit(summary(data, args, evidence_path))
    return code
