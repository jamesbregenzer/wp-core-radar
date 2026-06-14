# Outcome Tracking

WP Core Radar tracks contribution outcomes and review decisions so scoring and workflow sections can improve over time without automating contribution activity.

## Contribution Outcomes

Contribution outcomes describe what happened after a ticket was acted on manually in WordPress Trac.

Examples:

- Ticket tested
- Trac comment posted
- Patch accepted
- Props received
- Ticket committed
- Follow-up requested

Outcome records live in:

```text
data/outcomes/outcomes.csv
```

This file remains intentionally simple because outcomes are low-volume and manually maintained.

## Review Decisions

Review decisions describe how Radar triaged a ticket before or after human review.

Examples:

- `shortlist` — strong candidate for follow-up
- `watch` — worth monitoring, but not actionable yet
- `reject` — poor fit for this workflow
- `tested` — patch or behavior tested
- `commented` — manual Trac comment posted
- `props` — contribution resulted in props
- `committed` — ticket was committed

Review decisions live in:

```text
data/reviews/reviews.json
```

Reviews are stored as JSON keyed by ticket ID because this format is easy for both the local admin console and a future protected Worker endpoint to validate safely.

Example:

```json
{
  "33073": {
    "status": "shortlist",
    "reason": "Good first contribution candidate",
    "notes": "Patch exists and needs testing.",
    "updated_at": "2026-06-14T00:00:00Z"
  }
}
```

The review data file should remain constrained metadata only. It should not become a general-purpose repository write surface.
