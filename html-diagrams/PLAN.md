# HTML Effectiveness Skill Extraction Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan phase-by-phase. Keep the Phase Status table at the bottom current as work progresses.

**Goal:** Extract the patterns from https://thariqs.github.io/html-effectiveness/ into a coherent set of reusable Hermes HTML-output skills for agent-generated single-file artifacts.

**Architecture direction:** Build one shared foundation skill for self-contained HTML artifacts, then add focused skills for each work category: Exploration & Planning, Code Review & Understanding, Design, Prototyping, Illustrations & Diagrams, Decks, Research & Learning, Reports, and Custom Editing Interfaces. Each category skill should distill the demos into trigger conditions, artifact anatomy, prompting workflow, implementation patterns, pitfalls, and verification checks.

**Tech stack:** Hermes `SKILL.md` files with YAML frontmatter; self-contained HTML/CSS/JS examples; optional `templates/`, `references/`, and `assets/` directories per skill; static browser verification.

---

## Source evidence

Index inspected: `https://thariqs.github.io/html-effectiveness/`

The source page presents twenty self-contained `.html` demos grouped into nine categories. The page states the examples are companion artifacts to “The unreasonable effectiveness of HTML” and are intended as alternatives to walls of markdown.

License note from fetched source: `Copyright 2026 Anthropic PBC · SPDX-License-Identifier: Apache-2.0`. Preserve attribution if copying code or prose. Prefer distilling patterns over copying full demos verbatim.

Downloaded examples for inspection during planning only: `/tmp/html-effectiveness/*.html`.

## Demo inventory

| Category | Demo files | Pattern to extract |
|---|---|---|
| Exploration & Planning | `01-exploration-code-approaches.html`, `02-exploration-visual-designs.html`, `16-implementation-plan.html` | Side-by-side option comparison, visual direction board, handoff-ready implementation plan with timeline/data-flow/risk table |
| Code Review & Understanding | `03-code-review-pr.html`, `17-pr-writeup.html`, `04-code-understanding.html` | Annotated diff, reviewer-centered PR writeup, module/call-flow map |
| Design | `05-design-system.html`, `06-component-variants.html` | Design-token reference, component state/variant matrix |
| Prototyping | `07-prototype-animation.html`, `08-prototype-interaction.html` | Animation sandbox with controls, clickable flow/interaction prototype |
| Illustrations & Diagrams | `10-svg-illustrations.html`, `13-flowchart-diagram.html` | Inline SVG figure sheet, annotated flowchart with step details |
| Decks | `09-slide-deck.html` | Keyboard-navigable slide deck in one HTML file |
| Research & Learning | `14-research-feature-explainer.html`, `15-research-concept-explainer.html` | Collapsible feature explainer, interactive concept explainer |
| Reports | `11-status-report.html`, `12-incident-report.html` | Weekly status report, incident/postmortem timeline |
| Custom Editing Interfaces | `18-editor-triage-board.html`, `19-editor-feature-flags.html`, `20-editor-prompt-tuner.html` | Throwaway task-specific editor with export/copy output loop |

## Proposed skill set

Create these skills unless an existing equivalent already covers the category better. Keep names lowercase and hyphenated.

1. `html-artifact-foundation`
   - Category: `creative` or this repo's chosen category root.
   - Purpose: shared conventions for self-contained HTML artifacts.
   - Covers: when HTML beats markdown, single-file constraints, accessibility, responsive layout, print/export behavior, no-build delivery, browser verification, copy/export buttons, attribution rules.
   - Related skills: all category-specific HTML skills.

2. `html-exploration-planning`
   - Demos: `01`, `02`, `16`.
   - Use when the user needs to compare options, pick a direction, or hand off a plan visually.
   - Artifact types: approach comparison board, visual direction board, implementation-plan page.

3. `html-code-review-understanding`
   - Demos: `03`, `17`, `04`.
   - Use when diffs, PR rationale, or code structure benefit from spatial layout.
   - Artifact types: annotated PR review, PR writeup, module map.

4. `html-design-systems`
   - Demos: `05`, `06`.
   - Use when design tokens, components, variants, or states should be reviewed visually.
   - Artifact types: token sheet, component contact sheet, variant/state matrix.

5. `html-prototyping`
   - Demos: `07`, `08`.
   - Use when motion, click-throughs, state transitions, or interaction details need to be felt rather than described.
   - Artifact types: animation sandbox, clickable flow, microinteraction prototype.

6. `html-illustrations-diagrams`
   - Demos: `10`, `13`.
   - Use when the output is primarily a diagram or figure set.
   - Artifact types: SVG figure sheet, annotated flowchart, process map.
   - Note: coordinate carefully with existing `architecture-diagram`, `excalidraw`, and `baoyu-infographic` skills to avoid overlap.

7. `html-slide-decks`
   - Demo: `09`.
   - Use when the user needs a lightweight browser-native presentation.
   - Artifact types: arrow-key deck, meeting readout, narrative walkthrough.
   - Note: coordinate with existing `powerpoint`; this skill is for HTML-native decks, not `.pptx` generation.

8. `html-research-learning`
   - Demos: `14`, `15`.
   - Use when a feature, repo subsystem, or concept should be taught with navigation and interaction.
   - Artifact types: feature explainer, interactive concept explainer, glossary-linked tutorial.

9. `html-reports`
   - Demos: `11`, `12`.
   - Use for recurring structured documents where timeline, status, metrics, and follow-ups improve scanability.
   - Artifact types: weekly status, incident report, postmortem, project health report.

10. `html-custom-editing-interfaces`
    - Demos: `18`, `19`, `20`.
    - Use when the user needs to manipulate structured information and export the result back to markdown, JSON, diff text, or a prompt.
    - Artifact types: triage board, feature-flag editor, prompt tuner, bespoke review interface.

## Shared extraction principles

- Distill reusable patterns, not demo-specific Acme placeholder content.
- Every skill should answer: when to use HTML, what information to gather first, artifact anatomy, implementation recipe, interaction/export recipe, verification checklist, and common failure modes.
- Each category skill should include a compact prompt template the agent can reuse.
- Keep the deliverable single-file by default: embedded CSS, embedded JS, inline SVG, no remote assets unless explicitly needed.
- Prefer semantic HTML first; add JavaScript only for interactions that materially improve the artifact.
- Include accessibility basics: heading hierarchy, keyboard navigation, labels, focus states, reduced-motion handling for motion-heavy artifacts, adequate contrast.
- Include responsive behavior: useful at desktop width, readable on narrow screens, printable when reports/plans/decks need it.
- Include a “copy/export result” pattern for editors and any artifact intended to feed back into an agent workflow.
- Include verification that the artifact opens locally in a browser and has no console errors.

## Skill file structure

Each `SKILL.md` should use peer-matched Hermes frontmatter:

```yaml
---
name: html-example-skill-name
description: "Use when ..."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation]
---
```

Recommended body shape:

```markdown
# Human Title

## Overview
## When to Use
## Inputs to Gather
## Artifact Anatomy
## Implementation Workflow
## Prompt Template
## HTML/CSS/JS Patterns
## Verification Checklist
## Common Pitfalls
```

Supporting files, if useful:

```text
<skill>/templates/base.html
<skill>/templates/example-prompt.md
<skill>/references/demo-inventory.md
```

## Implementation phases

### Phase 0: Repository and target-category discovery

**Objective:** Decide where these skills should live and avoid duplicating existing skills.

**Steps:**
1. Inspect the repository layout and existing skills, if any.
2. Inspect available/user-local peer skills that overlap: `architecture-diagram`, `excalidraw`, `sketch`, `claude-design`, `popular-web-designs`, `powerpoint`, `design-md`, `github-code-review`, and `writing-plans`.
3. Decide whether this repo should contain only these HTML skills or whether they should be added under a broader Hermes skills tree.
4. Confirm naming and category placement.

**Verification:** A short note in the implementation summary lists existing overlaps and the chosen placement rationale.

### Phase 1: Create the foundation skill

**Objective:** Establish shared rules so category skills stay concise and consistent.

**Files:**
- Create: `html-artifact-foundation/SKILL.md` or the selected category path.
- Optional create: `html-artifact-foundation/templates/base.html`.

**Content requirements:**
- Decision framework: markdown vs HTML vs external tool.
- Single-file artifact recipe.
- Visual hierarchy and layout defaults.
- Interaction rules and no-build constraints.
- Accessibility, responsive, and print checks.
- Browser verification commands/procedure.
- Attribution and license guidance for using source demos.

**Verification:** Validate frontmatter, open/read the skill, and manually review that all category skills can reference it.

### Phase 2: Create Exploration & Planning and Code Review & Understanding skills

**Objective:** Cover the most agent-workflow-native demos first.

**Files:**
- Create: `html-exploration-planning/SKILL.md`.
- Create: `html-code-review-understanding/SKILL.md`.

**Extraction details:**
- Exploration skill should include patterns for option cards, trade-off matrices, design direction galleries, milestone timelines, data-flow diagrams, and risk tables.
- Code review skill should include patterns for annotated diffs, severity tags, reviewer focus areas, before/after sections, file tours, and module maps.

**Verification:** Each skill has at least one reusable prompt template and a checklist that forces evidence gathering before rendering the HTML.

### Phase 3: Create Design and Prototyping skills

**Objective:** Cover visual/UI work where live HTML strongly outperforms prose.

**Files:**
- Create: `html-design-systems/SKILL.md`.
- Create: `html-prototyping/SKILL.md`.

**Extraction details:**
- Design skill should separate token sheets from component matrices and include color/type/spacing/state coverage.
- Prototyping skill should include animation controls, state machines, click-through screens, and reduced-motion fallback.

**Verification:** Each skill states when to stop at static HTML and when to add JavaScript.

### Phase 4: Create Illustrations & Diagrams and Decks skills

**Objective:** Cover communication artifacts that often become presentation or documentation assets.

**Files:**
- Create: `html-illustrations-diagrams/SKILL.md`.
- Create: `html-slide-decks/SKILL.md`.

**Extraction details:**
- Illustration skill should include inline SVG conventions, figure sheets, copyable SVG regions, annotated flowcharts, and diagram legends.
- Deck skill should include slide semantics, keyboard navigation, progress indicator, speaker-friendly layout, and print/PDF fallback.

**Verification:** Both skills clearly differentiate themselves from existing diagram/deck skills.

### Phase 5: Create Research & Learning and Reports skills

**Objective:** Cover structured reading artifacts.

**Files:**
- Create: `html-research-learning/SKILL.md`.
- Create: `html-reports/SKILL.md`.

**Extraction details:**
- Research skill should include TL;DR panels, collapsible paths, tabs, glossary sidebars, interactive teaching widgets, and comparison tables.
- Reports skill should include status sections, timelines, metrics/charts, log excerpts, follow-up checklists, and skim-first layout.

**Verification:** Both skills include data-source grounding rules to avoid polished but unsupported reports/explainers.

### Phase 6: Create Custom Editing Interfaces skill

**Objective:** Capture the most advanced “HTML as temporary tool” pattern.

**Files:**
- Create: `html-custom-editing-interfaces/SKILL.md`.
- Optional create: `html-custom-editing-interfaces/templates/export-button.js`.

**Extraction details:**
- Include drag/drop or click-state patterns, dependency validation, live preview, changed-key diffing, and clipboard export.
- Emphasize that every editor must have an explicit export format that feeds back into the agent or repository.

**Verification:** Skill includes export-format examples for markdown, JSON, unified diff text, and prompt text.

### Phase 7: Cross-link, deduplicate, and validate

**Objective:** Make the skill set coherent rather than ten isolated documents.

**Steps:**
1. Add `related_skills` links between the foundation and category skills.
2. Remove duplicated foundation content from category skills; replace with references to `html-artifact-foundation`.
3. Check all descriptions are under 1024 characters and all names are lowercase/hyphenated.
4. Validate frontmatter for every `SKILL.md`.
5. Search for accidental copied demo-specific company names unless intentionally used in examples.

**Verification commands:**

```bash
python - <<'PY'
from pathlib import Path
import re, yaml
for p in Path('.').rglob('SKILL.md'):
    text = p.read_text()
    assert text.startswith('---'), p
    m = re.search(r'\n---\s*\n', text[3:])
    assert m, p
    fm = yaml.safe_load(text[3:m.start()+3])
    assert fm.get('name'), p
    assert fm.get('description'), p
    assert len(fm['description']) <= 1024, p
    assert text[m.end()+3:].strip(), p
    print('ok', p)
PY
```

### Phase 8: Add sample artifact smoke test

**Objective:** Prove the skills can be used to generate working HTML, not just instructions.

**Steps:**
1. Pick one representative category, preferably `html-custom-editing-interfaces` or `html-exploration-planning`.
2. Use the skill instructions to generate a small sample HTML artifact into `examples/`.
3. Open it locally or run a static smoke check.
4. Check for missing title, missing viewport, empty buttons, inline script errors, and obvious accessibility issues.

**Verification:** The generated sample opens as a self-contained HTML file and the implementation summary reports the exact file path and smoke-check result.

## Acceptance criteria

- `PLAN.md` exists and is the active control surface for the extraction project.
- The final skill set includes one shared foundation skill plus category skills covering all nine source categories.
- Every source demo is mapped to at least one skill.
- Each skill has valid Hermes frontmatter and a non-empty actionable body.
- Each skill includes trigger conditions, inputs to gather, artifact anatomy, implementation workflow, prompt template, verification checklist, and pitfalls.
- Shared rules are centralized in `html-artifact-foundation` instead of repeated everywhere.
- At least one generated example artifact verifies the skills are executable in practice.
- Attribution/licensing is handled if any source code or prose from the demos is copied.

## Open decisions

- Final repository/category placement: flat directories in this repo vs `skills/<category>/<name>/`.
- Whether to create actual reusable `templates/base.html` files or keep templates inline in the skills.
- Whether to merge some narrow categories later if the resulting skills feel too small, especially `html-slide-decks` and `html-reports`.
- Whether to promote these as general `creative` skills or keep them as a dedicated HTML artifact pack.

## What not to do yet

- Do not create a build system; the point is self-contained HTML.
- Do not require screenshots or browser automation for every skill use; use browser verification when the artifact has meaningful interaction or visual complexity.
- Do not collapse all categories into one giant skill unless implementation proves the category skills are too thin.

## Phase Status

| Number | Title | Status |
|---:|---|---|
| 0 | Repository and target-category discovery | TODO |
| 1 | Create the foundation skill | TODO |
| 2 | Create Exploration & Planning and Code Review & Understanding skills | TODO |
| 3 | Create Design and Prototyping skills | TODO |
| 4 | Create Illustrations & Diagrams and Decks skills | TODO |
| 5 | Create Research & Learning and Reports skills | TODO |
| 6 | Create Custom Editing Interfaces skill | TODO |
| 7 | Cross-link, deduplicate, and validate | TODO |
| 8 | Add sample artifact smoke test | TODO |
