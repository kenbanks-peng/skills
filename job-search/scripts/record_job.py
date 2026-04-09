#!/usr/bin/env python3
"""Insert a single candidate job into the jobs database, deduping by URL.

Reads one JSON object from stdin. Required keys: job_title, job_url.
Everything else is optional. Any key not listed in FIELDS is ignored.

Usage: echo '{"job_title": "...", "job_url": "..."}' | python record_job.py <jobs.db>

Exit codes:
  0  inserted
  0  skipped (already present) — prints "skipped <id>"
  2  bad input
"""
import hashlib
import json
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

# Columns that the inserter will populate from the payload.
# Anything else in the payload is ignored.
FIELDS: list[str] = [
    # Core posting
    "job_title", "company", "company_domain", "company_size", "company_industry",
    "company_stage", "job_url", "application_url", "source_url", "source",
    "source_job_id", "job_description", "description_hash",
    # Location & work mode
    "location", "location_city", "location_region", "location_country",
    "work_mode", "timezone", "relocation_required", "visa_sponsorship",
    # Compensation
    "salary_min", "salary_max", "salary_currency", "salary_period",
    "salary_raw", "compensation_notes",
    # Role characterization
    "employment_type", "seniority_level", "role_type",
    "years_experience_required", "tech_stack",
    # Matching
    "keyword_alignment", "match_score", "match_reasons", "track",
    # Subjective
    "priority", "excitement",
    # Pipeline (mostly filled in later, but accept on insert too)
    "date_applied", "application_method", "referral_contact", "resume_version",
    "cover_letter_path", "recruiter_name", "recruiter_email", "last_contact_date",
    "next_action", "next_action_date", "interview_count", "rejection_reason",
    "withdrawal_reason",
    # Housekeeping
    "notes", "date_posted",
]

VALID_WORK_MODE = {"remote", "hybrid", "onsite"}
VALID_SALARY_PERIOD = {"year", "month", "week", "day", "hour", "contract"}
VALID_EMPLOYMENT_TYPE = {"full_time", "part_time", "contract", "fractional", "internship"}
VALID_ROLE_TYPE = {"ic", "manager", "hybrid"}


def _normalize_alignment(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return ",".join(str(v).strip() for v in value if str(v).strip())
    return str(value)


def _normalize_tech_stack(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        return json.dumps([str(v).strip() for v in value if str(v).strip()])
    return str(value)


def _normalize_track(value) -> str | None:
    if value is None:
        return None
    track = str(value).strip().lower()
    return track or None


def _enum(name: str, value, valid: set[str]) -> str | None:
    if value is None:
        return None
    v = str(value).strip().lower()
    if v == "":
        return None
    if v not in valid:
        raise ValueError(f"invalid {name}: {value!r} (valid: {sorted(valid)})")
    return v


def _bool01(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if value else 0
    s = str(value).strip().lower()
    if s in ("1", "true", "yes", "y", "t"):
        return 1
    if s in ("0", "false", "no", "n", "f"):
        return 0
    raise ValueError(f"invalid boolean: {value!r}")


_WS_RE = re.compile(r"\s+")


def _compute_description_hash(description) -> str | None:
    """SHA-256 of the normalized description. Used as a soft dedupe key for
    cross-board reposts (same text under a different job_url).

    Normalization: lowercase, collapse all whitespace to single spaces, strip.
    Returns None for empty / missing descriptions so that the absence of a
    description never collides with other absent descriptions.
    """
    if description is None:
        return None
    text = str(description)
    normalized = _WS_RE.sub(" ", text).strip().lower()
    if not normalized:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _bounded_int(name: str, value, lo: int, hi: int) -> int | None:
    if value is None:
        return None
    n = int(value)
    if not (lo <= n <= hi):
        raise ValueError(f"{name} must be between {lo} and {hi}, got {n}")
    return n


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: record_job.py <path-to-jobs.db>", file=sys.stderr)
        return 2
    db_path = Path(sys.argv[1]).expanduser()
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"bad json: {exc}", file=sys.stderr)
        return 2

    if not payload.get("job_title") or not payload.get("job_url"):
        print("missing required fields job_title/job_url", file=sys.stderr)
        return 2

    row: dict = {k: payload.get(k) for k in FIELDS}

    # Auto-compute description_hash when not supplied by the caller. Hash is
    # derived from the (normalized) job_description so cross-board reposts
    # dedupe even when job_url differs. Caller-supplied hashes are respected.
    if not row.get("description_hash"):
        row["description_hash"] = _compute_description_hash(row.get("job_description"))

    try:
        row["keyword_alignment"] = _normalize_alignment(row["keyword_alignment"])
        row["tech_stack"] = _normalize_tech_stack(row["tech_stack"])
        row["track"] = _normalize_track(row["track"])
        row["work_mode"] = _enum("work_mode", row["work_mode"], VALID_WORK_MODE)
        row["salary_period"] = _enum("salary_period", row["salary_period"], VALID_SALARY_PERIOD)
        row["employment_type"] = _enum("employment_type", row["employment_type"], VALID_EMPLOYMENT_TYPE)
        row["role_type"] = _enum("role_type", row["role_type"], VALID_ROLE_TYPE)
        row["relocation_required"] = _bool01(row["relocation_required"])
        row["priority"] = _bounded_int("priority", row["priority"], 1, 5)
        row["excitement"] = _bounded_int("excitement", row["excitement"], 1, 5)
    except (ValueError, TypeError) as exc:
        print(f"bad payload: {exc}", file=sys.stderr)
        return 2

    # System-managed fields.
    now_iso = datetime.now().isoformat(timespec="seconds")
    row["date_found"] = date.today().isoformat()
    row["created_at"] = now_iso
    row["updated_at"] = now_iso
    row["state"] = "created"
    row["archived"] = 0
    if row.get("interview_count") is None:
        row["interview_count"] = 0

    conn = sqlite3.connect(db_path)
    try:
        # Dedupe by job_url first (hard key), then by description_hash when
        # available (soft key catches cross-board reposts under different URLs).
        existing = conn.execute(
            "SELECT id FROM jobs WHERE job_url = ?", (row["job_url"],)
        ).fetchone()
        if existing:
            print(f"skipped {existing[0]}")
            return 0

        if row.get("description_hash"):
            existing = conn.execute(
                "SELECT id FROM jobs WHERE description_hash = ?",
                (row["description_hash"],),
            ).fetchone()
            if existing:
                print(f"skipped {existing[0]} (description_hash match)")
                return 0

        columns = list(row.keys())
        placeholders = ",".join(f":{c}" for c in columns)
        sql = f"INSERT INTO jobs ({', '.join(columns)}) VALUES ({placeholders})"
        cur = conn.execute(sql, row)
        conn.commit()
        print(f"inserted {cur.lastrowid}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
