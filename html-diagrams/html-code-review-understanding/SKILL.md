---
name: html-code-review-understanding
description: "Use when diffs, PR rationale, code structure, or module behavior need a spatial HTML artifact such as annotated diffs, reviewer writeups, file tours, or module maps."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation, github-code-review]
---

# HTML Code Review and Understanding

## Overview

This skill creates self-contained HTML artifacts for reviewing diffs, explaining PRs, and mapping code structure. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

Source demo mapping: 03-code-review-pr.html, 17-pr-writeup.html, 04-code-understanding.html. Patterns are distilled, not copied verbatim.

## When to Use

Use this skill when:
- a PR or local diff needs reviewer-centered visual explanation
- before/after behavior, risk areas, or test coverage should be scanned spatially
- a repo subsystem needs a module map, call-flow map, or file tour
- review comments need severity, evidence, and suggested fixes in one place

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- diff or PR source, changed file list, branch/base, test results, and review scope
- reviewer audience: maintainer, stakeholder, author, security reviewer, or onboarding reader
- risky hunks, behavior changes, dependencies, and module entry points
- exact file paths and line references for every finding or explanation

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use `github-code-review` for the actual GitHub/local review workflow, comments, approvals, and verdict discipline. Use this skill when the review needs a spatial explanatory artifact: annotated hunks, risk maps, PR writeups, module tours, or call-flow diagrams.

## Artifact Anatomy

- Summary band: scope, files changed, risk level, test status, review verdict.
- Annotated diff panels: file path, hunks, inline callouts, severity tags, suggested action.
- Reviewer focus areas: correctness, security, tests, performance, maintainability.
- Before/after behavior cards grounded in code evidence.
- File tour with entry points, dependencies, and ownership boundaries.
- Module/call-flow map using SVG arrows plus textual fallback.
- PR writeup section: problem, approach, validation, rollout, follow-ups.

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

Use `<pre><code>` blocks for diff snippets, but keep them short and annotated. Severity tags should include words and colors: Critical, Warning, Suggestion, Looks good. For module maps, pair each node with file path and responsibility; arrows should describe calls/data, not merely point. Include test evidence with command and result when available.

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
- Replacing actual review with a pretty PR summary. Findings still need file paths and evidence.
- Showing huge diffs in full; extract representative hunks and link or cite paths.
- Letting color-only severity tags fail accessibility.
