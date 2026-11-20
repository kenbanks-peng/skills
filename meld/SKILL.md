---
name: meld
description: Use Meld for agent responses that present results in a list or table or could benefit from a simple report. Only the simplest responses should omit Meld.
---

# Presentation

Use at most three columns in tables unless more are necessary.

# Workflow

1. Run `meld skill` for current syntax, components, and rendering instructions.
2. Run `meld paths --project <project-directory>` (defaults to the current directory). Meld creates global project storage and returns JSON containing absolute `source_dir` and `output_dir` paths; use these paths without constructing folder names or hashes. Write UTF-8 Markdown plus Meld components to `$source_dir/document.meld`.
3. Render HTML with an explicit output path: `meld "$source_dir/document.meld" --output "$output_dir/document.html"`. Keep source files and rendered HTML in the returned folders; do not create `.meld/` in the repository. Resolve rendering errors before proceeding.
4. Set `html_path` to the generated HTML’s absolute path and open it:

   ```sh
   terminal-browser open "$html_path" --split right
   ```

5. Keep the agent response to a single sentence summarizing the result and linking to the generated HTML; do not repeat the report in chat.

