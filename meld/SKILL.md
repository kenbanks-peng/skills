---
name: meld
description: Create self-contained HTML reports with Meld when a conversation result, findings, comparison, or handoff benefits from a visual document with structured panels, metrics, or charts.
---

## Workflow

1. Run `meld skill` for current syntax, components, and rendering instructions.
2. Write UTF-8 Markdown plus Meld components to a meld document, for example, `document.meld`.
3. Run `meld document.meld` to produce `document.html`. Resolve rendering errors before proceeding.
4. Open the generated HTML using its absolute path in a new Rex browser block, following [the terminal-browser instructions](terminal-browser.md).
5. Verify the rendered content before reporting success. Clear the browser activity indicator and leave the output visible.

