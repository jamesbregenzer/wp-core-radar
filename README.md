# WP Core Radar

WP Core Radar is a deterministic, human-in-the-loop contribution discovery and prioritization workflow for WordPress Core tickets.

It collects ticket data from WordPress Trac, archives raw CSV exports, scores opportunities with explainable rules, and generates public and protected review views so a human contributor can decide what to test, watch, reject, or act on manually.

## What this project is

WP Core Radar helps answer:

- Which WordPress Core tickets are worth reviewing today?
- Which tickets look like good patch-testing opportunities?
- Which opportunities have clear signals such as patches, testing needs, owner activity, or feedback requests?
- Which tickets have already been reviewed, rejected, watched, tested, commented on, or completed?

## What this project is not

WP Core Radar does not auto-comment on Trac, automate contribution activity, or bypass WordPress.org access controls. It is intentionally a recommendation and review workflow, not a bot.

## Current architecture

```text
Mac Mini browser collector
  → archived raw Trac CSVs
  → deterministic scoring
  → Markdown report + public dashboard + admin data JSON
  → GitHub
  → Cloudflare Pages
  → Cloudflare Worker route at james.bregenzer.dev/radar/
```

The Mac Mini is an intentional part of the system because the CSV collection flow depends on the local browser/network environment. GitHub is the source of truth after the Mac Mini pushes updates. Cloudflare Pages serves the generated static dashboard, and a Cloudflare Worker handles routing plus the protected `/radar/admin/` review console.

## Main commands

Run the full pipeline:

```bash
python3 scripts/run-radar.py
```

Regenerate reports without fetching new Trac data:

```bash
python3 scripts/run-radar.py --skip-fetch
```

Run one configured query:

```bash
python3 scripts/run-radar.py --query general_needs_testing
```

Generate only the public dashboard:

```bash
python3 scripts/generate-dashboard.py
```

Generate only the Markdown report:

```bash
python3 scripts/generate-report.py
```

Record a review decision locally:

```bash
python3 scripts/review-ticket.py 33073 shortlist "Good first contribution candidate"
```

Run the local development review console:

```bash
python3 scripts/review-server.py
```

Then open:

```text
http://127.0.0.1:8765/radar/admin
```

The production review console is served by the Cloudflare Worker at:

```text
/radar/admin/
```

## Outputs

- `docs/radar/index.html` is the public static dashboard.
- `docs/radar/admin-data.json` is the static data payload used by the protected Worker admin console.
- `reports/latest.md` is the latest Markdown report.
- `reports/radar-YYYY-MM-DD.md` is the dated Markdown report.
- `data/reviews/reviews.json` stores human review decisions as constrained metadata keyed by ticket ID.
- `data/outcomes/outcomes.csv` stores manually maintained contribution outcomes.
- `data/raw/manual/YYYY-MM-DD/<query_slug>.csv` stores archived Trac CSV exports.

## Deployment

The public dashboard is served at `/radar/` through Cloudflare Pages/Worker routing. The generated dashboard includes an **Admin Console** link in the header that points to `/radar/admin/`.

The protected `/radar/admin/` route is rendered by a Cloudflare Worker. It authenticates with a password, reads `docs/radar/admin-data.json` from the Pages origin, and writes review decisions only to `data/reviews/reviews.json` through the GitHub API.

The Worker should use narrowly scoped secrets:

- `ADMIN_PASSWORD_HASH`
- `SESSION_SECRET`
- `GITHUB_TOKEN`

The Worker should not become a general-purpose repository editor.

## Project docs

- `docs/architecture.md` — system architecture and boundaries
- `docs/mac-mini-collector.md` — local collection workflow
- `docs/scoring-rubric.md` — deterministic scoring rules
- `docs/outcome-tracking.md` — review and contribution state
- `docs/failed-approaches.md` — decisions not to repeat without a reason
- `docs/vision.md` — product and technical direction
