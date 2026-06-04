---
name: html-custom-editing-interfaces
description: "Use when the user needs a throwaway self-contained HTML editor to manipulate structured information and export markdown, JSON, unified diff text, or prompt text back into an agent or repository workflow."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation]
---

# HTML Custom Editing Interfaces

## Overview

This skill creates self-contained HTML artifacts for temporary task-specific editors with explicit export loops. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

Source demo mapping: 18-editor-triage-board.html, 19-editor-feature-flags.html, 20-editor-prompt-tuner.html. Patterns are distilled, not copied verbatim.

## When to Use

Use this skill when:
- the user needs to sort, classify, tune, toggle, validate, or reorder structured information
- manual editing in markdown would be error-prone but a full app is overkill
- the output must be copied back as JSON, markdown, unified diff text, or a prompt
- a live preview, validation panel, or changed-key diff would reduce mistakes

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- source data schema, editable fields, validation rules, and dependencies
- required export formats: markdown, JSON, unified diff text, prompt text, or mixed
- original state for changed-key diffs and reset behavior
- accessibility fallback for drag/drop or complex interactions

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use this skill when HTML is a temporary tool, not just a document. The distinguishing feature is an explicit export loop back into an agent or repository workflow; without export, prefer a simpler report, prototype, or markdown form.

## Artifact Anatomy

- Intake/import area if the editor starts from pasted data.
- Work surface: triage board, toggle table, prompt sections, sortable cards, or state matrix.
- Validation panel with blocking issues and warnings.
- Live preview showing exactly what will be exported.
- Change summary/diff showing what differs from the initial state.
- Explicit export panel with format selector and copy/download buttons.
- Reset/restore controls so experimentation is safe.

## Implementation Workflow

1. Apply `html-artifact-foundation` for document skeleton, accessibility, responsive, print, attribution, and verification rules.
2. Gather the category-specific inputs above and write a short evidence list before composing the page.
3. Choose one primary artifact type from this skill; avoid mixing every pattern into one page.
4. Build the category-specific anatomy below with semantic sections and CSS variables.
5. Add JavaScript only for the category-specific interaction/export/navigation behavior described here.
6. Verify using the foundation checklist plus the category-specific checklist below.

## Prompt Template

```text
Create a self-contained HTML artifact for: [goal].
Audience: [reader/operator].
Source evidence to use: [files, diffs, notes, data, screenshots].
Artifact type: [choose one from this skill].
Must show: [required sections or states].
Interaction/export needs: [tabs, filters, copy JSON, keyboard deck, none].
Constraints: single local HTML file; embedded CSS/JS only; semantic HTML; accessible controls; responsive layout; no unsupported claims.
Verification: save to [path], run static checks, and if interactive open locally and check console errors.
```

## HTML/CSS/JS Patterns

Represent editable state as a JavaScript object/array, render from state, and export from the same state. Keep original state for changed-key diffing. Validate dependencies before export: missing required fields, duplicate keys, incompatible flags, empty prompt sections. Clipboard export should fall back to visible selectable text. Drag/drop is optional; click-to-move buttons are more robust and accessible.

## Verification Checklist

- [ ] Foundation checklist passed: complete HTML document, accessibility basics, responsive behavior, and appropriate print/export behavior.
- [ ] Category trigger fits this skill and the relationship notes above rule out a better peer skill.
- [ ] Category-specific source evidence was gathered before rendering factual content.
- [ ] Artifact anatomy includes the required category sections and omits irrelevant decorative panels.
- [ ] Any category-specific JavaScript interaction/export/navigation works and has no console errors.
- [ ] Factual claims are tied to source notes or labeled assumptions.

## Common Pitfalls

- Duplicating the foundation skill instead of keeping this category focused.
- Creating an attractive but unsupported artifact with invented data.
- Adding controls that do not change anything meaningful.
- Letting dense layouts become unreadable on narrow screens.
- Building an editor with no explicit export format. The export is the product.
- Storing important state only in DOM text instead of a data object.
- Making drag/drop the only interaction; provide keyboard or button alternatives.
- Exporting invalid JSON/diff/prompt text without validation.
