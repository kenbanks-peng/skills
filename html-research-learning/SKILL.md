---
name: html-research-learning
description: "Use when a feature, repository subsystem, research topic, or concept should be taught with a self-contained HTML explainer using TL;DR panels, collapsible paths, tabs, glossary, or interactive widgets."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation]
---

# HTML Research and Learning

## Overview

This skill creates self-contained HTML artifacts for interactive explainers for concepts, features, and research. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

Local examples: `examples/14-research-feature-explainer.html`, `examples/15-research-concept-explainer.html`. The guidance below distills reusable patterns; copied examples preserve the upstream Apache-2.0 notice.

## When to Use

Use this skill when:
- a concept or subsystem needs to be taught, not merely summarized
- readers have different depth needs and benefit from progressive disclosure
- tabs, glossary terms, comparisons, or small teaching widgets clarify the subject
- a research synthesis needs visible sources and grounded claims

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- source material, claims to teach, reader knowledge level, and learning goal
- terms that need glossary definitions and sections that need progressive disclosure
- examples, comparisons, or widgets that will make the concept easier to understand
- citation/source requirements and known uncertainty

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use research-domain skills for gathering current or academic source material. Use this skill after evidence exists and the deliverable should teach through HTML navigation, collapsible paths, glossary sidebars, tabs, or small explanatory widgets.

## Artifact Anatomy

- TL;DR panel with key takeaways and reading path.
- Progressive sections using `<details>` for optional depth.
- Tabs or segmented controls for perspectives, examples, or roles.
- Glossary sidebar with short definitions and anchors.
- Concept diagram or mini-simulation when interaction improves learning.
- Comparison tables for alternatives, assumptions, or trade-offs.
- Source notes beside claims and a bibliography/source list.

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

Use native `<details><summary>` for collapsible depth before writing JS. Tabs need `role="tablist"`, buttons with `aria-selected`, and panels with labels. Teaching widgets should have reset buttons and clear explanations of what changed. Keep source citations close to the claims they support.

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
- Writing a polished explainer from weak sources. Ground every non-obvious factual claim.
- Hiding the core explanation inside collapsed sections. TL;DR should stand alone.
- Making interactive widgets that entertain but do not teach.
