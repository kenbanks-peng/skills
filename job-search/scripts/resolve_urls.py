#!/usr/bin/env python3
"""Resolve URL templates in job-search-urls.md against the tracks in job-search-spec.toml.

For each track, build scope = (universal {{name}} bindings, overlaid by the
track's {{name}} bindings). For each URL template, substitute placeholders,
fanning out list-valued bindings into the cartesian product. Emit one JSONL
record per resolved URL on stdout:

  {"track": "dev", "url": "https://...", "vars": {"queries": "staff engineer", ...}}

Errors:
  - Template references {{name}} not in scope → printed to stderr, exit 1.
  - urls.md has no column-zero `- ` or `* ` bullet templates → exit 1.

Only column-zero bullets in urls.md are templates, so the file's
documentation block is left alone.
"""

from __future__ import annotations

import json
import re
import sys
from itertools import product
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_search_spec import parse_search_spec  # noqa: E402

PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")
URL_RE = re.compile(r"https?://\S+")
BULLET_LINE_RE = re.compile(r"^[-*]\s+(.+)$")


def parse_url_templates(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            continue
        m = BULLET_LINE_RE.match(line)
        if not m:
            continue
        u = URL_RE.search(m.group(1))
        if u:
            out.append(u.group(0).rstrip(").,"))
    return out


def _strify(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def expand(
    template: str, scope: dict[str, object]
) -> tuple[list[tuple[str, dict]], list[str]]:
    placeholders = list(dict.fromkeys(PLACEHOLDER_RE.findall(template)))
    missing = [p for p in placeholders if p not in scope]
    if missing:
        return [], [f"{template}: missing {{{{{', '.join(missing)}}}}}"]

    value_lists: list[list[str]] = []
    for name in placeholders:
        v = scope[name]
        if isinstance(v, list):
            if not v:
                return [], [f"{template}: variable '{name}' is empty list"]
            value_lists.append([_strify(x) for x in v])
        else:
            value_lists.append([_strify(v)])

    out: list[tuple[str, dict]] = []
    for combo in product(*value_lists):
        url = template
        bound: dict[str, str] = {}
        for name, value in zip(placeholders, combo):
            url = re.sub(
                r"\{\{\s*" + re.escape(name) + r"\s*\}\}", quote_plus(value), url
            )
            bound[name] = value
        out.append((url, bound))
    return out, []


def main() -> int:
    if len(sys.argv) != 3:
        print(
            "usage: resolve_urls.py <job-search-urls.md> <job-search-spec.toml>",
            file=sys.stderr,
        )
        return 2

    templates = parse_url_templates(
        Path(sys.argv[1]).expanduser().read_text(encoding="utf-8")
    )
    if not templates:
        print("no URL templates found in urls.md", file=sys.stderr)
        return 1

    spec = parse_search_spec(Path(sys.argv[2]).expanduser().read_text(encoding="utf-8"))
    tracks = spec.get("track") or []
    if not tracks:
        print("no tracks defined in job-search-spec.toml", file=sys.stderr)
        return 1

    universal_vars = spec.get("search") or {}

    errors: list[str] = []
    seen: set[str] = set()

    for track in tracks:
        track_id = track["id"]
        scope = {**universal_vars, **(track.get("search") or {})}
        for template in templates:
            urls, errs = expand(template, scope)
            if errs:
                errors.extend(f"[{track_id}] {e}" for e in errs)
                continue
            for url, bound in urls:
                if url in seen:
                    continue
                seen.add(url)
                print(json.dumps({"track": track_id, "url": url, "vars": bound}))

    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
