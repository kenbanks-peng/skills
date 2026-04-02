---
name: prime
description: Prime the conversation with project context by listing tracked files and displaying AGENTS.md if present
---

# Prime

Gather project context at the start of a conversation.

## Instructions

1. Run `git ls-files` to list all tracked files in the repository.
2. Check if `AGENTS.md` exists in the repository root.
   - If it exists, `cat AGENTS.md` and display its contents.
   - If it does not exist, skip this step silently.
