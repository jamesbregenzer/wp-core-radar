# WP Core Radar

WP Core Radar is a deterministic, human-in-the-loop contribution discovery and prioritization workflow for WordPress Core tickets.

It collects ticket data from WordPress Trac, archives raw CSV exports, scores opportunities with explainable rules, and generates public and private review views so a human contributor can decide what to test, watch, reject, or act on manually.

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
  → Markdown report + public dashboard
  → GitHub
  → Cloudflare Pages/Worker routing
```

The Mac Mini is an intentional part of the system because the CSV collection flow depends on the local browser/network environment. GitHub and Cloudflare host the generated artifacts after the Mac Mini pushes updates.

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

Record a review decision:

```bash
python3 scripts/review-ticket.py 33073 shortlist "Good first contribution candidate"
```

Run the local private review console:

```bash
python3 scripts/review-server.py
```

Then open:

```text
http://127.0.0.1:8765/radar/admin
```

## Outputs

- `docs/radar/index.html` is the public static dashboard.
- `reports/latest.md` is the latest Markdown report.
- `reports/radar-YYYY-MM-DD.md` is the dated Markdown report.
- `data/reviews/reviews.json` stores human review decisions as constrained metadata keyed by ticket ID.
- `data/outcomes/outcomes.csv` stores manually maintained contribution outcomes.
- `data/raw/manual/YYYY-MM-DD/<query_slug>.csv` stores archived Trac CSV exports.

## Deployment

The public dashboard is designed to be served at `/radar/` through Cloudflare Pages/Workers routing.

The local admin console is intentionally not published by the static dashboard. A future `/radar/admin/` route should authenticate before writing review metadata, and should only update the constrained reviews JSON file.

## Project docs

- `docs/architecture.md` — system architecture and boundaries
- `docs/mac-mini-collector.md` — local collection workflow
- `docs/scoring-rubric.md` — deterministic scoring rules
- `docs/outcome-tracking.md` — review and contribution state
- `docs/failed-approaches.md` — decisions not to repeat without a reason
