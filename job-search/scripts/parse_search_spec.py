#!/usr/bin/env python3
"""Parse job-search-spec.toml.

Protocol — the entire thing:

The spec file is a TOML document. Every key is either a reserved structural
key or a {{name}} placeholder usable in job-search-urls.md.

Structure:

  [search]                     Universal URL template variables.
    <key> = <value>            Every key here is a {{key}} placeholder available
                               to every track.

  [filter.*]                   Universal hard filters (NOT URL placeholders).
                               These are used for candidate filtering.

  [[track]]                    Array of tables, one per track.
    id    = "<slug>"           Reserved. DB `track` column.
    label = "<text>"           Reserved. Display name.

    [track.search]             Track URL template variables (placeholders).
    [track.filter.*]           Track hard filters (merged vs universal).
    [track.scoring]            Track scoring keywords (any/none lists).

  [profile]                    Optional. Free-form context for Claude.
    experience = ["..."]
    domains = ["..."]
    skills = ["..."]

  [rubric]                     Optional. Scoring bands for Claude.
    bands = [
      { range = "80-100", means = "..." },
      ...
    ]

Resolution per track:
  scope = search ∪ track.search
  List-valued bindings fan out as the cartesian product in urls.md.

Output (Python dict / JSON) uses the same vocabulary as the TOML:

  {
    "search":  {...},
    "filter":  {...},
    "track": [
      {"id": "...", "label": "...", "search": {...}, "filter": {...}, "scoring": {...}},
      ...
    ],
    "profile": {...},
    "rubric":  {...}
  }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


def parse_search_spec(text: str) -> dict[str, Any]:
    doc = tomllib.loads(text)

    search = doc.get("search") or {}
    if not isinstance(search, dict):
        raise ValueError("`[search]` must be a table")

    filters = doc.get("filter") or {}
    if not isinstance(filters, dict):
        raise ValueError("`[filter]` must be a table (use [filter.*] subtables)")

    raw_tracks = doc.get("track") or []
    if not isinstance(raw_tracks, list):
        raise ValueError("`[[track]]` must be an array of tables")

    tracks_out: list[dict[str, Any]] = []
    for i, t in enumerate(raw_tracks):
        if not isinstance(t, dict):
            raise ValueError(f"track[{i}] must be a table")
        if "id" not in t:
            raise ValueError(f"track[{i}] missing required `id`")

        track_search = t.get("search") or {}
        if not isinstance(track_search, dict):
            raise ValueError(f"track[{i}].search must be a table")

        track_filters = t.get("filter") or {}
        if not isinstance(track_filters, dict):
            raise ValueError(f"track[{i}].filter must be a table")

        track_scoring = t.get("scoring") or {}
        if not isinstance(track_scoring, dict):
            raise ValueError(f"track[{i}].scoring must be a table")

        tracks_out.append(
            {
                "id": str(t["id"]),
                "label": str(t.get("label") or t["id"]),
                "search": track_search,
                "filter": track_filters,
                "scoring": track_scoring,
            }
        )

    return {
        "search": search,
        "filter": filters,
        "track": tracks_out,
        "profile": doc.get("profile") or {},
        "rubric": doc.get("rubric") or {},
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: parse_search_spec.py <job-search-spec.toml>", file=sys.stderr)
        return 2
    text = Path(sys.argv[1]).expanduser().read_text(encoding="utf-8")
    try:
        spec = parse_search_spec(text)
    except (ValueError, tomllib.TOMLDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    json.dump(spec, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
