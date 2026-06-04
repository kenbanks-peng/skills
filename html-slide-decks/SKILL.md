---
name: html-slide-decks
description: "Use when the user needs a lightweight browser-native presentation as one HTML file with keyboard navigation, progress, speaker-friendly layout, and print/PDF fallback."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation, powerpoint, claude-design]
---

# HTML Slide Decks

## Overview

This skill creates self-contained HTML artifacts for lightweight browser-native decks. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

For diagrams and diagram-like visualizations, inherit the foundation default: Catppuccin Mocha dark theme unless the user asks otherwise.

Local example: `examples/09-slide-deck.html`. The guidance below distills reusable patterns; copied examples preserve the upstream Apache-2.0 notice.

## When to Use

Use this skill when:
- the user wants a presentation but not a `.pptx` file
- a narrative walkthrough should be opened locally, shared as HTML, or printed to PDF
- keyboard navigation and a progress indicator matter
- the deck benefits from HTML/SVG/CSS interaction or responsive browser viewing

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- audience, talk length, narrative arc, required slides, and takeaway
- whether the deck is browser-native HTML or must be `.pptx`
- keyboard navigation, progress, print/PDF, and speaker-note expectations
- visual system constraints and any diagrams or demos embedded in slides

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use `powerpoint` whenever a `.pptx` file is input or output. Use `claude-design` for broader designed artifacts that may include decks. Use this skill for lightweight browser-native presentations with keyboard navigation and print/PDF fallback.

## Artifact Anatomy

- Deck shell with one active slide at a time and a slide count/progress indicator.
- Semantic slide sections with stable IDs and accessible labels.
- Keyboard navigation: ArrowRight/PageDown/Space next, ArrowLeft/PageUp previous, Home/End.
- Sparse slide layouts: title, section divider, comparison, timeline, diagram, quote, conclusion.
- Print/PDF fallback that renders all slides in order.
- Optional presenter notes only when requested.

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

Use `<section class="slide" aria-label="Slide N: Title">`. Toggle `[hidden]` or an `.active` class. Store current index in a small variable; localStorage is optional. Keep slide size predictable, often 16:9, and scale content with CSS. Print CSS should reveal all slides and hide navigation controls.

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
- Use `powerpoint` instead when the requested artifact is `.pptx` or must use a PowerPoint template.
- Overfilling slides with report-level detail. One idea per slide.
- Forgetting keyboard focus and visible current-slide indication.
