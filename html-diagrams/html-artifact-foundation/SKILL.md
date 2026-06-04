---
name: html-artifact-foundation
description: "Use when creating self-contained HTML artifacts instead of markdown; provides shared single-file, accessibility, responsive, print, export, attribution, and browser-verification rules for HTML-output skills."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, foundation, accessibility, verification]
    related_skills: [html-exploration-planning, html-code-review-understanding, html-design-systems, html-prototyping, html-illustrations-diagrams, html-slide-decks, html-research-learning, html-reports, html-custom-editing-interfaces]
---

# HTML Artifact Foundation

## Overview

Use this as the shared base for agent-generated single-file HTML artifacts. The purpose is not to make every answer visual; it is to recognize when a browser-native artifact communicates structure, comparison, interaction, or state better than another wall of markdown.

Default to one portable `.html` file with embedded CSS, embedded JavaScript only when it earns its place, inline SVG where useful, and no build step. Category skills should reference this skill for shared rules rather than repeating them.

The patterns are distilled from the public `html-effectiveness` demos. Do not copy demo code or prose unless the user explicitly asks and the copied material keeps the source attribution and Apache-2.0 notice.

## When to Use

Use HTML when the requested output needs at least one of these:
- spatial comparison: options, variants, trade-offs, before/after states
- scan-first hierarchy: dashboards, status reports, plans, incident timelines
- visual systems: colors, typography, component states, diagrams, figure sheets
- interaction: tabs, filters, toggles, animation controls, collapsible explainers
- export loop: a temporary editor that lets a human manipulate data and copy JSON, markdown, prompt text, or a diff back into a workflow
- presentation: a self-contained deck or narrative walkthrough

Prefer markdown when:
- the output is mostly prose, a short checklist, or code snippets
- the user needs easy inline editing in chat rather than a file
- there is no meaningful layout, visual, or interactive affordance

Prefer an external tool when:
- `.pptx`, `.pdf`, `.excalidraw`, Figma, or production repo code is the requested deliverable
- the artifact needs server persistence, authentication, collaboration, or real backend APIs
- the user needs pixel-perfect production implementation in an existing app stack

## Inputs to Gather

Before writing HTML, gather or infer:
- objective: what decision, explanation, or workflow the artifact supports
- audience: who will read or operate it and their context level
- source evidence: files, diffs, metrics, incident logs, notes, screenshots, requirements
- constraints: brand tokens, target viewport, print/PDF needs, offline needs, export format
- interaction budget: static, light controls, or tool-like editor
- fidelity: rough exploration, polished communication artifact, or handoff-ready reference

If evidence is missing for claims, mark assumptions visibly or stop to retrieve the data. A beautiful unsupported artifact is worse than a plain grounded note.

## Artifact Anatomy

Every standalone artifact should include:
- `<!doctype html>`, `<html lang="en">`, UTF-8 charset, viewport meta, and a meaningful `<title>`
- one clear top-level heading and a short purpose/subtitle
- a layout shell with named sections, not anonymous div soup
- CSS variables for colors, spacing, type scale, radii, shadows, and state colors
- semantic regions (`header`, `main`, `section`, `article`, `nav`, `aside`, `footer`) where practical
- visible source/evidence notes when the artifact makes factual claims
- optional controls grouped in a labeled panel; controls should not obscure primary content
- footer metadata: generated date/source if useful, and attribution if copied source material is included

## Implementation Workflow

1. Decide whether HTML is justified using the decision framework above.
2. Choose the category skill for the artifact type and read its anatomy/checklist.
3. Gather source evidence before designing the layout.
4. Sketch the information hierarchy in text: title, primary panels, secondary panels, export/interaction needs.
5. Write a complete single-file HTML document. Use inline CSS. Add JS only for material interactions.
6. Keep generated data in structured arrays/objects inside the script when that improves maintainability.
7. Verify statically and, for visual or interactive work, open the file in a browser and inspect the console.
8. Report the exact path and what verification actually ran.


## Prompt Template

```text
Create a self-contained HTML artifact for: [goal].
Audience and reading mode: [who will use it, skim/deep review/presentation/operator].
Source evidence to use: [files, notes, logs, diffs, metrics, screenshots, or explicit assumptions].
Chosen category skill: [html-exploration-planning / html-code-review-understanding / ...].
Required anatomy: [sections, panels, controls, export format].
Constraints: one local HTML file; embedded CSS/JS only; semantic HTML; accessible controls; responsive layout; no unsupported claims.
Verification: save to [path], run static checks, and open locally/check console when visual or interactive complexity warrants it.
```

Optional starting point: `templates/base.html` contains a minimal skeleton with `{{title}}`, `{{purpose}}`, and `{{content}}` placeholders. Replace all placeholders before delivery; it is a starting template, not a finished artifact.

## HTML/CSS/JS Patterns

Base skeleton:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Artifact title</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f5f0;
      --surface: #ffffff;
      --ink: #1f2937;
      --muted: #6b7280;
      --line: #d8d2c5;
      --accent: #8b5cf6;
      --danger: #b91c1c;
      --success: #15803d;
      --radius: 16px;
      --shadow: 0 18px 50px rgba(31, 41, 55, .10);
      --max: 1180px;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: var(--bg); color: var(--ink); line-height: 1.5; }
    main, header, footer { width: min(var(--max), calc(100% - 32px)); margin-inline: auto; }
    .card { background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); padding: clamp(16px, 2vw, 28px); }
    :focus-visible { outline: 3px solid color-mix(in srgb, var(--accent), white 20%); outline-offset: 3px; }
    @media (max-width: 760px) { .grid { grid-template-columns: 1fr !important; } }
    @media print { body { background: white; } .no-print { display: none !important; } .card { box-shadow: none; break-inside: avoid; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .001ms !important; transition-duration: .001ms !important; scroll-behavior: auto !important; } }
  </style>
</head>
<body>
  <header><p class="eyebrow">Artifact type</p><h1>Artifact title</h1><p>Purpose statement.</p></header>
  <main><!-- sections --></main>
  <footer>Generated from provided sources. No copied demo code.</footer>
</body>
</html>
```

Interaction rules:
- Use native controls first: `<button>`, `<details>`, `<summary>`, radio groups, checkboxes, forms.
- Buttons must have non-empty text or `aria-label` and visible focus states.
- If JS changes content, update button labels or `aria-expanded`/`aria-selected` states.
- Do not hide all content behind JavaScript; static fallback should still communicate the point.
- Keep state local to the page unless the user explicitly asks for persistence; if using `localStorage`, namespace the key.

Copy/export pattern:

```js
async function copyText(text, statusEl) {
  try {
    await navigator.clipboard.writeText(text);
    statusEl.textContent = 'Copied';
  } catch (error) {
    statusEl.textContent = 'Copy failed; select the export text manually.';
  }
}
```

## Accessibility, Responsive, and Print Checks

Accessibility basics:
- one `h1`; headings descend logically
- text contrast is strong enough for body and controls
- interactive controls are keyboard reachable and have visible labels
- tap targets are roughly 44px where practical
- color is not the only way severity/status is communicated
- animations respect `prefers-reduced-motion`
- SVGs have `<title>`/`aria-label` if informative, `aria-hidden="true"` if decorative

Responsive basics:
- no horizontal scrolling at narrow widths unless the content is intentionally tabular and wrapped in an overflow region
- grids collapse to one column on small screens
- charts/diagrams keep labels readable or provide a textual summary

Print basics:
- hide controls with `.no-print`
- remove heavy shadows/backgrounds
- avoid splitting cards, timeline items, and slides awkwardly with `break-inside: avoid`

## Verification Checklist

- [ ] File exists at the stated path and is a complete HTML document.
- [ ] Has title, charset, viewport, and one primary heading.
- [ ] No remote assets unless explicitly justified.
- [ ] Buttons/links have text labels and keyboard focus states.
- [ ] Responsive behavior exists for narrow screens.
- [ ] Print CSS exists when the artifact is a report, plan, or deck.
- [ ] If interactive, open locally and check the browser console for errors.
- [ ] If factual, visible content is grounded in cited/provided sources or clearly labeled assumptions.
- [ ] If source demos are copied, attribution and Apache-2.0 notice are preserved.

## Common Pitfalls

1. Making HTML for prose-only output. If layout and interaction do not help, markdown is better.
2. Building a mini app without an export path. A temporary editor must return useful text or data.
3. Inventing metrics, statuses, or claims for visual polish. Ground every factual panel.
4. Hiding required content behind hover-only interactions or fragile JavaScript.
5. Using low-contrast muted text, tiny labels, or keyboard-inaccessible controls.
6. Shipping a file that was never opened or statically checked.
7. Copying demo-specific placeholder companies, names, or prose into reusable skills.
