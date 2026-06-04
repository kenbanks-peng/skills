---
name: html-prototyping
description: "Use when motion, click-through flows, state transitions, or microinteractions need to be experienced in a browser-native single-file HTML prototype."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation, claude-design, sketch]
---

# HTML Prototyping

## Overview

This skill creates self-contained HTML artifacts for browser-native prototypes for motion and interaction. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

For diagrams and diagram-like visualizations, inherit the foundation default: Catppuccin Mocha dark theme unless the user asks otherwise.

Local examples: `examples/07-prototype-animation.html`, `examples/08-prototype-interaction.html`. The guidance below distills reusable patterns; copied examples preserve the upstream Apache-2.0 notice.

## When to Use

Use this skill when:
- the user needs to feel an animation, state transition, or interaction rather than read about it
- a click-through flow can clarify product behavior before implementation
- a small state machine, loading/empty/error path, or microinteraction needs review
- controls should let the user tune timing, state, density, or scenario

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- target flow, state machine, starting state, success/error/empty/loading states
- motion or transition goals and timing constraints
- controls the reviewer needs: play/pause, speed, state selector, variant toggles
- reduced-motion fallback and whether persistence is useful

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use `sketch` for disposable static visual directions and `claude-design` for broader polished design artifacts. Use this skill when the core value is runnable behavior: motion, state transitions, click-through flows, microinteractions, and browser-tested controls.

## Artifact Anatomy

- Scenario frame: goal, primary path, and current state.
- Prototype canvas: the UI or motion under test, visually separated from controls.
- Controls panel: play/pause, speed, state selector, variant toggles, reset.
- State machine notes: states, triggers, transitions, and edge cases.
- Reduced-motion fallback description and CSS media query.
- Feedback/log panel for click-through prototypes when helpful.

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

Use plain JavaScript event listeners and CSS classes for state changes. Keep prototype state in one object when more than two controls interact. Animation controls should manipulate CSS variables such as `--duration` or classes such as `.is-playing`. Use `prefers-reduced-motion` to disable non-essential animation and provide an instant transition fallback.

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
- Adding JavaScript to static mockups where simple HTML would be clearer.
- Hiding controls or making the prototype impossible to reset.
- Using motion as decoration rather than state explanation.
