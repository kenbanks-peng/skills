---
name: meld
description: Use Meld for agent responses that present results in a list or table or could benefit from a simple report.
---

# Workflow

1. Run `meld skill`. Follow its instructions to write and render the report. Unless inconvenient, limit tables to three columns.
2. Set html_path to the absolute path of the generated report. Run `terminal-browser open "$html_path" --split right`.
3. Reply with one sentence summarizing the result and linking to the HTML. Do not repeat the report in chat.

