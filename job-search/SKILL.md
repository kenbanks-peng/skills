---
name: job-search
description: Scan job-board URLs for roles matching the user's skillset and constraints, record new matches in a SQLite database, and produce a daily summary report. Use this skill whenever the user asks to "find new jobs", "check job boards", "run my job search", "search for jobs matching my resume", "get today's job matches", or mentions "job search skill".
---

# Job Search

Run a repeatable job-hunt workflow against the user's JobSearch workspace:

1. Load `job-search-spec.toml` (tracks, variable bindings, profile, rubric) and `job-search-urls.md` (URL templates).
2. For every track, resolve URL templates into concrete fetch URLs.
3. Fetch each URL, extract postings, hydrate each posting's full job description from its detail page, then filter and score them per track using the full description.
4. Dedupe against `data/jobs.db` (by `job_url` first, then by `description_hash` to catch cross-board reposts) and insert new matches with state = `created`.
5. Write a daily Word report to `data/daily/YYYY-MM-DD.docx`.

## Workspace layout

```
JobSearch/
├── job-search-urls.md       # URL templates with {{name}} placeholders
├── job-search-spec.toml     # TOML spec: tracks, bindings, profile, rubric
└── data/
    ├── jobs.db              # SQLite database (auto-created, source of truth)
    ├── jobs.xlsx            # Workbook rebuilt from jobs.db on every run
    └── daily/
        └── YYYY-MM-DD.docx  # Daily report, Microsoft Word format
```

All generated artifacts live under `data/`. The TOML spec and URL template
file stay at the workspace root because the user edits them directly.

## Protocol — job-search-spec.toml

The spec file is a TOML document. Every key is either a reserved structural key or a `{{name}}` placeholder usable in `job-search-urls.md`.

```toml
[search]                      # URL template variables (universal)
location              = "Remote, Canada"
posted_within_seconds = 604800

[filter.*]                    # hard filters (universal); not URL placeholders
[filter.location]
country.any          = ["CA"]         # ISO 3166-1 alpha-2
work_mode.any        = ["remote"]     # remote | hybrid | onsite
timezone.any         = []             # IANA tz names, empty = no constraint
relocation_ok        = false
sponsorship_required = false

[filter.compensation]
min      = 0
currency = "CAD"                      # ISO 4217
period   = "year"                     # year | month | week | day | hour | contract

[filter.title]
none = ["Intern", "Junior"]           # case-insensitive substring

[filter.score]
min = 30                              # 0-100

[[track]]                     # array of tables, one entry per track
id    = "<slug>"              # reserved. Track id.
label = "<text>"              # reserved. Display name.

[track.search]                # URL template variables for this track
queries = ["...", ...]        # referenced as {{queries}} in job-search-urls.md

[track.filter.*]              # hard filters for this track; merged vs universal
[track.filter.title]
none = ["Sales", "Recruiter"] # case-insensitive substring

[track.scoring]               # scoring keywords for this track
any  = ["...", ...]
none = ["...", ...]

[profile]                     # optional. Free-form context for scoring.
experience = ["..."]
domains    = ["..."]
skills     = ["..."]

[rubric]                      # optional. Scoring bands.
bands = [
  { range = "80-100", means = "..." },
  { range = "50-79",  means = "..." },
  ...
]
```

**Resolution per track:**

```
scope = search ∪ track.search
```

List-valued bindings fan out as the cartesian product when substituted into URL templates. A `{{name}}` referenced in `job-search-urls.md` but not present in any scope is a hard error — the resolver exits non-zero and no fetches happen.

**Filters are not placeholders.** `filter.*` and `track.filter.*` tables define hard constraints applied before/alongside scoring. Universal vs track merge rule:

- `min / max / any / every` → track overrides universal
- `none` → track concatenates with universal

**Profile and rubric** are optional tables surfaced to Claude as scoring context. They are not placeholders and are not referenced from urls.md.

## Protocol — job-search-urls.md

Each column-zero `- ` or `* ` bullet is one URL template. Indented bullets and lines starting with `#` are ignored. Templates may contain `{{name}}` placeholders that are resolved per track from `job-search-spec.toml`.

## Database schema

`jobs.db` has one table, `jobs`. Columns are grouped below. `scripts/init_db.py`
creates and migrates the schema idempotently.

**Identity & timestamps**

| column      | type    | notes                                   |
| ----------- | ------- | --------------------------------------- |
| id          | INTEGER | primary key                             |
| date_found  | TEXT    | ISO date first recorded                 |
| date_posted | TEXT    | ISO date the posting went up (if known) |
| created_at  | TEXT    | ISO timestamp of row insert             |
| updated_at  | TEXT    | ISO timestamp of last modification      |

**Core posting**

| column           | type | notes                                           |
| ---------------- | ---- | ----------------------------------------------- |
| job_title        | TEXT | required                                        |
| company          | TEXT | free-text as displayed                          |
| company_domain   | TEXT | canonical dedupe key for the employer           |
| company_size     | TEXT | headcount bucket (e.g. `51-200`)                |
| company_industry | TEXT |                                                 |
| company_stage    | TEXT | seed / series-a / public / ...                  |
| job_url          | TEXT | UNIQUE — primary dedupe key                     |
| application_url  | TEXT | when distinct from job_url                      |
| source_url       | TEXT | resolved fetch URL that surfaced this posting   |
| source           | TEXT | normalized board name (linkedin, otta, ...)     |
| source_job_id    | TEXT | posting's ID on the source board, where exposed |
| job_description  | TEXT | full scraped description                        |
| description_hash | TEXT | content hash for cross-board repost detection   |

**Location & work mode**

| column              | type    | notes                          |
| ------------------- | ------- | ------------------------------ |
| location            | TEXT    | original free-text             |
| location_city       | TEXT    |                                |
| location_region     | TEXT    | state/province                 |
| location_country    | TEXT    |                                |
| work_mode           | TEXT    | `remote` / `hybrid` / `onsite` |
| timezone            | TEXT    |                                |
| relocation_required | INTEGER | 0/1                            |
| visa_sponsorship    | TEXT    | `yes` / `no` / `unknown`       |

**Compensation**

| column             | type    | notes                                                   |
| ------------------ | ------- | ------------------------------------------------------- |
| salary_min         | INTEGER |                                                         |
| salary_max         | INTEGER |                                                         |
| salary_currency    | TEXT    | ISO 4217 (`CAD`, `USD`, ...)                            |
| salary_period      | TEXT    | `year` / `month` / `week` / `day` / `hour` / `contract` |
| salary_raw         | TEXT    | original string                                         |
| compensation_notes | TEXT    | equity, bonus, signing                                  |

**Role characterization**

| column                    | type    | notes                                                                |
| ------------------------- | ------- | -------------------------------------------------------------------- |
| employment_type           | TEXT    | `full_time` / `part_time` / `contract` / `fractional` / `internship` |
| seniority_level           | TEXT    | staff / senior / principal / manager / director                      |
| role_type                 | TEXT    | `ic` / `manager` / `hybrid`                                          |
| years_experience_required | INTEGER |                                                                      |
| tech_stack                | TEXT    | JSON array string                                                    |

**Matching / scoring**

| column            | type    | notes                                     |
| ----------------- | ------- | ----------------------------------------- |
| keyword_alignment | TEXT    | comma-separated matched scoring keywords  |
| match_score       | INTEGER | 0–100 fit score against the winning track |
| match_reasons     | TEXT    | short rationale for the score             |
| track             | TEXT    | winning track id (or `unknown`)           |

**Subjective**

| column     | type    | notes                      |
| ---------- | ------- | -------------------------- |
| priority   | INTEGER | 1–5, Ken's triage priority |
| excitement | INTEGER | 1–5, gut-level fit/energy  |

**Application pipeline**

| column             | type    | notes                                                                                                   |
| ------------------ | ------- | ------------------------------------------------------------------------------------------------------- |
| state              | TEXT    | `created` / `screening` / `applied` / `interviewing` / `offer` / `rejected` / `withdrawn` / `cancelled` |
| date_applied       | TEXT    | ISO date                                                                                                |
| application_method | TEXT    | `direct` / `referral` / `recruiter` / `board`                                                           |
| referral_contact   | TEXT    |                                                                                                         |
| resume_version     | TEXT    | which tailored resume was sent                                                                          |
| cover_letter_path  | TEXT    |                                                                                                         |
| recruiter_name     | TEXT    |                                                                                                         |
| recruiter_email    | TEXT    |                                                                                                         |
| last_contact_date  | TEXT    |                                                                                                         |
| next_action        | TEXT    | short prose                                                                                             |
| next_action_date   | TEXT    | ISO date; indexed, drives "what's on deck" views                                                        |
| interview_count    | INTEGER | default 0                                                                                               |
| rejection_reason   | TEXT    |                                                                                                         |
| withdrawal_reason  | TEXT    |                                                                                                         |

**Housekeeping**

| column   | type    | notes                             |
| -------- | ------- | --------------------------------- |
| notes    | TEXT    | free-form                         |
| archived | INTEGER | 0/1, soft-delete without deletion |

Indexes: `state`, `date_found`, `track`, `company_domain`, `next_action_date`, `archived`.

## Dependencies

- Python 3.11+ (uses stdlib `tomllib`). On 3.10, install the `tomli` backport.
- `openpyxl` for the workbook export (`pip install openpyxl --break-system-packages`).
- `python-docx` for the daily Word report (`pip install python-docx --break-system-packages`).

## Workflow

Use TodoWrite to show progress. Execute in order.

### 1. Resolve the workspace

Find the JobSearch folder (usually the mounted directory under `/sessions/*/mnt/`). Ask if ambiguous.

### 2. Initialize the database

```
python scripts/init_db.py <workspace>/data/jobs.db
```

The script creates `<workspace>/data/` if it doesn't already exist. The
migration list is idempotent and will add `source_job_id` to any older DB
that predates it.

### 3. Parse the spec

```
python scripts/parse_search_spec.py <workspace>/job-search-spec.toml
```

Returns:

```json
{
  "search": {
    "location": "Remote, Canada",
    "posted_within_seconds": 604800
  },
  "filter": {
    "location": {
      "country": { "any": ["CA"] },
      "work_mode": { "any": ["remote"] }
    },
    "compensation": { "min": 0, "currency": "CAD", "period": "year" },
    "score": { "min": 30 }
  },
  "track": [
    {
      "id": "dev",
      "label": "Software development",
      "search": { "queries": ["senior software engineer", "..."] },
      "filter": { "title": { "none": ["Sales", "..."] } },
      "scoring": { "any": ["React", "..."], "none": ["PHP", "..."] }
    }
  ],
  "profile": { "experience": ["..."], "domains": ["..."], "skills": ["..."] },
  "rubric": { "bands": [{ "range": "80-100", "means": "..." }, "..."] }
}
```

Use `context.profile` and `context.rubric` as scoring guidance in step 6.

### 4. Resolve URL templates

```
python scripts/resolve_urls.py <workspace>/job-search-urls.md <workspace>/job-search-spec.toml
```

Emits JSONL, one line per resolved URL:

```json
{"track": "dev", "url": "https://...", "vars": {"queries": "staff engineer", "location": "Remote, Canada", ...}}
```

The resolver dedupes URLs globally. Non-zero exit = a template referenced an undefined variable; stop and tell the user which one.

### 5. Fetch and extract

For each resolved URL:

1. Call WebFetch asking for: title, company, location, salary (as shown), posted date, work mode (remote/hybrid/onsite), employment type, and the direct link to each posting. Return JSON.
2. Parse the response. On failure, note it and continue — do not retry via curl or other fetchers.
3. Normalize each posting into a candidate dict. Populate as many schema fields as the page exposes — don't fabricate values, leave unknowns as null. Typical extractions:
   - `location` → the raw string; also split into `location_city` / `location_region` / `location_country` when obvious. Normalize `location_country` to ISO 3166-1 alpha-2 (e.g. "Canada" → `CA`).
   - `work_mode` → `remote` / `hybrid` / `onsite`. **Do not trust the board's tag alone — see "Verifying work_mode" below.** Normalize to lowercase canonical form.
   - `salary_raw` → original string; parse `salary_min` / `salary_max` / `salary_currency` (ISO 4217) / `salary_period` (`year` / `month` / `week` / `day` / `hour` / `contract`) when unambiguous.
   - `employment_type` → one of `full_time` / `part_time` / `contract` / `fractional` / `internship` if stated. Snap abbreviations (FTE → `full_time`, W2 → `full_time`, C2C → `contract`).
   - `seniority_level` → snap to the closest of `junior` / `mid` / `senior` / `staff` / `principal` / `lead` / `manager` / `senior manager` / `director` / `vp` based on the title. "Sr." → `senior`, "EM" → `manager`, "VP of Engineering" → `vp`. Leave null if genuinely ambiguous.
   - `role_type` → `ic` / `manager` / `hybrid` based on the title and listing. "Tech lead manager" and similar player-coach roles are `hybrid`.
   - `date_posted` → ISO date derived from "posted 2d ago" etc.
   - `source` → the board name (`linkedin`, `otta`, `indeed`, direct careers page, ...).
   - `source_job_id` → the posting's own ID on the source board, when the page or URL exposes one. Examples: LinkedIn `currentJobId=4127884412`, Indeed `jk=abcd1234ef56`, Greenhouse `/jobs/7654321`, Lever `postings/<uuid>`, Ashby `jobs/<uuid>`. Extract the raw id string — do not prefix with the board name. Leave null when the board does not publish a stable posting id. This value is surfaced in the daily report's Job ID column.
   - `company_domain` → when the listing links to a company careers page.

   **If a field can't be confidently snapped to a canonical form, leave it null. Don't guess.** Null means "unknown" at filter time, which is safer than a wrong canonical value.

4. Resolve relative job URLs against the fetch URL.
5. Carry the originating track id as a _hint_ for scoring.
6. Set `source_url` to the resolved fetch URL (not the template).

Don't chase pagination on the first pass.

#### Hydrating `job_description` (required before scoring)

After extracting candidates from a search/listing page, fetch each candidate's **detail page** with WebFetch and populate `job_description` with the full posting body. Scoring in step 6 must run against the full description, not the card snippet — title+snippet alone is too thin to judge fit and produces both false positives and false negatives.

For each candidate:

1. WebFetch the candidate's `job_url`. Ask for the full job description text, the "About the company" / "About us" blurb if present, and any responsibilities / requirements / qualifications / tech stack sections. Return as a single `job_description` string (plain text, sections concatenated).
2. While you have the detail page, backfill any schema fields the search card didn't expose: `company_domain`, `company_size`, `company_industry`, `company_stage`, `salary_*`, `employment_type`, `seniority_level`, `role_type`, `years_experience_required`, `tech_stack`, `date_posted`, `visa_sponsorship`, `relocation_required`, `timezone`, and — critically — the hybrid/onsite signals needed to verify `work_mode` (see "Verifying work_mode" above). The detail page is almost always richer than the search card; harvest what's there.
3. If WebFetch fails for a given detail page, record the failure, leave `job_description` null, and still pass the candidate on to scoring with whatever was extracted from the card. Don't retry via curl or other fetchers.
4. Do **not** compute `description_hash` yourself — `record_job.py` derives it from the normalized `job_description` at insert time. Just make sure `job_description` is populated.

Be polite to the boards: hydrate detail pages serially (or in small batches), not in a thundering herd.

#### Verifying work_mode

Job boards routinely tag postings as "Remote" when the actual arrangement is hybrid: "remote with 2 days/week in office," "remote-friendly — quarterly onsite," "remote within commuting distance of HQ," "must be based in \<city\>." The board's tag is a _hint_, not ground truth. A posting tagged `remote` that's actually hybrid will slip past a `work_mode.any = ["remote"]` filter and waste the user's time.

**Rule: never accept `work_mode = "remote"` from the tag alone. Verify against the posting text.**

1. **If the listing is tagged `remote` and you only have the card/snippet** (no full description), set `work_mode = null` and `notes = "remote tag unverified — needs hydration"`. Leave the posting in the candidate set; filters treat `null` as "unknown, not excluded." It'll be resolved later when the description is hydrated, or judged at scoring time.

2. **If the listing is tagged `remote` and you have the full description**, scan for hybrid/onsite signals before accepting. Any of these phrases downgrade `remote` → `hybrid`:
   - "in the office" / "in-office" / "onsite" / "on-site" / "on site"
   - "X days per week" / "X days a week" / "X days in" / "hybrid"
   - "commutable" / "commuting distance" / "within N miles/km of"
   - "must be located in" / "must live in" / "based in \<city\>"
   - "quarterly" / "monthly" / "weekly" mandatory visits, offsites, or meetings
   - "HQ" / "headquarters" paired with any visit cadence

3. **If the listing is tagged `remote` but the location is a specific city** (not a country, region, or "Anywhere"), treat it as suspect. Downgrade to `hybrid` unless the description explicitly says "fully remote," "100% remote," or "work from anywhere."

4. **Accept `remote` only when** the description says "fully remote," "100% remote," "work from anywhere," "distributed company / team," or equivalent, with no conflicting signals.

5. **Record the verification outcome in `notes`** when you downgrade or override — e.g. `"remote→hybrid: '2 days/week in office'"` or `"remote confirmed: 'fully distributed team'"`. Future audits depend on this.

The same logic applies in reverse but is rarer: a posting tagged `hybrid` or `onsite` that the description reveals is actually fully remote. If you see it clearly, upgrade and note why.

**Do not downgrade just because a company mentions having an office.** Many fully-remote companies still have offices that employees can optionally visit. The signal is _mandatory_ in-person attendance, not the mere existence of a physical location.

### 6. Filter and score

For each candidate:

1. **Hard filters** — evaluate universal + track-specific `filter.*` / `track.filter.*` constraints. Drop postings that violate any _known_ constraint (unknown/null values should not be treated as violations).
2. **Score against every track** — judge the full `job_description` (hydrated in step 5) plus the title against each track's `track.scoring` keywords and its `track.search` intent, guided by `context.rubric.bands` and `context.profile`. Be generous on borderlines. If `job_description` came back null because detail-page hydration failed, fall back to the title+snippet but note that in `match_reasons` — e.g. `"scored from card only; detail fetch failed"`.
3. **Pick the winner** — highest-scoring track wins. Set `track` = its id and `match_score` = its score. If below `filter.score.min` (after universal+track merge), drop. If posting straddles two tracks, pick dominant and note the secondary in `notes`. If genuinely unclassifiable but above threshold, set `track = "unknown"`.
4. **keyword_alignment** — list the specific scoring keywords from the winning track actually seen in the title/snippet.
5. **match_reasons** — one short sentence capturing _why_ the score landed where it did. This is future-Ken auditing past-Claude.
6. **role_type / seniority_level** — if determinable from the title (`Staff`, `Principal`, `Director of Engineering`, etc.), set them. They make it easy to slice IC-vs-leadership results in the daily report.

### 7. Dedupe and insert

For each survivor:

```
python scripts/record_job.py <workspace>/data/jobs.db
```

(Candidate JSON on stdin.) The inserter:

- derives `description_hash` from the normalized `job_description` automatically (you don't need to pre-compute it; callers may override by passing their own `description_hash`);
- skips existing `job_url`s (hard dedupe key) and prints `skipped <id>`;
- also skips rows whose `description_hash` matches an existing row (soft dedupe key — catches cross-board reposts where the same posting appears under a different URL) and prints `skipped <id> (description_hash match)`;
- otherwise inserts with `date_found = today, state = 'created'`.

Track inserted vs skipped per source URL for the report.

### 8. Generate the daily report

```
python scripts/daily_report.py <workspace>/data/jobs.db <workspace>/data/daily/<YYYY-MM-DD>.docx \
  --search-spec <workspace>/job-search-spec.toml
```

The report is written as a Microsoft Word document (`.docx`). Passing
`--search-spec` uses the track labels and order from the spec.

Each match row in the per-track tables carries a **Job ID** column. When
the source board exposed a posting id it's rendered as `<source_job_id>
(#<db_id>)`; when it didn't, only the DB row id is shown as `#<db_id>`.
The title cell links directly to `job_url`.

### 9. Regenerate the workbook

SQLite is the source of truth. After every run that touched `data/jobs.db`
(inserts in step 7, or state updates via the "Managing application state"
section), rebuild `data/jobs.xlsx` from the DB:

```
python scripts/export_xlsx.py <workspace>/data/jobs.db <workspace>/data/jobs.xlsx \
  --search-spec <workspace>/job-search-spec.toml
```

The script is idempotent — it rewrites the entire workbook from current DB
state, using a temp file + atomic rename so a crash never leaves a
half-written file. Three sheets are produced: `Jobs` (all non-archived),
`Active` (pipeline, terminal states excluded), and `Summary` (counts by
track × state).

**Consequence:** any manual edits made directly in `jobs.xlsx` will be
overwritten on the next run. To change a job's state, notes, priority, etc.,
update the DB (see "Managing application state" below) and re-export.

If the workbook is open in Excel on Windows when the export runs, the atomic
replace will fail with `PermissionError`. Close Excel and re-run.

Requires `openpyxl`:

```
pip install openpyxl --break-system-packages
```

### 10. Present

Share `computer://` links to both the daily report (`data/daily/<YYYY-MM-DD>.docx`)
and the workbook (`data/jobs.xlsx`), plus a one-line summary. Keep chat short.

## Managing application state

Valid states: `created`, `screening`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`, `cancelled`. Reject others.

Common updates — always bump `updated_at`:

```sql
-- Mark as applied
UPDATE jobs
SET state='applied', date_applied=date('now'),
    resume_version='<version>', application_method='<direct|referral|recruiter|board>',
    updated_at=datetime('now')
WHERE id=<id>;

-- Schedule a follow-up
UPDATE jobs
SET next_action='<what to do>', next_action_date='<YYYY-MM-DD>',
    updated_at=datetime('now')
WHERE id=<id>;

-- Reject / withdraw
UPDATE jobs SET state='rejected', rejection_reason='<why>', updated_at=datetime('now') WHERE id=<id>;
UPDATE jobs SET state='withdrawn', withdrawal_reason='<why>', updated_at=datetime('now') WHERE id=<id>;

-- Soft-archive stale rows without deleting
UPDATE jobs SET archived=1, updated_at=datetime('now') WHERE id=<id>;
```

Useful views for "what's on deck":

```sql
-- Active pipeline (not archived, not terminal)
SELECT id, job_title, company, state, next_action, next_action_date, priority
FROM jobs
WHERE archived=0 AND state NOT IN ('rejected','withdrawn','cancelled')
ORDER BY COALESCE(next_action_date,'9999-12-31'), priority DESC NULLS LAST;

-- Pipeline counts by state × track
SELECT track, state, COUNT(*) FROM jobs WHERE archived=0 GROUP BY track, state;
```

When querying the DB for reports or summaries, filter `archived=0` unless the user explicitly asks for history.

After any state-changing update (applied / rejected / archived / next_action / notes), re-run `scripts/export_xlsx.py` so `jobs.xlsx` reflects the new DB state. The workbook is a derived view; the DB is the source of truth.

## Scheduling

If the user wants automatic runs, use the `schedule` skill. Weekday mornings is a reasonable cadence.

## Failure modes

- **Malformed TOML** — `parse_search_spec.py` prints the TOML error and exits 1. Fix the spec file before proceeding.
- **WebFetch blocked** — note it, don't retry via other fetchers.
- **Same job on multiple boards with different URLs** — acceptable; dedupe is by URL.
- **Template references undefined `{{name}}`** — hard error from resolver. Fix by adding the key to `[search]` in the spec (or as a `[track.search]` override).
- **Track missing `id`** — hard error. Every track must have an `id`.
- **Empty result day** — still generate the report with a "no new matches" line.
- **Track in DB not in current spec** — `daily_report.py` falls back to the raw id as the label.
