#!/usr/bin/env python3
"""Require each exact identifying note once in the configured target file."""

import argparse
import json
from pathlib import Path

from worker_runtime import emit


def check(manifest):
    manifest = Path(manifest).resolve(strict=True)
    config = json.loads(manifest.read_text())
    notes = config["notes"]
    if (
        not isinstance(notes, list)
        or len(notes) < 2
        or any(not isinstance(note, str) or not note.strip() for note in notes)
        or len(set(notes)) != len(notes)
    ):
        raise ValueError(
            "Configure at least two distinct, nonempty exact identifying notes"
        )
    relative = Path(config["file"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Target file must be relative to the manifest directory")
    target = manifest.parent / relative
    if (
        target.is_symlink()
        or manifest.parent not in target.resolve(strict=True).parents
    ):
        raise ValueError("Target must remain inside the manifest directory")
    text = target.read_text()
    counts = {note: text.count(note) for note in notes}
    return {
        "ok": all(count == 1 for count in counts.values()),
        "file": str(target),
        "counts": counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        required=True,
        help='JSON: {"file": "relative/path.md", "notes": ["exact first", "exact second"]}',
    )
    args = parser.parse_args()
    try:
        result = check(args.manifest)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"ok": False, "error": str(error)}
    return emit(result)


if __name__ == "__main__":
    raise SystemExit(main())
