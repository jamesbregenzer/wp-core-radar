# Failed Approaches

This file records approaches that were tried or considered and should not be repeated without a clear reason.

## Publishing the local development admin console directly

The local `scripts/review-server.py` console is useful for development, but it should not be exposed directly to the public internet.

The production `/radar/admin/` route should remain Worker-rendered, authenticated, and narrowly scoped to writing constrained review metadata to `data/reviews/reviews.json`.

Keeping `scripts/review-server.py` in a public repository is acceptable because it is source code, not a running service. The unsafe version would be committing secrets, running it on a public port, exposing it through a tunnel, or deploying it as the production admin interface.

## Treating Radar as a Trac automation bot

Radar is intentionally human-in-the-loop. It should not auto-comment on Trac, submit tickets, or perform contribution actions on behalf of a person.

## Keeping every raw field in the public dashboard

Early dashboard versions exposed many raw columns such as component, milestone, separate keyword lists, review reason, and raw source slugs. This made the dashboard feel like a CSV export instead of a product.

The current public dashboard intentionally keeps the table focused:

```text
Score | Tier | Ticket | Summary | Track | Trac Status | Discovery Track | Signals
```

Detailed scoring and action controls belong in the protected admin console, not the public dashboard.

## Publishing directly from a GitHub Pages custom domain

GitHub Pages works for a single repository/domain mapping, but it does not preserve the desired long-term architecture where `james.bregenzer.dev` can become a portfolio site while `/radar/` serves this project.

Cloudflare Worker routing is the preferred direction because it allows multiple projects to live under path prefixes while still supporting protected dynamic routes like `/radar/admin/`.

## Replacing the Mac Mini collector with GitHub-hosted Actions

GitHub-hosted runners do not share the Mac Mini's local browser/network context. Because Trac CSV collection depends on that context, GitHub Actions should not be the primary collector.

Actions may still be useful later for linting or validation after the Mac Mini pushes updates.
