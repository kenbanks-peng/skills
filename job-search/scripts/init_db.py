#!/usr/bin/env python3
"""Initialize the jobs SQLite database.

Usage: python init_db.py <path-to-jobs.db>

Safe to run repeatedly. On a fresh DB, creates the full schema. On an existing
DB, adds any missing columns via ALTER TABLE (migrations list below).
Prints the current row count on success so the caller can confirm.
"""
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Timestamps
    date_found                TEXT NOT NULL,            -- ISO date first recorded
    date_posted               TEXT,                     -- ISO date the posting went up (if known)
    created_at                TEXT NOT NULL,            -- ISO timestamp row was inserted
    updated_at                TEXT NOT NULL,            -- ISO timestamp last modified

    -- Core posting
    job_title                 TEXT NOT NULL,
    company                   TEXT,
    company_domain            TEXT,                     -- canonical key, messy `company` names dedupe here
    company_size              TEXT,                     -- headcount bucket
    company_industry          TEXT,
    company_stage             TEXT,                     -- seed/series/public
    job_url                   TEXT NOT NULL UNIQUE,     -- dedupe key
    application_url           TEXT,                     -- sometimes differs from job_url
    source_url                TEXT,                     -- which resolved fetch URL surfaced it
    source                    TEXT,                     -- normalized board name (linkedin, otta, ...)
    source_job_id             TEXT,                     -- posting's ID on the source board, where available
    job_description           TEXT,                     -- full scraped description
    description_hash          TEXT,                     -- dedupe reposts across boards

    -- Location & work mode
    location                  TEXT,                     -- original free-text
    location_city             TEXT,
    location_region           TEXT,
    location_country          TEXT,
    work_mode                 TEXT CHECK (work_mode IS NULL OR work_mode IN ('remote','hybrid','onsite')),
    timezone                  TEXT,
    relocation_required       INTEGER CHECK (relocation_required IN (0,1)),
    visa_sponsorship          TEXT,                     -- 'yes' / 'no' / 'unknown'

    -- Compensation
    salary_min                INTEGER,
    salary_max                INTEGER,
    salary_currency           TEXT,                     -- ISO 4217, e.g. 'CAD', 'USD'
    salary_period             TEXT CHECK (salary_period IS NULL OR salary_period IN ('year','month','week','day','hour','contract')),
    salary_raw                TEXT,                     -- original string
    compensation_notes        TEXT,                     -- equity, bonus, signing

    -- Role characterization
    employment_type           TEXT CHECK (employment_type IS NULL OR employment_type IN ('full_time','part_time','contract','fractional','internship')),
    seniority_level           TEXT,                     -- staff, senior, principal, manager, director, ...
    role_type                 TEXT CHECK (role_type IS NULL OR role_type IN ('ic','manager','hybrid')),
    years_experience_required INTEGER,
    tech_stack                TEXT,                     -- JSON array string

    -- Matching / scoring
    keyword_alignment         TEXT,                     -- comma-separated matched keywords
    match_score               INTEGER,                  -- 0-100
    match_reasons             TEXT,                     -- short rationale for the score
    track                     TEXT,                     -- winning track id (or 'unknown')

    -- Subjective
    priority                  INTEGER CHECK (priority IS NULL OR priority BETWEEN 1 AND 5),
    excitement                INTEGER CHECK (excitement IS NULL OR excitement BETWEEN 1 AND 5),

    -- Application pipeline
    state                     TEXT NOT NULL DEFAULT 'created'
        CHECK (state IN ('created','screening','applied','interviewing','offer','rejected','withdrawn','cancelled')),
    date_applied              TEXT,
    application_method        TEXT,                     -- direct / referral / recruiter / board
    referral_contact          TEXT,
    resume_version            TEXT,                     -- which tailored resume was sent
    cover_letter_path         TEXT,
    recruiter_name            TEXT,
    recruiter_email           TEXT,
    last_contact_date         TEXT,
    next_action               TEXT,
    next_action_date          TEXT,
    interview_count           INTEGER NOT NULL DEFAULT 0,
    rejection_reason          TEXT,
    withdrawal_reason         TEXT,

    -- Housekeeping
    notes                     TEXT,
    archived                  INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0,1))
);

CREATE INDEX IF NOT EXISTS idx_jobs_state           ON jobs(state);
CREATE INDEX IF NOT EXISTS idx_jobs_date_found      ON jobs(date_found);
CREATE INDEX IF NOT EXISTS idx_jobs_track           ON jobs(track);
CREATE INDEX IF NOT EXISTS idx_jobs_company_domain  ON jobs(company_domain);
CREATE INDEX IF NOT EXISTS idx_jobs_next_action     ON jobs(next_action_date);
CREATE INDEX IF NOT EXISTS idx_jobs_archived        ON jobs(archived);
CREATE INDEX IF NOT EXISTS idx_jobs_description_hash ON jobs(description_hash);
"""

# Columns added after the initial schema. SQLite ALTER TABLE ADD COLUMN can't
# enforce CHECK constraints retroactively, so constraints above apply only to
# fresh databases. For migrated rows we trust record_job.py to validate.
MIGRATIONS: list[tuple[str, str]] = [
    ("track",                     "ALTER TABLE jobs ADD COLUMN track TEXT"),
    ("date_posted",               "ALTER TABLE jobs ADD COLUMN date_posted TEXT"),
    ("created_at",                "ALTER TABLE jobs ADD COLUMN created_at TEXT"),
    ("company_domain",            "ALTER TABLE jobs ADD COLUMN company_domain TEXT"),
    ("company_size",              "ALTER TABLE jobs ADD COLUMN company_size TEXT"),
    ("company_industry",          "ALTER TABLE jobs ADD COLUMN company_industry TEXT"),
    ("company_stage",             "ALTER TABLE jobs ADD COLUMN company_stage TEXT"),
    ("application_url",           "ALTER TABLE jobs ADD COLUMN application_url TEXT"),
    ("source",                    "ALTER TABLE jobs ADD COLUMN source TEXT"),
    ("source_job_id",             "ALTER TABLE jobs ADD COLUMN source_job_id TEXT"),
    ("job_description",           "ALTER TABLE jobs ADD COLUMN job_description TEXT"),
    ("description_hash",          "ALTER TABLE jobs ADD COLUMN description_hash TEXT"),
    ("location_city",             "ALTER TABLE jobs ADD COLUMN location_city TEXT"),
    ("location_region",           "ALTER TABLE jobs ADD COLUMN location_region TEXT"),
    ("location_country",          "ALTER TABLE jobs ADD COLUMN location_country TEXT"),
    ("work_mode",                 "ALTER TABLE jobs ADD COLUMN work_mode TEXT"),
    ("timezone",                  "ALTER TABLE jobs ADD COLUMN timezone TEXT"),
    ("relocation_required",       "ALTER TABLE jobs ADD COLUMN relocation_required INTEGER"),
    ("visa_sponsorship",          "ALTER TABLE jobs ADD COLUMN visa_sponsorship TEXT"),
    ("salary_currency",           "ALTER TABLE jobs ADD COLUMN salary_currency TEXT"),
    ("salary_period",             "ALTER TABLE jobs ADD COLUMN salary_period TEXT"),
    ("compensation_notes",        "ALTER TABLE jobs ADD COLUMN compensation_notes TEXT"),
    ("employment_type",           "ALTER TABLE jobs ADD COLUMN employment_type TEXT"),
    ("seniority_level",           "ALTER TABLE jobs ADD COLUMN seniority_level TEXT"),
    ("role_type",                 "ALTER TABLE jobs ADD COLUMN role_type TEXT"),
    ("years_experience_required", "ALTER TABLE jobs ADD COLUMN years_experience_required INTEGER"),
    ("tech_stack",                "ALTER TABLE jobs ADD COLUMN tech_stack TEXT"),
    ("match_reasons",             "ALTER TABLE jobs ADD COLUMN match_reasons TEXT"),
    ("priority",                  "ALTER TABLE jobs ADD COLUMN priority INTEGER"),
    ("excitement",                "ALTER TABLE jobs ADD COLUMN excitement INTEGER"),
    ("date_applied",              "ALTER TABLE jobs ADD COLUMN date_applied TEXT"),
    ("application_method",        "ALTER TABLE jobs ADD COLUMN application_method TEXT"),
    ("referral_contact",          "ALTER TABLE jobs ADD COLUMN referral_contact TEXT"),
    ("resume_version",            "ALTER TABLE jobs ADD COLUMN resume_version TEXT"),
    ("cover_letter_path",         "ALTER TABLE jobs ADD COLUMN cover_letter_path TEXT"),
    ("recruiter_name",            "ALTER TABLE jobs ADD COLUMN recruiter_name TEXT"),
    ("recruiter_email",           "ALTER TABLE jobs ADD COLUMN recruiter_email TEXT"),
    ("last_contact_date",         "ALTER TABLE jobs ADD COLUMN last_contact_date TEXT"),
    ("next_action",               "ALTER TABLE jobs ADD COLUMN next_action TEXT"),
    ("next_action_date",          "ALTER TABLE jobs ADD COLUMN next_action_date TEXT"),
    ("interview_count",           "ALTER TABLE jobs ADD COLUMN interview_count INTEGER NOT NULL DEFAULT 0"),
    ("rejection_reason",          "ALTER TABLE jobs ADD COLUMN rejection_reason TEXT"),
    ("withdrawal_reason",         "ALTER TABLE jobs ADD COLUMN withdrawal_reason TEXT"),
    ("archived",                  "ALTER TABLE jobs ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"),
]


def existing_columns(conn: sqlite3.Connection) -> set[str]:
    return {row[1] for row in conn.execute("PRAGMA table_info(jobs)").fetchall()}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: init_db.py <path-to-jobs.db>", file=sys.stderr)
        return 2
    db_path = Path(sys.argv[1]).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        cols = existing_columns(conn)
        for column, ddl in MIGRATIONS:
            if column not in cols:
                conn.execute(ddl)
        # Indexes that may need creating after migration on an older DB.
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_track          ON jobs(track)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_domain ON jobs(company_domain)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_next_action    ON jobs(next_action_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_archived       ON jobs(archived)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_description_hash ON jobs(description_hash)")
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    finally:
        conn.close()
    print(f"ok {db_path} rows={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
