---
name: prime
description: Prime the conversation with project context by listing tracked files and displaying AGENTS.md if present
---

# Prime

Gather project context at the start of a conversation.

## Instructions

1. !`git ls-files 2> /dev/null || true`
2. !`cat AGENTS.md 2> /dev/null || true`
   
