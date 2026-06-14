# WP Core Radar Architecture

WP Core Radar is a deterministic, human-in-the-loop contribution intelligence workflow for WordPress Core.

## System Overview

```text
WordPress Trac
  ↓
Mac Mini browser-assisted collector
  ↓
Archived raw CSV datasets
  ↓
Deterministic scoring and grouping
  ↓
Markdown report + public dashboard
  ↓
GitHub repository
  ↓
Cloudflare Pages/Worker routing
```

The Mac Mini remains central because the CSV collection step depends on the local browser/network environment. GitHub and Cloudflare host the resulting static artifacts; they do not currently collect Trac data.

## Public / Private Split

```text
/radar/          Public, static dashboard
/radar/admin/    Future authenticated admin UI
```

The public dashboard is read-only. It is safe to publish because it contains scored ticket recommendations and review metadata only.

Admin write-back should remain narrowly scoped to `data/reviews/reviews.json`. It should not become a general repository editor.

## Data Flow

1. Query tracks are configured in `config/queries.json`.
2. `scripts/browser-fetch.py` opens each configured query in Firefox and waits for `query.csv`.
3. `scripts/import-download.py` archives the downloaded CSV under `data/raw/manual/YYYY-MM-DD/`.
4. `scripts/radarlib.py` discovers datasets, normalizes ticket rows, loads outcomes/reviews, scores tickets, and groups workflow sections.
5. `scripts/generate-report.py` writes `reports/latest.md` and a dated report.
6. `scripts/generate-dashboard.py` writes `docs/radar/index.html`.
7. Cloudflare deploys the static dashboard after the repo is pushed.

## Shared Logic

Core parsing, scoring, grouping, review status handling, and presentation labels belong in `scripts/radarlib.py`.

Script-specific files should focus on their output format:

- `generate-dashboard.py` renders public HTML.
- `generate-report.py` renders Markdown.
- `review-server.py` renders the local admin console.
- `run-radar.py` orchestrates collection and generation.

## Guardrails

Radar never auto-comments on Trac and never attempts to automate contribution activity. It identifies opportunities, explains why they ranked, and leaves contribution decisions to a human reviewer.

## Dataset Conventions

Preferred archive convention:

```text
data/raw/<source>/<YYYY-MM-DD>/<query_slug>.csv
```

Current browser-assisted imports use:

```text
data/raw/manual/YYYY-MM-DD/<query_slug>.csv
```

The discovery layer remains tolerant of older archived paths, but new imports should follow the current convention.
