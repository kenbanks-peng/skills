---
name: html
description: "Present design information, chart data, or results as a polished, self-contained HTML artifact. Includes three ready-to-adapt templates."
---

# HTML

Create one portable HTML file for information that benefits from visual layout. Use markdown for short prose-only answers.

## Choose a template

Resolve paths relative to this skill directory. Read the selected template before adapting it.

| Need | Template | Structure |
| --- | --- | --- |
| Present design information | `templates/design.html` | Direction, palette, typography, components, rationale |
| Visualize chart data | `templates/charts.html` | Context, horizontal bar chart, exact data table, interpretation |
| Present results | `templates/results.html` | Decision summary, next actions |

Templates are independent starting points, not dependencies on other skills. Each opens directly in a browser without a server, build, or network access.

## Workflow

1. Establish audience, purpose, source material, and intended takeaway. Ask only for missing information that prevents useful output.
2. Choose one template. Preserve its structure only where it serves the content; remove irrelevant sections.
3. Copy it to the requested destination, or a descriptive local `.html` file. Never overwrite the source template.
4. Replace the sample title, copy, values, dates, sources, and metadata. Keep a visible sample/assumption label if any illustrative content remains. Never invent evidence, metrics, or a review verdict.
5. Use the embedded Catppuccin Mocha palette by default: Base background, Surface 0 cards, Text/Subtext 0 copy, Blue accents, and Peach emphasis. Adapt tokens only when a different brand or theme is requested. Keep print output light with dark text and accents.
6. Verify the saved artifact and report its path plus checks actually performed.

## Template guidance

### Design information

Explain the design objective and audience before showing specimens. Include token values and intended uses, a readable type scale, representative components, and rationale/trade-offs. Show real control markup when demonstrating controls; do not imply a static specimen performs an action. Identify proposals versus approved decisions. Replace all specimen copy as appropriate.

### Chart data

Edit the JSON in `#chart-data`: `title`, `unit`, `source`, and `items` containing unique `label` strings and finite numeric `value` fields. The chart and table render from the same dataset; negative values, zero, empty data, and invalid input are handled. The template uses a horizontal bar chart with a zero baseline and direct labels, not a color-dependent legend.

Use a chart appropriate to the question: bars compare categories, lines show time, scatterplots show relationships. If changing chart type, update its renderer, accessible description, and verification accordingly. Do not imply a time trend or causality from category totals. State units, period, provenance, missing-data treatment, and any uncertainty. Do not convert missing values to zero. Keep the exact-value table. If scripting is disabled, the template shows an explicit notice rather than a misleading empty chart.

### Results

Lead with what was learned and the decision it supports, followed by concrete next actions and evidence. Keep the default layout single-column without metric-card or side-by-side findings rows. Target one page: a short takeaway, a brief decision, and at most three next actions. Omit footer rules and footnote sections; place necessary source/limitation context beside the relevant claim. Use concise copy before shrinking type; never clip or hide overflow to force a fit. Verify print pagination on both A4 and Letter after adapting content. Narrow screens may scroll. If metrics are needed, include definitions and comparison periods/baselines in the narrative; state limitations beside the relevant claims. Keep observations distinct from interpretations. Remove unsupported metrics rather than manufacturing numbers. Do not imply that sample results describe the user's project.

## Shared requirements

- One complete HTML document with embedded CSS/JS and no external assets or libraries.
- Meaningful title, language, charset, viewport, one primary heading, and semantic regions.
- Responsive layout, readable contrast, labeled controls, visible keyboard focus, and no color-only meaning.
- Print CSS that preserves content and removes unnecessary decoration.
- Textual descriptions and exact values for charts; render untrusted text with `textContent`, never HTML interpolation.
- No persistence, analytics, or backend unless explicitly requested.
- Preserve source attribution if copying third-party content.

## Verification

- Check that the output is complete, sample content was replaced or labeled, and source notes are accurate.
- Open in a browser; inspect headings, visible content, narrow layout, and console errors.
- For charts, confirm chart/table values match, and check negative, zero, empty, and invalid datasets after renderer changes.
- For interactive additions, exercise the controls and keyboard path.
- Use terminal-browser in a new Rex block when requested; never replace the conversation block.
