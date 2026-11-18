---
name: meld
description: Use Meld for agent responses that present results in a list or table. Only the simplest responses should omit Meld.
---

# Workflow

1. Run `meld skill` for current syntax, components, and rendering instructions.
2. Create `.meld/source/` in the project root. Write UTF-8 Markdown plus Meld components to a source file there, for example, `.meld/source/document.meld`.
3. Render HTML directly into `.meld/` with an explicit output path: `meld .meld/source/document.meld --output .meld/document.html`. Keep source files in `.meld/source/` and rendered HTML in `.meld/`. Resolve rendering errors before proceeding.
4. Open the generated HTML using its absolute path in a new Rex browser block, following [the terminal-browser instructions](terminal-browser.md).
5. Verify the rendered content before reporting success. Clear the browser activity indicator and leave the output visible.

