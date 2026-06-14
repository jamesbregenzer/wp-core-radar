# Failed Approaches

This file records approaches that were tried or considered and should not be repeated without a clear reason.

## Publishing the admin console publicly

The review console writes to local CSV files and can run follow-up scripts. It should remain local-only until proper authentication, authorization, and write-safety controls are added.

## Treating Radar as a Trac automation bot

Radar is intentionally human-in-the-loop. It should not auto-comment on Trac, submit tickets, or perform contribution actions on behalf of a person.

## Keeping every raw field in the public dashboard

Early dashboard versions exposed many raw columns such as component, milestone, separate keyword lists, review reason, and source slugs. This made the dashboard feel like a CSV export instead of a product.

The current public dashboard intentionally keeps the table focused:

```text
Score | Tier | Ticket | Summary | Track | Trac Status | Discovery Track | Signals
```

Detailed scoring and action controls belong in the local admin console, not the public dashboard.

## Publishing directly from GitHub Pages custom domain

GitHub Pages works for a single repository/domain mapping, but it does not preserve the desired long-term architecture where `james.bregenzer.dev` can become a portfolio site while `/radar/` serves this project.

Cloudflare routing is the preferred direction for this project.
