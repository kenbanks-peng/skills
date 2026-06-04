---
name: html-exploration-planning
description: "Use when comparing approaches, exploring visual directions, or handing off an implementation plan as a self-contained HTML artifact with option cards, timelines, flow diagrams, and risk tables."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation, writing-plans, sketch]
---

# HTML Exploration and Planning

## Overview

This skill creates self-contained HTML artifacts for comparing options, choosing directions, and handing off plans visually. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

Source demo mapping: 01-exploration-code-approaches.html, 02-exploration-visual-designs.html, 16-implementation-plan.html. Patterns are distilled, not copied verbatim.

## When to Use

Use this skill when:
- the user needs to compare multiple implementation approaches or design directions
- trade-offs, risks, dependencies, or milestones need to be seen together
- a plan should be handoff-ready with timeline, data flow, owners, and decision points
- stakeholders need a visual board rather than a long prose plan

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- decision question, candidate options, locked constraints, and recommendation criteria
- comparable dimensions for trade-off scoring: effort, risk, reversibility, dependency, user impact
- milestone gates, data-flow steps, owners, and unresolved unknowns
- for visual direction boards: reference images/sites, brand constraints, and taste boundaries

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use `writing-plans` for durable prose/markdown implementation plans with task details. Use this skill when the plan or exploration benefits from HTML comparison boards, timelines, matrices, data-flow visuals, or stakeholder handoff pages. Use `sketch` for disposable UI variants rather than general technical planning.

## Artifact Anatomy

- Header with decision question, recommendation, and confidence level.
- Option cards with goal fit, complexity, risk, dependencies, and best-for notes.
- Trade-off matrix using comparable dimensions, not vague pros/cons.
- Visual direction gallery with annotated principles and constraints.
- Milestone timeline with entry/exit criteria.
- Data-flow or handoff diagram using inline SVG or CSS grid.
- Risk table with mitigation and trigger signals.
- Final decision area: recommended option, why not the alternatives, and next step.

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

Option-card pattern: use `article` cards with consistent fields: problem fit, effort, risk, reversibility, unknowns. Timeline pattern: ordered list with phase labels, deliverables, gates, and owner/source. Matrix pattern: rows are options, columns are comparable decision dimensions; avoid mixing narrative bullets and scores without definitions. Inline SVG can show data flow, but include a text summary for accessibility.

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
- Comparing options with unnormalized criteria; every option should be judged on the same dimensions.
- Treating the recommended direction as fact without showing the trade-off basis.
