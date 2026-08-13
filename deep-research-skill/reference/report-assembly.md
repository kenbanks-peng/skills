# Report Assembly: Progressive File Generation

## Length Requirements by Mode

| Mode | Target Words | Description |
|------|--------------|-------------|
| Quick | 2,000-4,000 | Baseline quality threshold |
| Standard | 4,000-8,000 | Comprehensive analysis |
| Deep | 8,000-15,000 | Thorough investigation |
| UltraDeep | 15,000-20,000+ | Maximum rigor (at output limit) |

---

## Output Token Safeguard

**Agent output limits vary.** Check the current agent's limits before generating a large report.

**Practical limits:**
- Keep each generated section within the current agent's output limit.
- Leave a safety margin for tool-call overhead.
- Use auto-continuation for reports that exceed one agent run (see continuation.md).

---

## Progressive Section Generation

**Core Strategy:** Generate and save each section individually with the current agent's file-write or file-edit capability. This allows large reports while keeping each generation manageable.

### Phase 8.1: Setup

```bash
# Create folder: ~/Documents/[TopicName]_Research_[YYYYMMDD]/
mkdir -p ~/Documents/[folder_name]

# Initialize markdown file with frontmatter
# Path: [folder]/research_report_[YYYYMMDD]_[slug].md
```

### Phase 8.2: Section Generation Loop

**Pattern:** Generate section -> save it to the file -> move to the next section.
Keep each file operation to one section and within the current agent's output limit.

**Initialize research run (persist to disk):**
```bash
# Create run manifest and artifact files using citation_manager CLI
python scripts/citation_manager.py init-run --out-dir [folder] --query "[question]" --mode [mode]
# Creates: run_manifest.json, sources.jsonl, evidence.jsonl, claims.jsonl
```

**Register each source as you encounter it:**
```bash
python scripts/citation_manager.py register-source \
  --json '{"raw_url": "...", "title": "...", "source_type": "academic", "year": "2024"}' \
  --dir [folder]
# Returns stable source_id (sha256-based, survives renumbering and continuation)
```

**Assign display numbers after all sources registered:**
```bash
python scripts/citation_manager.py assign-display-numbers --dir [folder]
# Maps stable source_ids to [1], [2], [3]... for rendering
```

Source identity is stable across edits and continuation. Display numbers are derived at render time, never stored in state. This survives context compaction and enables continuation agents to pick up citation state via stable IDs.

**Section sequence:**

1. **Executive Summary** (200-400 words)
   - Create the file with frontmatter and the Executive Summary.
   - Track citations.
   - Progress: "Executive Summary complete"

2. **Introduction** (400-800 words)
   - Append the Introduction to the file.
   - Track citations.
   - Progress: "Introduction complete"

3. **Finding 1-N** (600-2,000 words each)
   - Append Finding N to the file.
   - Track citations.
   - Progress: "Finding N complete"

4. **Synthesis & Insights**
   - Add novel insights beyond source statements.
   - Append the section to the file.

5. **Limitations & Caveats**
   - Add counterevidence, gaps, and uncertainties.
   - Append the section to the file.

6. **Recommendations**
   - Add immediate actions, next steps, and research needs.
   - Append the section to the file.

7. **Bibliography** (CRITICAL)
   - Include every citation from citations_used.
   - Do not use ranges, placeholders, or truncation.
   - Append the section to the file.

8. **Methodology Appendix**
   - Add the research process and verification approach.
   - Append the section to the file.

---

## File Organization

**1. Create dedicated folder:**
- Location: `~/Documents/[TopicName]_Research_[YYYYMMDD]/`
- Clean topic name (remove special chars, use underscores)

**2. File naming convention:**
All files use same base name:
- `research_report_20251104_topic_slug.md`
- `research_report_20251104_topic_slug.html`
- `research_report_20251104_topic_slug.pdf`

**3. Keep continuation state in:** `~/.agents/share/deep-research-skill/` (internal tracking). Ensure the directory exists before writing state.

---

## Word Count Per Section

**CRITICAL:** No single Edit call should exceed 2,000 words.

Example: 10 findings x 1,500 words = 15,000 words total
- Each Edit call: 1,500 words (under limit)
- File grows to 15,000 words
- No single tool call exceeds limits
