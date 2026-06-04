---
name: html-reports
description: "Use when recurring status, incident, postmortem, project health, or operational reports need a skim-first self-contained HTML layout with metrics, timelines, evidence, and follow-up tracking."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [html, artifacts, visualization]
    related_skills: [html-artifact-foundation, writing-plans]
---

# HTML Reports

## Overview

This skill creates self-contained HTML artifacts for structured status and incident reports. It builds on `html-artifact-foundation`: keep the shared single-file, accessibility, responsive, print, attribution, and verification rules centralized there, and use this skill for the category-specific structure.

Source demo mapping: 11-status-report.html, 12-incident-report.html. Patterns are distilled, not copied verbatim.

## When to Use

Use this skill when:
- a status report needs metrics, progress, blockers, decisions, and next steps in one scan
- an incident/postmortem needs timeline, impact, root cause, remediation, and owners
- a project health report should combine narrative, evidence, and follow-up actions
- the report may be printed or shared as a static HTML file

Do not use this skill when a plain markdown answer is enough, when the requested deliverable is a production app implementation, or when a more specialized peer skill is a better fit.

## Inputs to Gather

Use the foundation input checklist first. Additionally gather:

- reporting period, status definitions, metrics with sources/timestamps, and stakeholders
- timeline events, owners, blockers, decisions, and follow-up actions
- for incidents: impact, detection, response, root-cause evidence, and remediation
- print/PDF needs and confidentiality constraints

Evidence gate: do not render factual claims until you have the underlying source, or label the panel as an assumption/draft.

## Relationship to Other Skills

Use markdown or `writing-plans` for simple checklists and durable task plans. Use this skill when status, incident, postmortem, or project-health information is easier to scan as an HTML report with metrics, timelines, source notes, and print-ready layout.

## Artifact Anatomy

- Executive summary with status, confidence, and top risks.
- Metrics row with definitions and source timestamps.
- Timeline or event log with times, owners, and evidence links/notes.
- Workstream cards: done, in progress, blocked, next.
- Incident sections: impact, detection, response, root cause, contributing factors, remediation.
- Follow-up checklist with owners, due dates, and status.
- Appendix/source notes for commands, logs, datasets, or meeting notes.

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

Use tables for precise metrics and timelines; use cards for scan-first workstreams. Avoid fake charts unless you have real data; small inline SVG sparklines are acceptable when values are supplied. Print CSS is required. Status labels should include text and color. Incident timelines should sort chronologically and preserve timezone/source.

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
- Reporting unsupported green/yellow/red status. Show the evidence and timestamp.
- Mixing incident facts with speculation; label hypotheses clearly.
- Forgetting print/PDF behavior for stakeholder reports.
