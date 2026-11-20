---
name: meld
description: Use Meld for agent responses that present results in a list or table or could benefit from a simple report. Only the simplest responses should omit Meld.
---

# Presentation

Use at most three columns in tables unless more are necessary.

# Workflow

1. Run `meld skill` for current syntax, components, and rendering instructions.
2. Create `.meld/source/` in the project root. Write UTF-8 Markdown plus Meld components to a source file there, for example, `.meld/source/document.meld`.
3. Render HTML directly into `.meld/` with an explicit output path: `meld .meld/source/document.meld --output .meld/document.html`. Keep source files in `.meld/source/` and rendered HTML in `.meld/`. Resolve rendering errors before proceeding.
4. Set `html_path` to the generated HTML’s absolute path and open it:

   ```sh
   terminal-browser open "$html_path" --split right
   ```

5. Keep the agent response to a single sentence summarizing the result and linking to the generated HTML; do not repeat the report in chat.

