# WP Core Radar

WP Core Radar is an intelligent contribution discovery and prioritization engine for WordPress Core contributors.

It helps identify high-value contribution opportunities, score them deterministically, and produce actionable recommendations so contributors can spend less time searching Trac and more time contributing.

## Purpose

WP Core Radar helps answer:

- Which WordPress Core tickets are worth reviewing today?
- Which tickets are good patch-testing opportunities?
- Which tickets match my strengths and available time?
- Which opportunities are most likely to move Core forward?

## Initial Focus

The first version focuses on:

- WordPress Core Trac tickets
- Tickets with patches
- Tickets needing testing
- Media component opportunities
- Recent contributor activity
- Clear reproduction and testing paths

## Core Principles

- Human-in-the-loop contribution
- Deterministic scoring before AI review
- Transparent ranking reasons
- Respectful use of WordPress.org resources
- No auto-commenting on Trac
- No spammy automation
- No attempts to bypass access controls

## Planned Workflow

```text
Collect data
Normalize opportunities
Score deterministically
Generate ranked reports
Review top candidates
Act manually and thoughtfully
Track outcomes
```

## Project Status

Early development.

Current milestone:

- Build the Thor-based Mac Mini collector
- Fetch WordPress Core Trac data from a residential connection
- Save raw opportunity data
- Generate the first ranked report
