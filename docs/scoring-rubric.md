# Scoring Rubric

WP Core Radar uses deterministic scoring before any human or AI-assisted review. The goal is to surface WordPress Core tickets that are likely to be actionable, useful, and aligned with repeatable contribution work.

The source of truth for scoring is `score_ticket()` in `scripts/radarlib.py`. This document mirrors that implementation so the public repo is reviewable without reading the code first.

## Baseline Track Priority

Every enabled query in `config/queries.json` has a `priority` value. That value becomes the ticket's starting score before ticket-level signals are added.

Current enabled tracks:

| Query slug | Display name | Baseline |
|---|---|---:|
| `media_has_patch` | Media: Has Patch | +100 |
| `accessibility_has_patch` | Accessibility: Has Patch | +95 |
| `docs_needs_testing` | Docs: Needs Testing | +75 |
| `good_first_bugs` | Good First Bugs | +70 |
| `general_needs_testing` | General: Needs Testing | +65 |

Unknown archived datasets fall back to a baseline of +50.

## Freshness and Momentum

Freshness is scored from the ticket's `created` date and momentum is scored from the ticket's `modified` or change time. These signals are intentionally modest, but they help keep Priority Targets focused on current, approachable work instead of allowing very old tickets to rank highly only because they accumulated useful keywords years ago.

Ticket age and activity age are scored separately. A ticket can be old but still receive a small momentum boost when it was recently updated; a fresh ticket can still be penalized later if it stops receiving activity.

## Positive Ticket Signals

| Signal | Points | Source |
|---|---:|---|
| Has patch | +35 | `keywords` contains `has-patch` or `has patch` |
| Needs testing | +30 | `keywords` contains `needs-testing` or `needs testing` |
| Good first bug | +20 | `keywords` contains `good-first-bug` or `good first bug` |
| Media component | +20 | `component` is `Media` |
| Accessibility signal | +18 | component or keywords mention accessibility |
| Dev feedback | +18 | `keywords` contains `dev-feedback` or `dev feedback` |
| Reporter feedback | +10 | `keywords` contains `reporter-feedback` or `reporter feedback` |
| Fresh ticket within 30 days | +8 | created date |
| Recent activity within 7 days | +8 | modified/change time |
| Concrete milestone | +8 | milestone is present and not `Awaiting Review` or `Future Release` |
| Healthy comment count | +7 | 2–20 comments |
| Has owner | +6 | owner exists and is not `anonymous` or `nobody` |
| Fresh ticket within 90 days | +5 | created date |
| Recent activity within 30 days | +5 | modified/change time |
| Fresh ticket within 180 days | +2 | created date |
| Recent activity within 90 days | +2 | modified/change time |

## Negative Ticket Signals

| Signal | Points | Source |
|---|---:|---|
| Closed or non-actionable status | -100 | status is `closed`, `fixed`, `wontfix`, `duplicate`, or `invalid` |
| Already produced props | -60 | `data/outcomes/outcomes.csv` records `props` |
| Already tested | -20 | `data/outcomes/outcomes.csv` records `tested` |
| Very old ticket over five years | -12 | created date older than 1825 days |
| Stale activity over one year | -10 | modified/change time older than 365 days |
| Missing summary | -10 | summary field is empty |
| Old ticket over three years | -8 | created date older than 1095 days |
| Very large thread | -8 | more than 80 comments |
| Stale activity over six months | -5 | modified/change time older than 180 days |
| Older ticket over one year | -4 | created date older than 365 days |

## Priority Target Rules

A ticket appears in **Priority Targets** only when all of these are true:

1. It has no existing review decision.
2. Its score is at least 150.
3. It has at least one action signal: `needs testing`, `has patch`, or `good first bug`.
4. It has at least one manageability signal: `recent activity`, `healthy comment count`, or `has owner`.
5. It does not include stale or already-acted-on penalties such as `very old ticket`, `stale activity`, `very large thread`, `already produced props`, or `already tested`.

Only the first 12 matching tickets are shown as Priority Targets.

## Review Grouping

Review decisions live in `data/reviews/reviews.json` and move tickets into workflow sections:

| Review status | Section |
|---|---|
| `shortlist` | Shortlisted |
| `watch` | Watching |
| `tested`, `commented`, `props`, `committed` | Completed / Acted On |
| `reject` | Rejected |
| no review status | Priority Targets or Top Opportunities |

## Guardrail

Scores are recommendations only. WP Core Radar does not auto-comment on Trac or perform contribution activity. A human reviewer opens the ticket, verifies current state, tests locally where appropriate, and decides what to do next.
