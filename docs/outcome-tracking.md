# Outcome Tracking

WP Core Radar tracks contribution outcomes and review decisions so scoring and workflow sections can improve over time without automating contribution activity.

## Contribution outcomes

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

## Review decisions

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

Reviews are stored as JSON keyed by ticket ID because this format is easy for both local tooling and the protected Cloudflare Worker admin route to validate safely.

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

Because the repository is public, review notes should be written as publishable metadata. Do not store secrets, private credentials, or sensitive personal notes in `data/reviews/reviews.json`.

## Protected admin write path

The production `/radar/admin/` console is rendered by the Cloudflare Worker. It authenticates the user, loads generated ticket data from `docs/radar/admin-data.json`, and writes review decisions to `data/reviews/reviews.json` through the GitHub API.

Allowed review statuses are intentionally limited to the workflow states above. This keeps the admin route useful for review decisions without turning it into a broad repository write surface.
