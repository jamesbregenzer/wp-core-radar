# Scoring Rubric

WP Core Radar uses deterministic scoring before any model review.

The goal is to prioritize contribution opportunities that are likely to be useful, actionable, and aligned with the contributor’s strengths.

## Positive Signals

| Signal | Points |
|---|---:|
| Has patch | +30 |
| Needs testing | +30 |
| Recent activity within 30 days | +15 |
| Clear reproduction steps | +15 |
| Media component | +15 |
| Admin/UI component | +10 |
| Has screenshots | +10 |
| Has unit tests | +10 |
| Low setup complexity | +15 |

## Negative Signals

| Signal | Points |
|---|---:|
| Closed ticket | -100 |
| No patch | -20 |
| Stale for more than 2 years | -25 |
| Complex environment required | -20 |
| Already has multiple recent test reports | -15 |
| Multisite-specific | -15 |
| Large architectural discussion | -25 |
| Unclear reproduction path | -20 |

## Opportunity Tracks

- Patch Testing
- Bug Reproduction
- Ticket Triage
- Small Patch Authoring
- Documentation
- Accessibility Review
- Release Testing
- Meta Contribution

## Output

Each opportunity should include:

- Score
- Confidence
- Track
- Reasoning
- Estimated effort
- Recommended next action
- Why this is a good fit